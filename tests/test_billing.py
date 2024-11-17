from django.test import TestCase
from decimal import Decimal
from billing.models import Invoice, Payment
from users.models import User
from patients.models import Patient
from appointments.models import Appointment
from datetime import date, time

class BillingTests(TestCase):
    def setUp(self):
        self.doctor = User.objects.create_user(
            username='doctor',
            password='testpass',
            role=User.Role.DOCTOR
        )
        self.patient_user = User.objects.create_user(
            username='patient',
            password='testpass',
            role=User.Role.PATIENT
        )
        self.patient = Patient.objects.create(
            user=self.patient_user,
            patient_id='P12345',
            date_of_birth='1990-01-01'
        )
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date=date(2024, 1, 1),
            time_slot=time(10, 0),
            reason='Regular checkup'
        )

    def test_invoice_creation(self):
        invoice = Invoice.objects.create(
            patient=self.patient,
            appointment=self.appointment,
            invoice_number='INV001',
            amount=Decimal('1000.00'),
            tax=Decimal('180.00'),
            total_amount=Decimal('1180.00'),
            due_date=date(2024, 1, 15)
        )
        self.assertEqual(invoice.status, Invoice.Status.PENDING)
        self.assertEqual(invoice.total_amount, Decimal('1180.00'))

    def test_payment_processing(self):
        invoice = Invoice.objects.create(
            patient=self.patient,
            appointment=self.appointment,
            invoice_number='INV001',
            amount=Decimal('1000.00'),
            tax=Decimal('180.00'),
            total_amount=Decimal('1180.00'),
            due_date=date(2024, 1, 15)
        )
        
        payment = Payment.objects.create(
            invoice=invoice,
            amount=Decimal('1180.00'),
            payment_method='CARD',
            transaction_id='TXN001',
            status='SUCCESS'
        )
        
        self.assertEqual(payment.amount, invoice.total_amount)
        invoice.refresh_from_db()
        invoice.status = Invoice.Status.PAID
        invoice.save()
        self.assertEqual(invoice.status, Invoice.Status.PAID)