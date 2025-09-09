# REST API Agent Integration Example

## Overview

This document provides a complete example of creating and integrating a REST API-based agent with the Backend Orchestrator. Unlike Kafka-based agents that use asynchronous messaging, REST API agents provide synchronous HTTP-based communication.

## Use Cases for REST API Agents

REST API agents are ideal for:
- **External Service Integration**: Connecting to third-party APIs (pharmacy systems, EHR systems)
- **Synchronous Operations**: Operations that need immediate responses
- **Simple Request-Response**: Straightforward data retrieval or validation
- **Legacy System Integration**: Connecting to existing REST-based systems

## Complete Implementation Example

### Scenario: Pharmacy Integration Agent

We'll create an agent that integrates with external pharmacy systems to check prescription status and availability.

### Step 1: Project Structure

```
agents/pharmacy-integration-agent/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py             # Configuration settings
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── endpoints.py      # REST API endpoints
│   ├── clients/
│   │   ├── __init__.py
│   │   └── pharmacy_client.py    # External API client
│   ├── models/
│   │   ├── __init__.py
│   │   ├── requests.py           # Request models
│   │   └── responses.py          # Response models
│   └── services/
│       ├── __init__.py
│       └── pharmacy_service.py   # Business logic
├── tests/
│   ├── __init__.py
│   ├── test_endpoints.py
│   └── test_pharmacy_service.py
├── docs/
│   ├── API_REFERENCE.md
│   └── INTEGRATION_GUIDE.md
├── pyproject.toml
├── .env.example
├── .env
└── README.md
```

### Step 2: Configuration

```python
# app/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Service Configuration
    SERVICE_NAME: str = "pharmacy-integration-agent"
    PORT: int = 8001
    HOST: str = "0.0.0.0"
    
    # External Pharmacy API Configuration
    PHARMACY_API_BASE_URL: str
    PHARMACY_API_KEY: str
    PHARMACY_API_TIMEOUT: int = 30
    
    # Database Configuration (if needed)
    DATABASE_URL: Optional[str] = None
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### Step 3: Data Models

```python
# app/models/requests.py
from pydantic import BaseModel
from typing import Optional, Dict, Any

class PrescriptionCheckRequest(BaseModel):
    """Request to check prescription status"""
    prescription_id: str
    session_id: str
    patient_id: Optional[str] = None
    pharmacy_id: Optional[str] = None

class PrescriptionRefillRequest(BaseModel):
    """Request to initiate prescription refill"""
    prescription_id: str
    session_id: str
    patient_id: str
    quantity: Optional[int] = None
    pickup_preference: Optional[str] = "pharmacy"  # "pharmacy" or "delivery"

class PharmacySearchRequest(BaseModel):
    """Request to search for nearby pharmacies"""
    session_id: str
    location: str  # Address, zip code, or coordinates
    radius_miles: Optional[int] = 10
    insurance_accepted: Optional[str] = None
```

```python
# app/models/responses.py
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class PrescriptionStatus(BaseModel):
    """Prescription status information"""
    prescription_id: str
    status: str  # "ready", "in_progress", "not_found", "expired"
    medication_name: str
    quantity: int
    ready_for_pickup: bool
    estimated_ready_time: Optional[datetime] = None
    pharmacy_name: str
    pharmacy_address: str
    pharmacy_phone: str
    special_instructions: Optional[str] = None

class PrescriptionCheckResponse(BaseModel):
    """Response for prescription status check"""
    status: str  # "success" or "error"
    message: str
    prescription_status: Optional[PrescriptionStatus] = None
    requires_human_handoff: bool = False
    suggested_actions: List[str] = []

class PharmacyInfo(BaseModel):
    """Pharmacy information"""
    pharmacy_id: str
    name: str
    address: str
    phone: str
    distance_miles: float
    hours: Dict[str, str]  # {"monday": "9AM-9PM", ...}
    services: List[str]  # ["prescription_pickup", "delivery", "consultation"]
    insurance_accepted: List[str]

class PharmacySearchResponse(BaseModel):
    """Response for pharmacy search"""
    status: str
    message: str
    pharmacies: List[PharmacyInfo] = []
    total_found: int = 0
```

### Step 4: External API Client

```python
# app/clients/pharmacy_client.py
import httpx
import asyncio
from typing import Dict, Any, List, Optional
import structlog
from app.core.config import settings
from app.models.responses import PrescriptionStatus, PharmacyInfo

logger = structlog.get_logger()

