import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from datetime import datetime, timedelta
from decimal import Decimal
from patients.models import Patient
from appointments.models import Appointment
from billing.models import Invoice

@pytest.mark.django_db
class TestAnalyticsAPI:
    def test_patient_demographics(self, authenticated_client, create_user):
        # Create patients of different ages
        Patient.objects.create(
            user=create_user,
            patient_id='P1',
            date_of_birth='2010-01-01'  # Age: 0-18
        )
        Patient.objects.create(
            user=create_user,
            patient_id='P2',
            date_of_birth='1990-01-01'  # Age: 19-30
        )
        
        response = authenticated_client.get(reverse('analytics-patient-demographics'))
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_patients'] == 2
        assert '0-18' in response.data['age_distribution']
        assert '19-30' in response.data['age_distribution']

    def test_financial_summary(self, authenticated_client, create_user):
        patient = Patient.objects.create(
            user=create_user,
            patient_id='P1',
            date_of_birth='1990-01-01'
        )
        
        # Create invoices
        Invoice.objects.create(
            patient=patient,
            invoice_number='INV001',
            amount=Decimal('1000.00'),
            tax=Decimal('180.00'),
            total_amount=Decimal('1180.00'),
            status=Invoice.Status.PAID,
            due_date='2024-01-15'
        )
        Invoice.objects.create(
            patient=patient,
            invoice_number='INV002',
            amount=Decimal('500.00'),
            tax=Decimal('90.00'),
            total_amount=Decimal('590.00'),
            status=Invoice.Status.PENDING,
            due_date='2024-01-15'
        )
        
        response = authenticated_client.get(
            reverse('analytics-financial-summary'),
            {'period': 'month'}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_revenue'] == '1770.00'
        assert response.data['paid_amount'] == '1180.00'
        assert response.data['pending_amount'] == '590.00'

    def test_appointment_statistics(self, authenticated_client, create_user, doctor_user):
        patient = Patient.objects.create(
            user=create_user,
            patient_id='P1',
            date_of_birth='1990-01-01'
        )
        
        # Create appointments
        Appointment.objects.create(
            patient=patient,
            doctor=doctor_user,
            date='2024-01-01',
            time_slot='10:00:00',
            status=Appointment.Status.COMPLETED
        )
        Appointment.objects.create(
            patient=patient,
            doctor=doctor_user,
            date='2024-01-02',
            time_slot='11:00:00',
            status=Appointment.Status.SCHEDULED
        )
        
        response = authenticated_client.get(
            reverse('analytics-appointment-statistics'),
            {'period': 'month'}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_appointments'] == 2
        assert len(response.data['status_distribution']) == 2
        assert len(response.data['daily_distribution']) == 2