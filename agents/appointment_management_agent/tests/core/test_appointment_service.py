import pytest
from datetime import datetime, timedelta
from app.models.appointment import AppointmentRequest, AppointmentResponse
from app.core.appointment_service import AppointmentService

@pytest.fixture
def llm_client_mock(mocker):
    mock = mocker.MagicMock()
    mock.generate_content.return_value.text = "Appointment confirmed for your requested time."
    return mock

@pytest.fixture
def appointment_service(llm_client_mock):
    return AppointmentService(llm_client=llm_client_mock)

@pytest.fixture
def valid_request():
    return AppointmentRequest(
        user_id="user123",
        requested_date=datetime.now() + timedelta(days=2, hours=2),
        service_type="general-checkup",
        notes="First time visit"
    )

async def test_process_valid_appointment_request(appointment_service, valid_request):
    response = await appointment_service.process_appointment_request(valid_request)
    assert isinstance(response, AppointmentResponse)
    assert response.user_id == valid_request.user_id
    assert response.service_type == valid_request.service_type
    assert response.status == "confirmed"

async def test_validate_appointment_time_within_hours(appointment_service):
    # Test appointment during working hours
    valid_date = datetime.now() + timedelta(days=1)
    valid_date = valid_date.replace(hour=14, minute=0)  # 2 PM
    assert appointment_service._validate_appointment_time(valid_date) is True

    # Test appointment outside working hours
    invalid_date = valid_date.replace(hour=20)  # 8 PM
    assert appointment_service._validate_appointment_time(invalid_date) is False

async def test_validate_appointment_notice_period(appointment_service):
    # Test with insufficient notice
    too_soon = datetime.now() + timedelta(hours=1)
    assert appointment_service._validate_appointment_time(too_soon) is False

    # Test with sufficient notice
    good_notice = datetime.now() + timedelta(days=2)
    good_notice = good_notice.replace(hour=14, minute=0)
    assert appointment_service._validate_appointment_time(good_notice) is True
