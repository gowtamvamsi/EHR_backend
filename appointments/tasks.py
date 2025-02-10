from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from .models import Appointment
from users.models import User
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_appointment_reminders():
    """Send reminder emails and SMS for upcoming appointments"""
    tomorrow = timezone.now().date() + timedelta(days=1)
    appointments = Appointment.objects.filter(
        date=tomorrow,
        status=Appointment.Status.CONFIRMED
    ).select_related('patient__user', 'doctor')
    
    for appointment in appointments:
        subject = 'Appointment Reminder'
        message = f"You have an appointment tomorrow at {appointment.time_slot} with Dr. {appointment.doctor.get_full_name()}"
        recipient_email = [appointment.patient.user.email]
        recipient_phone = appointment.patient.user.phone_number  # Assuming phone_number exists
        
        # Send email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_email,
            fail_silently=True
        )
        
        # Log the reminder
        logger.info(f"Reminder sent to {appointment.patient.user.email} for appointment {appointment.id}")

@shared_task
def cleanup_cancelled_appointments():
    """Archive or clean up old cancelled appointments"""
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    deleted_count, _ = Appointment.objects.filter(
        status=Appointment.Status.CANCELLED,
        created_at__date__lte=thirty_days_ago
    ).delete()
    
    logger.info(f"{deleted_count} cancelled appointments older than 30 days deleted.")