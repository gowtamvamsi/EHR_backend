from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from .models import Appointment

@shared_task
def send_appointment_reminders():
    """Send reminder emails for upcoming appointments"""
    tomorrow = timezone.now().date() + timedelta(days=1)
    appointments = Appointment.objects.filter(
        date=tomorrow,
        status=Appointment.Status.CONFIRMED
    ).select_related('patient__user', 'doctor')
    
    for appointment in appointments:
        send_mail(
            subject='Appointment Reminder',
            message=f'You have an appointment tomorrow at {appointment.time_slot} with Dr. {appointment.doctor.get_full_name()}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[appointment.patient.user.email],
            fail_silently=True
        )

@shared_task
def cleanup_cancelled_appointments():
    """Archive or clean up old cancelled appointments"""
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    Appointment.objects.filter(
        status=Appointment.Status.CANCELLED,
        created_at__date__lte=thirty_days_ago
    ).update(archived=True)