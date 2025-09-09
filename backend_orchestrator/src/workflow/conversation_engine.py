import asyncio
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import structlog
import json

from ..llm_abstraction.provider_interface import LLMProviderInterface, LLMRequest 
from ..llm_abstraction.prompt_manager import PromptManager
from ..messaging.kafka_client import KafkaClient
from ..session.session_manager import SessionManager

logger = structlog.get_logger()

class ConversationEngine:
    """Main conversation processing engine that orchestrates AI agents"""
    
    def __init__(self, llm_provider: LLMProviderInterface, 
                 fallback_provider: LLMProviderInterface,
                 prompt_manager: PromptManager,
                 kafka_client: KafkaClient,
                 session_manager: SessionManager,
                 websocket_manager=None):
        self.llm_provider = llm_provider
        self.fallback_provider = fallback_provider
        self.prompt_manager = prompt_manager
        self.kafka_client = kafka_client
        self.session_manager = session_manager
        self.websocket_manager = websocket_manager
        
        self.intent_patterns = {
            "appointment_booking": ["book", "schedule", "appointment", "doctor", "clinic"],
            "appointment_modify": ["reschedule", "cancel", "change", "move"],
            "general_info": ["what", "how", "when", "where", "info", "help"],
            "medical_emergency": ["emergency", "urgent", "pain", "bleeding", "chest"],
            "pre_admission": ["admission", "surgery", "procedure", "preparation"],
            "post_discharge": ["discharge", "recovery", "follow-up", "medication"]
        }

        # Define explicit mapping for Kafka agent interactions
        # ADDED 'temporary_response' to each agent's configuration
        self.kafka_agent_topic_map = {
            "appointment_booking": {
                "request_topic": "appointment-agent-requests",
                "response_topic": "appointment-agent-responses",
                "timeout": 30,
                "temporary_response": "I'm processing your appointment request. Please give me a moment to check availability."
            },
            "appointment_modify": {
                "request_topic": "appointment-agent-requests", 
                "response_topic": "appointment-agent-responses",
                "timeout": 30,
                "temporary_response": "I'm working on modifying your appointment. Please hold on."
            },
            "general_info": { # Assuming general_info can be handled by a Kafka RAG agent
                "request_topic": "general-info-requests",
                "response_topic": "general-info-responses",
                "timeout": 15,
                "temporary_response": "Let me search our knowledge base for that information. One moment please."
            },
            "pre_admission": { 
                "request_topic": "info-dissemination-requests",
                "response_topic": "info-dissemination-responses",
                "timeout": 25,
                "temporary_response": "I'm retrieving the pre-admission details for you. This might take a moment."
            },
            "post_discharge": { 
                "request_topic": "info-dissemination-requests",
                "response_topic": "info-dissemination-responses",
                "timeout": 25,
                "temporary_response": "I'm looking up post-discharge information. Please wait."
            },
        }
        
        self.pending_agent_responses: Dict[str, Dict[str, Any]] = {}
        self._setup_kafka_listeners() 
    
    # --- Kafka Listener Setup ---
    def _setup_kafka_listeners(self):
        """Set up listeners for agent response topics based on the explicit mapping."""
        for intent_name, config in self.kafka_agent_topic_map.items():
            response_topic = config["response_topic"]
            if response_topic not in self.kafka_client.consumers: 
                self.kafka_client.subscribe_to_responses(response_topic, self._handle_agent_response)
                logger.info(f"Subscribed to Kafka response topic: {response_topic} for intent {intent_name}")
            else:
                logger.debug(f"Already subscribed to Kafka response topic: {response_topic}. Skipping.")
    
    # --- Kafka Agent Response Handler (Runs in background) ---
    async def _handle_agent_response(self, message: Dict[str, Any]):
        """
        Callback handler for Kafka agent responses.
        This runs asynchronously in the background. The result will NOT be returned
        by the original HTTP request to process_message.
        The frontend must use WebSockets or polling to receive this final response.
        """
        correlation_id = message.get("correlation_id")
        status = message.get("status")
        result = message.get("result", {})
        session_id = result.get("session_id")
        agent_context = result.get("agent_context") # Extract agent-specific context

        logger.info("Received agent response via Kafka", 
                    correlation_id=correlation_id, status=status, session_id=session_id)

        if not (correlation_id and correlation_id in self.pending_agent_responses):
            logger.warning(f"No pending request found for correlation_id {correlation_id}. "
                           f"This might be a delayed or unrequested response. Session ID: {session_id}")
            if session_id:
                # Logic for handling unsolicited messages can go here
                if self.websocket_manager:
                    await self.websocket_manager.send_message(session_id, {
                        "type": "final_response",
                        "data": {
                            "session_id": session_id,
                            "response": result.get("response", "Agent update."),
                            "intent": "unsolicited_update",
                            "requires_human_handoff": result.get("requires_human_handoff", False),
                            "suggested_actions": result.get("suggested_actions", []),
                            "correlation_id": None
                        },
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
            return

        pending_request_data = self.pending_agent_responses.pop(correlation_id)
        agent_future = pending_request_data.get("future")
        intent = pending_request_data.get("intent")

        # Check if the RAG agent failed to find an answer.
        is_rag_failure = (
            intent == "general_info" and
            result.get("response") == "I could not find relevant information in the documents to answer your question."
        )

        if is_rag_failure:
            logger.warning("RAG agent failed. Triggering general LLM fallback.", correlation_id=correlation_id, session_id=session_id)
            original_message = pending_request_data.get("message")
            session_data = await self.session_manager.get_session(session_id)

            if original_message and session_data:
                final_payload = await self._handle_general_info_fallback(session_id, original_message, session_data)
                final_payload["correlation_id"] = correlation_id
            else:
                logger.error("Cannot trigger fallback, missing original message or session data.", correlation_id=correlation_id)
                final_payload = result # Use the original failure message
        else:
            # Original success path for all agents
            final_payload = {
                "response": result.get("response", "Agent completed its task."),
                "requires_human_handoff": result.get("requires_human_handoff", False),
                "suggested_actions": result.get("suggested_actions", []),
                "session_id": session_id,
                "intent": intent,
                "correlation_id": correlation_id
            }

        # Resolve future and send final response via WebSocket
        if agent_future and not agent_future.done():
            agent_future.set_result(final_payload)
            logger.info(f"Final response ready for session: {session_id}", correlation_id=correlation_id)
            
            if session_id:
                # Instead of adding a new message, update the temporary one using the correlation_id
                await self.session_manager.update_message_by_correlation_id(
                    session_id, correlation_id, final_payload["response"]
                )

                # --- NEW: Update session context with agent's state ---
                if agent_context:
                    current_session = await self.session_manager.get_session(session_id)
                    if current_session:
                        new_context = {**current_session.get("context", {}), **agent_context}
                        await self.session_manager.update_session(session_id, {"context": new_context})
                        logger.info("Updated session context with data from agent", session_id=session_id, agent_context=agent_context)

                logger.debug(f"Updated assistant message in history for session_id: {session_id}")
                if self.websocket_manager:
                    await self.websocket_manager.send_message(session_id, {
                        "type": "final_response",
                        "data": final_payload,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
        else:
            logger.warning(f"Future for correlation_id {correlation_id} already done or missing. Skipping update.", session_id=session_id)

    # --- Generic Kafka Agent Routing Method (Returns temporary message immediately) ---
    async def _route_to_kafka_agent(self, session_id: str, message: str,
                                     intent: str, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Routes requests to Kafka agents. This method now returns a temporary
        message immediately, and the actual Kafka response will be handled
        asynchronously in the background (e.g., via WebSockets/polling).
        """
        agent_config = self.kafka_agent_topic_map.get(intent)
        if not agent_config:
            logger.error(f"Attempted to route intent '{intent}' to Kafka agent, but no configuration found in kafka_agent_topic_map.")
            # Fallback to general LLM if mapping is missing
            return await self._handle_general_info_fallback(session_id, message, session_data)

        request_topic = agent_config["request_topic"]
        temporary_response_text = agent_config.get("temporary_response", "I'm processing your request. One moment please.")
        # Timeout is still relevant for the asyncio.Future, but not for the immediate return.
        # timeout_seconds = agent_config.get("timeout", 20) 

        correlation_id = str(uuid.uuid4())
        # The Future is still created to be resolved by _handle_agent_response later
        response_future = asyncio.Future() 
        self.pending_agent_responses[correlation_id] = {
            "future": response_future,
            "session_id": session_id,
            "intent": intent,
            "message": message, # Store the original message for potential fallback
            "timestamp": asyncio.get_event_loop().time()
        }
        
        logger.info(f"Sending request to Kafka agent for intent '{intent}'", 
                    correlation_id=correlation_id, request_topic=request_topic, session_id=session_id)

        try:
            await self.kafka_client.send_task_request(
                agent_topic=request_topic,
                task_type=intent, 
                payload={
                    "message": message,
                    "session_id": session_id,
                    "user_context": session_data.get("context", {}),
                    "conversation_history": session_data.get("conversation_history", [])[-3:], 
                    "correlation_id": correlation_id
                },
                correlation_id=correlation_id 
            )

            # IMMEDIATE RETURN: Return the temporary message
            return {
                "response": temporary_response_text,
                "intent": intent,
                "requires_human_handoff": False,
                "suggested_actions": ["wait_for_agent_response"],
                "confidence_score": 0.9,
                "correlation_id": correlation_id
            }
        except Exception as e:
            logger.error(f"Error sending message to Kafka for intent '{intent}' (correlation_id: {correlation_id}): {str(e)}", exc_info=True, session_id=session_id)
            if correlation_id in self.pending_agent_responses:
                del self.pending_agent_responses[correlation_id]
            return {
                "response": "I encountered an issue trying to send your request. Please try again or contact support.",
                "intent": intent,
                "requires_human_handoff": True,
                "suggested_actions": ["contact_support"],
                "confidence_score": 0.0
            }
    
    async def _monitor_agent_timeouts(self):
        """Periodically checks for and handles timed-out agent requests."""
        while True:
            await asyncio.sleep(5) # Check every 5 seconds
            now = asyncio.get_event_loop().time()
            timed_out_ids = []
            for correlation_id, request_data in self.pending_agent_responses.items():
                intent = request_data.get("intent", "unknown")
                agent_config = self.kafka_agent_topic_map.get(intent, {})
                timeout_seconds = agent_config.get("timeout", 30)
                
                if now - request_data["timestamp"] > timeout_seconds:
                    timed_out_ids.append(correlation_id)

            for correlation_id in timed_out_ids:
                request_data = self.pending_agent_responses.pop(correlation_id, None)
                if request_data and self.websocket_manager:
                    session_id = request_data["session_id"]
                    logger.warning("Agent request timed out", correlation_id=correlation_id, session_id=session_id)
                    # This is where you would send a timeout message to the user via WebSocket
                    # For now, we just log it and clean up.

    # --- Intent Classification ---
    async def _classify_intent(self, message: str, session_data: Dict[str, Any]) -> str:
        """Classify user intent using pattern matching and then LLM if no match."""
        try:
            message_lower = message.lower()
            for intent, patterns in self.intent_patterns.items():
                if any(pattern in message_lower for pattern in patterns):
                    logger.info("Intent classified via patterns", intent=intent, message_preview=message[:50])
                    return intent
            
            logger.info("No pattern match, falling back to LLM for intent classification.", message_preview=message[:50])
            classification_prompt = self.prompt_manager.get_prompt(
                "intent_classification", 
                {
                    "message": message,
                    "conversation_history": "\n".join([f"{m['sender']}: {m['content']}" for m in session_data.get("conversation_history", [])[-5:]]),
                    "current_context": json.dumps(session_data.get("context", {})) 
                }
            )
            
            llm_request = LLMRequest(
                prompt=classification_prompt,
                max_tokens=50,
                temperature=0.1, 
                system_prompt="You are an intent classifier for a healthcare chatbot. Respond with only the intent name, e.g., 'appointment_booking', 'general_info', 'medical_emergency'."
            )
            
            try:
                response = await self.llm_provider.generate_response(llm_request)
                intent = response.content.strip().lower()
                
                valid_intents = list(self.intent_patterns.keys())
                if intent in valid_intents:
                    logger.info("Intent classified via LLM", intent=intent, message_preview=message[:50])
                    return intent
                else:
                    logger.warning(f"LLM classified unknown intent: '{intent}'. Defaulting to general_info.", message_preview=message[:50])
                    return "general_info" 
                    
            except Exception as e:
                logger.warning(f"Primary LLM intent classification failed: {str(e)}. Attempting fallback LLM.", message_preview=message[:50], error=str(e))
                try:
                    response = await self.fallback_provider.generate_response(llm_request) 
                    intent = response.content.strip().lower()
                    if intent in valid_intents:
                        logger.info("Intent classified via fallback LLM", intent=intent, message_preview=message[:50])
                        return intent
                    else:
                        logger.warning(f"Fallback LLM classified unknown intent: '{intent}'. Defaulting to general_info.", message_preview=message[:50])
                        return "general_info"
                except Exception as e_fallback:
                    logger.error(f"Fallback LLM intent classification also failed: {str(e_fallback)}. Defaulting to general_info.", message_preview=message[:50], error=str(e_fallback))
                    return "general_info" 
            
        except Exception as e:
            logger.error("Critical error during intent classification process", error=str(e), exc_info=True, message_preview=message[:50])
            return "general_info"

    # --- Specific Handlers for Non-Kafka or Direct Paths ---
    async def _handle_emergency(self, session_id: str, message: str) -> Dict[str, Any]:
        """Handle medical emergency situations directly without Kafka."""
        emergency_response = """
🚨 MEDICAL EMERGENCY DETECTED 🚨

If this is a life-threatening emergency, please:
1. Call emergency services immediately (911/999/112)
2. Go to the nearest emergency room

For urgent but non-life-threatening issues:
- Contact our emergency hotline: [EMERGENCY_NUMBER] (e.g., +62-21-1234567)
- Visit our urgent care center

I'm flagging this for immediate human review.
"""
        logger.critical("Medical emergency detected", session_id=session_id, message=message)
        
        return {
            "response": emergency_response,
            "requires_human_handoff": True,
            "suggested_actions": ["emergency_escalation", "call_emergency_services"]
        }
    
    async def _handle_general_info_fallback(self, session_id: str, message: str, 
                                            session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback to direct LLM when no specific agent is applicable or Kafka agent fails."""
        logger.info("Using direct LLM for general info/fallback", session_id=session_id, message_preview=message[:50])
        try:
            general_prompt = self.prompt_manager.get_prompt(
                "general_info_response", 
                {
                    "message": message,
                    "conversation_history": "\n".join([f"{m['sender']}: {m['content']}" for m in session_data.get("conversation_history", [])[-3:]]),
                    "user_context": json.dumps(session_data.get("context", {})) 
                }
            )
            
            llm_request = LLMRequest(
                prompt=general_prompt,
                max_tokens=1000, 
                temperature=0.7, 
                system_prompt="You are a helpful healthcare assistant. Your attempt to find specific information in the hospital's knowledge base has failed. Now, answer the user's question based on your general knowledge. IMPORTANT: Start your response by stating that you could not find specific information and are providing a general answer. For example: 'I couldn't find specific details in our documents, but generally...'. Do not give medical advice."
            )
            
            try:
                response = await self.llm_provider.generate_response(llm_request)
                content = response.content
                logger.info("Generated general info response with primary LLM", session_id=session_id)
            except Exception as e:
                logger.warning(f"Primary LLM failed for general info/fallback: {str(e)}. Attempting fallback LLM.", session_id=session_id, error=str(e))
                try:
                    response = await self.fallback_provider.generate_response(llm_request)
                    content = response.content
                    logger.info("Generated general info response with fallback LLM", session_id=session_id)
                except Exception as e_fallback:
                    logger.error(f"Fallback LLM also failed for general info/fallback: {str(e_fallback)}", session_id=session_id, error=str(e_fallback))
                    raise 

            return {
                "response": content,
                "requires_human_handoff": False,
                "suggested_actions": []
            }
            
        except Exception as e:
            logger.error("Error in general info fallback process", error=str(e), exc_info=True, session_id=session_id)
            return {
                "response": "I'm sorry, I'm having trouble processing your question right now. Please try again later.",
                "requires_human_handoff": False,
                "suggested_actions": ["try_again_later"]
            }

    # --- Message Routing Logic ---
    async def _route_message(self, session_id: str, message: str, intent: str, 
                             session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Routes the message to the appropriate handler based on intent."""
        
        if intent in self.kafka_agent_topic_map:
            logger.info(f"Routing intent '{intent}' to Kafka agent and returning temporary response.", session_id=session_id)
            # This call will now return the temporary response immediately
            return await self._route_to_kafka_agent(session_id, message, intent, session_data)
        
        # If no specific Kafka agent is mapped, or for direct LLM intents
        logger.info(f"No specific Kafka agent configured for intent '{intent}'. Falling back to general LLM.", session_id=session_id)
        return await self._handle_general_info_fallback(session_id, message, session_data)
            
    # --- Main Message Processing Entry Point ---
    async def process_message(self, user_id: str, message: str, 
                                session_id: Optional[str] = None,
                                context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process incoming user message and orchestrate response"""
        logger.info("Processing message started", received_session_id=session_id, user_id=user_id)
        # The client-provided session_id is respected throughout this flow.
        # A new one is only generated if the client provides none.
        client_provided_session_id = bool(session_id)
        try:
            # 1. Session Management: Get or create the session.
            session_data = await self.session_manager.get_session(session_id) if session_id else None
            
            if not session_data:
                # If session doesn't exist or no ID was provided, create one.
                # Pass the client's session_id if it exists, otherwise a new one will be generated.
                session_id = await self.session_manager.create_session(
                    user_id=user_id, 
                    initial_context=context, 
                    session_id=session_id
                )
                session_data = await self.session_manager.get_session(session_id)
                logger.info("Session ensured", session_id=session_id, user_id=user_id, client_provided_id=client_provided_session_id)

            await self.session_manager.add_message_to_history(
                session_id, "user", message
            )
            logger.debug("User message added to history", session_id=session_id, message_preview=message[:50])
            
            # 2. Intent Classification
            intent = await self._classify_intent(message, session_data or {})
            
            # 3. Route to Specific Handlers / Agents
            if intent == "medical_emergency":
                response_payload = await self._handle_emergency(session_id, message)
            else:
                # This call will now return the temporary response if routed to Kafka
                response_payload = await self._route_message(session_id, message, intent, session_data or {})
            
            # 4. Update Session History with Assistant's Response
            # This will now add the *temporary* response to history for Kafka-routed intents.
            # The *final* response from Kafka agent will need to be added to history
            # by the _handle_agent_response method when it arrives.
            # We add the correlation_id to the metadata so we can find and update this message later.
            await self.session_manager.add_message_to_history(
                session_id, "assistant", response_payload["response"],
                metadata={"correlation_id": response_payload.get("correlation_id"), "status": "pending"}
            )
            logger.debug("Assistant response added to history", session_id=session_id, message_preview=response_payload["response"][:50])
            
            # 5. Update Session Context and Intent
            await self.session_manager.update_session(session_id, {
                "current_intent": intent,
                "context": {**(session_data or {}).get("context", {}), **(context or {})} 
            })
            logger.debug("Session updated", session_id=session_id, current_intent=intent)

            # 6. Return the orchestrated response to the API (this will be the temporary one for Kafka)
            return {
                "response": response_payload["response"],
                "session_id": session_id,
                "intent": intent, 
                "requires_human_handoff": response_payload.get("requires_human_handoff", False),
                "suggested_actions": response_payload.get("suggested_actions", []),
                "correlation_id": response_payload.get("correlation_id") # Pass correlation_id if frontend polls
            }
            
        except Exception as e:
            logger.error("Error processing message", 
                         user_id=user_id, session_id=session_id, error=str(e), exc_info=True)
            
            return {
                "response": "I apologize, but I'm experiencing technical difficulties. Please try again or contact our support team.",
                "session_id": session_id or "error", 
                "intent": "error",
                "requires_human_handoff": True,
                "suggested_actions": ["contact_support"]
            }
