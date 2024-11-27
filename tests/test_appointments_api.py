import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from datetime import date, time
from appointments.models import Appointment
from users.models import User
from patients.models import Patient

@pytest.fixture
def doctor_user():
    return User.objects.create_user(
        username='doctor',
        password='testpass',
        role=User.Role.DOCTOR
    )

@pytest.fixture
def appointment_data(create_user, doctor_user):
    patient = Patient.objects.create(
        user=create_user,
        patient_id='P12345',
        date_of_birth='1990-01-01'
    )
    return {
        'patient': patient.id,
        'doctor': doctor_user.id,
        'date': '2024-01-01',
        'time_slot': '10:00:00',
        'reason': 'Regular checkup'
    }

@pytest.mark.django_db
class TestAppointmentAPI:
    def test_create_appointment(self, authenticated_client, appointment_data):
        response = authenticated_client.post(
            reverse('appointment-list'),
            appointment_data,
            format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert Appointment.objects.count() == 1

    def test_appointment_conflict(self, authenticated_client, appointment_data):
        # Create first appointment
        authenticated_client.post(
            reverse('appointment-list'),
            appointment_data,
            format='json'
        )
        
        # Try to create conflicting appointment
        response = authenticated_client.post(
            reverse('appointment-list'),
            appointment_data,
            format='json'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_appointment_status(self, authenticated_client, appointment_data):
        # Create appointment
        response = authenticated_client.post(
            reverse('appointment-list'),
            appointment_data,
            format='json'
        )
        appointment_id = response.data['id']
        
        # Update status
        response = authenticated_client.put(
            reverse('appointment-status', kwargs={'pk': appointment_id}),
            {'status': 'CONFIRMED'},
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'CONFIRMED'

    def test_get_doctor_schedule(self, authenticated_client, doctor_user, appointment_data):
        # Create appointment
        authenticated_client.post(
            reverse('appointment-list'),
            appointment_data,
            format='json'
        )
        
        response = authenticated_client.get(
            reverse('appointment-doctor-schedule'),
            {'doctor_id': doctor_user.id}
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1