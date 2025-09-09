from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.core.dependencies import get_appointment_service
from app.core.appointment_service import AppointmentService

router = APIRouter(prefix="/v1", tags=["appointments"])

@router.post("/book")
async def book_appointment(
    request: dict,
    appointment_service: AppointmentService = Depends(get_appointment_service)
):
    """Book a new appointment."""
    try:
        result = await appointment_service.book_appointment(request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )