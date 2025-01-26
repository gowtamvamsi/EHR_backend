from django.test import TestCase
from django.core.exceptions import ValidationError
from appointments.models import Appointment
from users.models import User
from patients.models import Patient
from datetime import date, time

class AppointmentTests(TestCase):
    def setUp(self):
        self.doctor = User.objects.create_user(
            username='doctor',
            password='testpass',
            role=Role.RoleType.DOCTOR
        )
        self.patient_user = User.objects.create_user(
            username='patient',
            password='testpass',
            role=Role.RoleType.PATIENT
        )
        self.patient = Patient.objects.create(
            user=self.patient_user,
            patient_id='P12345',
            date_of_birth='1990-01-01'
        )

    def test_appointment_creation(self):
        appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date=date(2024, 1, 1),
            time_slot=time(10, 0),
            reason='Regular checkup'
        )
        self.assertEqual(appointment.status, Appointment.Status.SCHEDULED)

    def test_appointment_slot_conflict(self):
        Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date=date(2024, 1, 1),
            time_slot=time(10, 0),
            reason='First appointment'
        )
        
        with self.assertRaises(ValidationError):
            Appointment.objects.create(
                patient=self.patient,
                doctor=self.doctor,
                date=date(2024, 1, 1),
                time_slot=time(10, 0),
                reason='Conflicting appointment'
            )