import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from decimal import Decimal
from billing.models import Invoice, Payment
from appointments.models import Appointment

@pytest.fixture
def invoice_data(create_user, doctor_user):
    patient = Patient.objects.create(
        user=create_user,
        patient_id='P12345',
        date_of_birth='1990-01-01'
    )
    appointment = Appointment.objects.create(
        patient=patient,
        doctor=doctor_user,
        date='2024-01-01',
        time_slot='10:00:00'
    )
    return {
        'patient': patient.id,
        'appointment': appointment.id,
        'amount': '1000.00',
        'due_date': '2024-01-15'
    }

@pytest.mark.django_db
class TestBillingAPI:
    def test_create_invoice(self, authenticated_client, invoice_data):
        response = authenticated_client.post(
            reverse('invoice-list'),
            invoice_data,
            format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert Decimal(response.data['total_amount']) == Decimal('1180.00')  # Including 18% GST

    def test_process_payment(self, authenticated_client, invoice_data):
        # Create invoice
        invoice_response = authenticated_client.post(
            reverse('invoice-list'),
            invoice_data,
            format='json'
        )
        
        payment_data = {
            'invoice': invoice_response.data['id'],
            'amount': '1180.00',
            'payment_method': 'CARD',
            'transaction_id': 'TXN001',
            'status': 'SUCCESS'
        }
        
        response = authenticated_client.post(
            reverse('payment-list'),
            payment_data,
            format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED
        
        # Check if invoice status is updated
        invoice = Invoice.objects.get(id=invoice_response.data['id'])
        assert invoice.status == Invoice.Status.PAID

    def test_get_invoice_payments(self, authenticated_client, invoice_data):
        # Create invoice
        invoice_response = authenticated_client.post(
            reverse('invoice-list'),
            invoice_data,
            format='json'
        )
        
        # Create payment
        Payment.objects.create(
            invoice_id=invoice_response.data['id'],
            amount=Decimal('1180.00'),
            payment_method='CARD',
            transaction_id='TXN001',
            status='SUCCESS'
        )
        
        response = authenticated_client.get(
            reverse('invoice-payments', kwargs={'pk': invoice_response.data['id']})
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1