class PharmacyAPIClient:
    """Client for external pharmacy API integration"""
    
    def __init__(self):
        self.base_url = settings.PHARMACY_API_BASE_URL
        self.api_key = settings.PHARMACY_API_KEY
        self.timeout = httpx.Timeout(settings.PHARMACY_API_TIMEOUT)
        
    async def get_prescription_status(self, prescription_id: str) -> Optional[PrescriptionStatus]:
        """Get prescription status from external pharmacy API"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/prescriptions/{prescription_id}",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                # Transform external API response to our model
                return PrescriptionStatus(
                    prescription_id=data["id"],
                    status=data["status"],
                    medication_name=data["medication"]["name"],
                    quantity=data["quantity"],
                    ready_for_pickup=data["ready_for_pickup"],
                    estimated_ready_time=data.get("estimated_ready_time"),
                    pharmacy_name=data["pharmacy"]["name"],
                    pharmacy_address=data["pharmacy"]["address"],
                    pharmacy_phone=data["pharmacy"]["phone"],
                    special_instructions=data.get("special_instructions")
                )
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning("Prescription not found", prescription_id=prescription_id)
                return None
            logger.error("Pharmacy API HTTP error", 
                        status_code=e.response.status_code, 
                        error=str(e))
            raise
        except httpx.RequestError as e:
            logger.error("Pharmacy API request failed", error=str(e))
            raise
        except Exception as e:
            logger.error("Unexpected error calling pharmacy API", error=str(e))
            raise
```

### Step 5: REST API Endpoints

```python
# app/api/v1/endpoints.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List
import structlog
from app.models.requests import PrescriptionCheckRequest, PharmacySearchRequest
from app.models.responses import PrescriptionCheckResponse, PharmacySearchResponse
from app.services.pharmacy_service import PharmacyService

logger = structlog.get_logger()
router = APIRouter(prefix="/v1", tags=["pharmacy"])

def get_pharmacy_service() -> PharmacyService:
    """Dependency injection for pharmacy service"""
    return PharmacyService()

@router.post("/check-prescription", response_model=PrescriptionCheckResponse)
async def check_prescription_status(
    request: PrescriptionCheckRequest,
    pharmacy_service: PharmacyService = Depends(get_pharmacy_service)
) -> PrescriptionCheckResponse:
    """Check prescription status via external pharmacy API"""
    try:
        logger.info("Prescription status check requested", 
                   prescription_id=request.prescription_id,
                   session_id=request.session_id)
        
        response = await pharmacy_service.check_prescription_status(request)
        
        logger.info("Prescription status check completed", 
                   prescription_id=request.prescription_id,
                   status=response.status)
        
        return response
        
    except Exception as e:
        logger.error("Error in prescription status endpoint", 
                    prescription_id=request.prescription_id,
                    error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Internal server error while checking prescription status"
        )

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
```

### Step 6: Backend Orchestrator Integration

```python
# backend_orchestrator/src/workflow/conversation_engine.py

async def _handle_prescription_status(self, session_id: str, message: str, 
                                    session_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle prescription status queries via REST API agent"""
    try:
        # Extract prescription ID from message or session data
        prescription_id = self._extract_prescription_id(message, session_data)
        
        if not prescription_id:
            return {
                "response": "I need your prescription ID to check the status. Can you provide it?",
                "requires_human_handoff": False,
                "suggested_actions": ["request_prescription_id"]
            }
        
        # Call REST API agent
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.PHARMACY_AGENT_URL}/v1/check-prescription",
                json={
                    "prescription_id": prescription_id,
                    "session_id": session_id,
                    "patient_id": session_data.get("patient_id")
                }
            )
            response.raise_for_status()
            result = response.json()
        
        # Format response for user
        if result["status"] == "success":
            response_text = result["message"]
            requires_handoff = result.get("requires_human_handoff", False)
            suggested_actions = result.get("suggested_actions", [])
        else:
            response_text = result.get("message", "Unable to check prescription status")
            requires_handoff = True
            suggested_actions = ["contact_pharmacy"]
        
        return {
            "response": response_text,
            "requires_human_handoff": requires_handoff,
            "suggested_actions": suggested_actions
        }
        
    except httpx.HTTPError as e:
        logger.error("Pharmacy agent HTTP error", error=str(e))
        return await self._handle_prescription_status_fallback(session_id, message, session_data)
    except Exception as e:
        logger.error("Error handling prescription status via REST", error=str(e))
        return await self._handle_prescription_status_fallback(session_id, message, session_data)

def _extract_prescription_id(self, message: str, session_data: Dict[str, Any]) -> Optional[str]:
    """Extract prescription ID from message or session data"""
    import re
    
    # Look for prescription ID patterns in message
    patterns = [
        r'(?:prescription|rx)\s*(?:id|number|#)?\s*:?\s*([A-Z0-9]{6,12})',
        r'([A-Z0-9]{6,12})',  # Generic alphanumeric pattern
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return match.group(1)
    
    # Check session data
    return session_data.get("prescription_id")
```

## Key Differences: REST vs Kafka Agents

### REST API Agents
- **Synchronous**: Immediate request-response
- **Simpler**: Direct HTTP communication
- **External Integration**: Ideal for third-party APIs
- **Stateless**: No message queuing or persistence
- **Error Handling**: HTTP status codes and exceptions

### Kafka Agents
- **Asynchronous**: Message queuing and processing
- **Scalable**: Can handle high message volumes
- **Resilient**: Message persistence and retry mechanisms
- **Complex**: Requires correlation ID management
- **Event-Driven**: Fits microservices architecture

## Best Practices for REST API Agents

1. **Timeout Management**: Always set appropriate timeouts
2. **Error Handling**: Provide meaningful error messages
3. **Health Checks**: Implement comprehensive health endpoints
4. **Logging**: Use structured logging with correlation IDs
5. **Validation**: Validate all input and output data
6. **Security**: Implement proper authentication and authorization
7. **Documentation**: Provide clear API documentation
8. **Testing**: Include unit, integration, and contract tests

## Conclusion

REST API agents provide a straightforward way to integrate external services with the healthcare chatbot system. They're particularly useful for:

- Real-time data retrieval
- External system integration
- Simple request-response patterns
- Legacy system connectivity

The pharmacy integration example demonstrates how to build a complete REST API agent that integrates seamlessly with the Backend Orchestrator while maintaining proper error handling, logging, and monitoring capabilities.
