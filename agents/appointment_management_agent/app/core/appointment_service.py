import os
import json
import structlog
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from uuid import uuid4
from google.generativeai import GenerativeModel

from app.models.appointment import AppointmentRequest, AppointmentResponse
from app.core.config import settings
from app.core.database import AppointmentDB

# This is a placeholder for your actual LLM client
# from app.clients.llm_client import LlmClient 

logger = structlog.get_logger(__name__)

class AppointmentService:
    """Service for handling appointment-related operations"""
    
    def __init__(self, llm_client: GenerativeModel):
        if not llm_client:
            raise ValueError("LLM client must be provided")
        self.llm = llm_client
        self.db = AppointmentDB()
        self.prompts: Dict[str, str] = {}
        self._load_prompts()
        
    def _load_prompts(self):
        """
        Loads prompt templates from files using a robust, absolute path.
        """
        # Build a path relative to the current file's location
        current_dir = Path(__file__).parent
        # Navigate up to 'app' and then down to 'prompts'
        prompts_dir = current_dir.parent / "prompts"
        
        prompt_files = {
            "booking_confirmation": "booking_confirmation.txt",
            "cancellation_policy": "cancellation_policy_explain.txt",
            "reminder_template": "reminder_template.txt",
        }

        logger.info("Loading prompts...", prompts_dir=str(prompts_dir))
        
        for key, filename in prompt_files.items():
            prompt_path = prompts_dir / filename
            try:
                with open(prompt_path, "r", encoding="utf-8") as f:
                    self.prompts[key] = f.read()
                logger.info("Prompt loaded successfully.", prompt=key, path=str(prompt_path))
            except FileNotFoundError:
                logger.error("Prompt file not found.", path=str(prompt_path))
                raise
            except Exception as e:
                logger.error("Failed to load prompt.", prompt=key, path=str(prompt_path), error=str(e))
                raise

    def _validate_appointment_time(self, requested_date: datetime) -> bool:
        """Validate if the requested appointment time is valid"""
        # Check if appointment is within working hours
        if requested_date.hour < settings.WORKING_HOURS_START or requested_date.hour >= settings.WORKING_HOURS_END:
            return False
            
        # Check if appointment has sufficient notice
        min_notice = timedelta(hours=settings.MIN_BOOKING_HOURS_NOTICE)
        if requested_date - datetime.now() < min_notice:
            return False
            
        # Check if appointment is not too far in the future
        max_ahead = timedelta(days=settings.MAX_BOOKING_DAYS_AHEAD)
        if requested_date - datetime.now() > max_ahead:
            return False
            
        return True
    
    async def _generate_confirmation(self, request: AppointmentRequest) -> str:
        """Generate a confirmation message using the LLM"""
        prompt = self.prompts["booking_confirmation"].format(
            date=request.requested_date.strftime("%Y-%m-%d %H:%M"),
            service=request.service_type
        )
        response = await self.llm.generate_content(prompt)
        return response.text

    async def get_doctor_availability(
        self,
        doctor_name: Optional[str] = None,
        specialization: Optional[str] = None,
        date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get doctor availability information"""
        return await self.db.get_doctor_info(
            doctor_name=doctor_name,
            specialization=specialization,
            availability_date=date
        )
            
    async def process_appointment_request(self, request: AppointmentRequest) -> AppointmentResponse:
        """Process an appointment request and return a response"""
        try:
            # Validate appointment time is within working hours and notice period
            if not self._validate_appointment_time(request.requested_date):
                raise ValueError("Requested appointment time is outside working hours or insufficient notice period")
                
            # Generate a unique appointment ID
            request.appointment_id = f"apt_{uuid4().hex[:8]}"
            
            # Try to create the appointment in the database
            success, result = await self.db.create_appointment(request)
            if not success:
                raise ValueError(f"Failed to create appointment: {result}")
            
            # Generate confirmation message
            confirmation = await self._generate_confirmation(request)
            
            # Create and return response
            return AppointmentResponse(
                appointment_id=request.appointment_id,
                user_id=request.user_id,
                scheduled_date=request.requested_date,
                service_type=request.service_type,
                status="confirmed",
                notes=confirmation
            )
            
        except Exception as e:
            logger.error("appointment_request_failed",
                        error=str(e),
                        user_id=request.user_id,
                        requested_date=request.requested_date)
            raise
            
    async def cancel_appointment(self, appointment_id: str) -> Tuple[bool, str]:
        """Cancel an existing appointment"""
        try:
            success, message = await self.db.cancel_appointment(appointment_id)
            if success:
                logger.info("appointment_cancelled_successfully",
                           appointment_id=appointment_id)
            else:
                logger.error("appointment_cancellation_failed",
                           appointment_id=appointment_id,
                           reason=message)
            return success, message
        except Exception as e:
            logger.error("appointment_cancellation_error",
                        error=str(e),
                        appointment_id=appointment_id)
            return False, str(e)

    def _extract_appointment_parameters(self, user_input: str, schedule_data: Optional[List[Dict[str, Any]]] = None, conversation_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        prompt = PromptTemplate.from_template(prompt_appointment_agent)
        try:
            # Using JsonOutputParser is more robust than regex
            chain = prompt | self.vertex_ai | self.json_parser
            result = chain.invoke({
                "user_input": user_input,
                "schedule_data": str(schedule_data) if schedule_data else "No previous schedule data available",
                "conversation_history": str(conversation_history) if conversation_history else "No previous conversation history",
                "current_date": __import__('datetime').date.today().isoformat()
            })

            # The parser already returns a dict
            filtered_params = {k: v for k, v in result.items() if v is not None and v != "null"}
            
            if "appointment_date" in filtered_params:
                if isinstance(filtered_params["appointment_date"], str):
                    filtered_params["appointment_date"] = convert_relative_date(filtered_params["appointment_date"])
            return filtered_params
        except Exception as e:
            logger.error(f"Error extracting appointment parameters: {e}", exc_info=True)
            return {}

    def _confirm_appointment_action(self, user_input: str, appointment_params: Dict[str, Any]) -> bool:
        prompt = PromptTemplate.from_template(prompt_confirm_appointment)
        chain = prompt | self.vertex_ai | self.str_parser
        result = chain.invoke({
            "user_input": user_input,
            "appointment_params": str(appointment_params)
        })
        return result.strip().lower() == "yes"

    def _format_appointment_response(self, result: str, action: str, appointment_params: Dict[str, Any]) -> str:
        prompt = PromptTemplate.from_template(prompt_format_appointment_response)
        chain = prompt | self.vertex_ai | self.str_parser
        response = chain.invoke({
            "action": action,
            "appointment_params": str(appointment_params),
            "result": result
        })
        return response.strip()

    def _analyze_appointment_parameters(self, user_input: str, previous_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        prompt = PromptTemplate.from_template(prompt_analyze_appointment_parameters)
        try:
            chain = prompt | self.vertex_ai | self.json_parser
            result = chain.invoke({
                "user_input": user_input,
                "previous_params": str(previous_params) if previous_params else "No previous parameters"
            })
            
            analysis = result
            if previous_params:
                analysis.setdefault("specialization", previous_params.get("specialization"))
                analysis.setdefault("hospital_name", previous_params.get("hospital_name"))
                
                analysis["missing_info"] = [
                    p for p in ["specialization", "hospital_name"] if not analysis.get(p) or analysis.get(p) == "null"
                ]
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing appointment parameters: {e}", exc_info=True)
            return {
                "specialization": None, "hospital_name": None,
                "missing_info": ["specialization", "hospital_name"],
                "response": "Maaf, saya tidak dapat memproses permintaan Anda. Silakan berikan informasi tentang spesialisasi dokter dan lokasi rumah sakit yang Anda inginkan."
            }

    def _format_schedule_response(self, schedule_data: list, user_input: str) -> str:
        if not schedule_data:
            return "Maaf, tidak ada jadwal dokter yang sesuai dengan kriteria pencarian Anda."
        prompt = PromptTemplate.from_template(prompt_format_schedule_response)
        chain = prompt | self.vertex_ai | self.str_parser
        response = chain.invoke({"schedule_data": str(schedule_data), "user_input": user_input})
        return response.strip()

    def process_query(self, user_input: str, previous_context: Optional[Dict[str, Any]] = None, conversation_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        try:
            logger.info(f"Processing appointment query: {user_input}")
            
            schedule_data = previous_context.get("raw_data") if previous_context else None
            previous_params = previous_context.get("appointment_params") if previous_context else {}
            
            params = self._extract_appointment_parameters(user_input, schedule_data, conversation_history)
            
            # Merge with previous parameters, giving new ones precedence
            merged_params = {**previous_params, **params}
            
            logger.info(f"Merged appointment parameters: {merged_params}")
            
            if "action" not in merged_params:
                if any(word in user_input.lower() for word in ["cancel", "batalkan"]):
                    merged_params["action"] = "cancel"
                elif any(word in user_input.lower() for word in ["edit", "ubah", "ganti"]):
                    merged_params["action"] = "edit"
                elif any(word in user_input.lower() for word in ["book", "pesan", "buat"]):
                    merged_params["action"] = "book"
                else:
                    merged_params["action"] = "read"
            
            action = merged_params.get("action", "read")
            
            # --- ACTION HANDLERS ---

            if action == "read":
                return self._handle_read_action(merged_params, user_input)
            
            if action == "book":
                return self._handle_book_action(merged_params, user_input, previous_params)

            if action == "edit":
                return self._handle_edit_action(merged_params, user_input)

            if action == "cancel":
                return self._handle_cancel_action(merged_params, user_input)

            return {
                "response": "Maaf, saya tidak dapat memproses permintaan Anda. Silakan coba lagi dengan memberikan informasi yang lebih jelas.",
                "source": "appointment_agent", "has_context": False, "similarity_score": 0.0,
                "appointment_params": merged_params, "status": "error"
            }
            
        except Exception as e:
            logger.error(f"Error processing appointment query: {e}", exc_info=True)
            return {
                "response": f"Maaf, terjadi kesalahan saat memproses permintaan appointment: {str(e)}",
                "source": "error", "has_context": False, "similarity_score": 0.0, "status": "error"
            }

    def _handle_read_action(self, params: Dict, user_input: str) -> Dict:
        schedule_data = get_doctor_info(
            database_name=settings.DATABASE_NAME,
            doctor_name=params.get("doctor_name"),
            hospital_name=params.get("hospital_name"),
            specialization=params.get("specialization"),
            availability_date=params.get("appointment_date"),
            start_time=params.get("appointment_time")
        )
        logger.info(f"Retrieved {len(schedule_data)} schedule entries for read action.")
        answer = self._format_schedule_response(schedule_data, user_input)
        return {
            "response": answer, "source": "appointment_database", "has_context": True,
            "similarity_score": 1.0, "raw_data": schedule_data,
            "appointment_params": params, "status": "complete"
        }

    def _handle_book_action(self, params: Dict, user_input: str, previous_params: Dict) -> Dict:
        required_params = ["doctor_name", "hospital_name", "appointment_date", "appointment_time", "payment_method"]
        missing_params = [p for p in required_params if p not in params]

        if missing_params:
            return self._handle_missing_booking_params(params, user_input, previous_params, missing_params)

        if not self._confirm_appointment_action(user_input, params):
            return {
                "response": f"Apakah Anda yakin ingin booking appointment dengan Dr. {params.get('doctor_name')} pada tanggal {params.get('appointment_date')} pukul {params.get('appointment_time')} dengan metode pembayaran {params.get('payment_method')}? Mohon konfirmasi (Ya/Tidak).",
                "source": "appointment_agent", "has_context": True, "similarity_score": 1.0,
                "appointment_params": params, "status": "confirmation_needed"
            }

        new_appointment_id = "app_" + str(uuid4())
        appointment_time = str(params["appointment_time"])
        if hasattr(params["appointment_time"], 'strftime'):
            appointment_time = params["appointment_time"].strftime("%H:%M:%S")

        result = booking_appointment(
            database_name=settings.DATABASE_NAME,
            doctor_name=params["doctor_name"],
            hospital_name=params["hospital_name"],
            appointment_date=params["appointment_date"],
            appointment_time=appointment_time,
            payment_method=params["payment_method"],
            new_appointment_id=new_appointment_id
        )
        
        params["appointment_id"] = new_appointment_id
        formatted_response = self._format_appointment_response(result, "book", params)
        
        return {
            "response": formatted_response, "source": "appointment_database", "has_context": True,
            "similarity_score": 1.0, "raw_data": result, "appointment_params": params,
            "status": "complete", "appointment_id": new_appointment_id
        }

    def _handle_missing_booking_params(self, params: Dict, user_input: str, previous_params: Dict, missing_params: List) -> Dict:
        # Logic for when doctor/hospital is missing -> need to query for doctors
        if "doctor_name" in missing_params or "hospital_name" in missing_params:
            analysis = self._analyze_appointment_parameters(user_input, previous_params)
            params.update({k: v for k, v in analysis.items() if v and v != "null"})

            if "specialization" in params and "hospital_name" in params:
                return self._query_and_present_doctors(params)
            else:
                return {
                    "response": analysis.get("response", "Mohon berikan informasi yang diperlukan untuk booking."),
                    "source": "appointment_agent", "has_context": True, "similarity_score": 1.0,
                    "appointment_params": params, "status": "parameter_collection"
                }

        # Logic for when only payment method is missing
        if "payment_method" in missing_params:
            return {
                "response": f"Silakan pilih metode pembayaran untuk booking dengan Dr. {params.get('doctor_name')} pada tanggal {params.get('appointment_date')} pukul {params.get('appointment_time')}:\n\n1. Pribadi\n2. Asuransi\n3. BPJS Kesehatan\n4. Kartu Kredit",
                "source": "appointment_agent", "has_context": True, "similarity_score": 1.0,
                "appointment_params": params, "status": "payment_method_needed"
            }

        # Generic message for other missing params
        return {
            "response": f"Untuk melakukan booking, saya memerlukan informasi tambahan: {', '.join(missing_params)}. Mohon berikan informasi tersebut.",
            "source": "appointment_agent", "has_context": True, "similarity_score": 1.0,
            "appointment_params": params, "status": "incomplete"
        }

    def _query_and_present_doctors(self, params: Dict) -> Dict:
        doctor_schedules = get_doctor_info(
            database_name=settings.DATABASE_NAME,
            specialization=params["specialization"],
            hospital_name=params["hospital_name"]
        )

        if not doctor_schedules:
            return {
                "response": f"Maaf, tidak ada dokter spesialis {params['specialization']} yang tersedia di {params['hospital_name']} saat ini. Silakan coba spesialisasi lain atau lokasi lain.",
                "source": "appointment_agent", "has_context": True, "similarity_score": 1.0,
                "appointment_params": params, "status": "no_doctors_available"
            }

        # Formatting logic to present doctor schedules
        doctors_info = {}
        for schedule in doctor_schedules:
            doctor_name = schedule.get("doctor_name")
            if doctor_name not in doctors_info:
                doctors_info[doctor_name] = {"hospital": schedule.get("hospital_name"), "dates": {}}
            
            date = schedule.get("availability_date")
            if date not in doctors_info[doctor_name]["dates"]:
                doctors_info[doctor_name]["dates"][date] = []
            
            if not schedule.get("is_booked"):
                time_val = schedule.get("start_time")
                time_str = time_val.strftime("%H:%M:%S") if hasattr(time_val, 'strftime') else str(time_val)
                doctors_info[doctor_name]["dates"][date].append(time_str)

        response = f"Berikut jadwal dokter spesialis {params['specialization']} di {params['hospital_name']} yang tersedia:\n\n"
        for doctor, info in doctors_info.items():
            response += f"Dr. {doctor} - {info['hospital']}\n"
            for date, times in info["dates"].items():
                if times:
                    response += f"  Tanggal {date}: {', '.join(times)}\n"
        
        response += "\nSilakan pilih dokter dan jadwal yang Anda inginkan dengan format: 'Saya pilih Dr. [nama dokter] pada tanggal [tanggal] jam [waktu]'"

        return {
            "response": response, "source": "appointment_agent", "has_context": True,
            "similarity_score": 1.0, "raw_data": doctor_schedules,
            "appointment_params": params, "status": "doctor_selection_needed"
        }

    def _handle_edit_action(self, params: Dict, user_input: str) -> Dict:
        required_params = ["doctor_name", "hospital_name", "appointment_date", "appointment_time", "payment_method", "existing_appointment_id"]
        missing_params = [p for p in required_params if p not in params]

        if missing_params:
            return {
                "response": f"Untuk mengubah appointment, saya memerlukan informasi tambahan: {', '.join(missing_params)}. Mohon berikan informasi tersebut.",
                "source": "appointment_agent", "has_context": True, "similarity_score": 1.0,
                "appointment_params": params, "status": "incomplete"
            }

        if not self._confirm_appointment_action(user_input, params):
            return {
                "response": f"Apakah Anda yakin ingin mengubah appointment menjadi dengan Dr. {params.get('doctor_name')} pada tanggal {params.get('appointment_date')} pukul {params.get('appointment_time')}? Mohon konfirmasi (Ya/Tidak).",
                "source": "appointment_agent", "has_context": True, "similarity_score": 1.0,
                "appointment_params": params, "status": "confirmation_needed"
            }

        appointment_time = str(params["appointment_time"])
        if hasattr(params["appointment_time"], 'strftime'):
            appointment_time = params["appointment_time"].strftime("%H:%M:%S")

        result = edit_booking_appointment(
            database_name=settings.DATABASE_NAME,
            doctor_name=params["doctor_name"],
            hospital_name=params["hospital_name"],
            appointment_date=params["appointment_date"],
            appointment_time=appointment_time,
            payment_method=params["payment_method"],
            existing_appointment_id=params["existing_appointment_id"]
        )
        
        formatted_response = self._format_appointment_response(result, "edit", params)
        return {
            "response": formatted_response, "source": "appointment_database", "has_context": True,
            "similarity_score": 1.0, "raw_data": result, "appointment_params": params, "status": "complete"
        }

    def _handle_cancel_action(self, params: Dict, user_input: str) -> Dict:
        if "existing_appointment_id" not in params:
            return {
                "response": "Untuk membatalkan appointment, saya memerlukan ID appointment yang ingin dibatalkan. Mohon berikan ID appointment tersebut.",
                "source": "appointment_agent", "has_context": True, "similarity_score": 1.0,
                "appointment_params": params, "status": "incomplete"
            }

        if not self._confirm_appointment_action(user_input, params):
            return {
                "response": f"Apakah Anda yakin ingin membatalkan appointment dengan ID {params.get('existing_appointment_id')}? Mohon konfirmasi (Ya/Tidak).",
                "source": "appointment_agent", "has_context": True, "similarity_score": 1.0,
                "appointment_params": params, "status": "confirmation_needed"
            }

        result = cancel_booking_appointment(
            database_name=settings.DATABASE_NAME,
            existing_appointment_id=params["existing_appointment_id"]
        )
        
        formatted_response = self._format_appointment_response(result, "cancel", params)
        return {
            "response": formatted_response, "source": "appointment_database", "has_context": True,
            "similarity_score": 1.0, "raw_data": result, "appointment_params": params, "status": "complete"
        }

