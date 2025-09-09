"""Shared pytest fixtures for the appointment management agent tests."""
import pytest
from datetime import datetime
from app.models.appointment import AppointmentRequest

@pytest.fixture
def sample_appointment_request():
    """Return a sample appointment request for testing."""
    return AppointmentRequest(
        user_id="test_user",
        requested_date=datetime.now(),
        service_type="general-checkup",
        notes="Test appointment"
    )
