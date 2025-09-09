"""Database operations for appointment management."""
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
import structlog
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.appointment import AppointmentRequest, AppointmentResponse

logger = structlog.get_logger()

class AppointmentDB:
    """Database operations for appointments."""
    
    def __init__(self):
        self.engine = create_engine(settings.DATABASE_URL)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    async def get_doctor_info(
        self,
        doctor_name: Optional[str] = None,
        specialization: Optional[str] = None,
        availability_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get doctor's availability information."""
        query = """
        SELECT 
            d.name AS doctor_name,
            s.name AS specialization,
            a.scheduled_date,
            a.status,
            a.service_type
        FROM appointments.doctors d
        JOIN appointments.specializations s ON d.specialization_id = s.id
        LEFT JOIN appointments.appointments a ON d.id = a.doctor_id
        WHERE 1=1
        """
        params: Dict[str, Any] = {}
        
        if doctor_name:
            query += " AND LOWER(d.name) LIKE LOWER(:doctor_name)"
            params['doctor_name'] = f"%{doctor_name}%"
            
        if specialization:
            query += " AND LOWER(s.name) LIKE LOWER(:specialization)"
            params['specialization'] = f"%{specialization}%"
            
        if availability_date:
            query += " AND DATE(a.scheduled_date) = :availability_date"
            params['availability_date'] = availability_date

        with self.SessionLocal() as session:
            result = session.execute(text(query), params)
            return [dict(row) for row in result]

    async def create_appointment(
        self,
        request: AppointmentRequest
    ) -> Tuple[bool, str]:
        """Create a new appointment."""
        # First check if there's a conflict
        check_query = """
        SELECT COUNT(*) 
        FROM appointments.appointments 
        WHERE doctor_id = :doctor_id 
        AND scheduled_date = :scheduled_date 
        AND status = 'confirmed'
        """
        
        insert_query = """
        INSERT INTO appointments.appointments 
        (id, user_id, doctor_id, scheduled_date, service_type, notes)
        VALUES (:id, :user_id, :doctor_id, :scheduled_date, :service_type, :notes)
        RETURNING id
        """
        
        try:
            with self.SessionLocal() as session:
                # Check for conflicts
                result = session.execute(
                    text(check_query),
                    {
                        "doctor_id": request.doctor_id,
                        "scheduled_date": request.requested_date
                    }
                )
                if result.scalar() > 0:
                    return False, "Time slot already booked"
                
                # Create appointment
                result = session.execute(
                    text(insert_query),
                    {
                        "id": UUID(request.appointment_id),
                        "user_id": request.user_id,
                        "doctor_id": request.doctor_id,
                        "scheduled_date": request.requested_date,
                        "service_type": request.service_type,
                        "notes": request.notes
                    }
                )
                session.commit()
                return True, str(result.scalar())
                
        except Exception as e:
            logger.error("appointment_creation_failed",
                        error=str(e),
                        user_id=request.user_id)
            return False, f"Failed to create appointment: {str(e)}"

    async def cancel_appointment(
        self,
        appointment_id: str
    ) -> Tuple[bool, str]:
        """Cancel an existing appointment."""
        query = """
        UPDATE appointments.appointments
        SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP
        WHERE id = :appointment_id AND status = 'confirmed'
        RETURNING id
        """
        
        try:
            with self.SessionLocal() as session:
                result = session.execute(
                    text(query),
                    {"appointment_id": UUID(appointment_id)}
                )
                session.commit()
                if result.rowcount == 0:
                    return False, "Appointment not found or already cancelled"
                return True, "Appointment cancelled successfully"
                
        except Exception as e:
            logger.error("appointment_cancellation_failed",
                        error=str(e),
                        appointment_id=appointment_id)
            return False, f"Failed to cancel appointment: {str(e)}"
