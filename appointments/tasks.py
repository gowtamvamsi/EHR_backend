from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from twilio.rest import Client
from .models import Appointment
from users.models import User
import logging

logger = logging.getLogger(__name__)

# Twilio Credentials from settings
TWILIO_ACCOUNT_SID = settings.TWILIO_ACCOUNT_SID
TWILIO_AUTH_TOKEN = settings.TWILIO_AUTH_TOKEN
TWILIO_PHONE_NUMBER = settings.TWILIO_PHONE_NUMBER

@shared_task
def send_appointment_reminders():
    """Send reminder emails and SMS for upcoming appointments"""
    tomorrow = timezone.now().date() + timedelta(days=1)
    appointments = Appointment.objects.filter(
        date=tomorrow,
        status=Appointment.Status.CONFIRMED
    ).select_related('patient__user', 'doctor')
    
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    
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
        
        # Send SMS
        if recipient_phone:
            try:
                client.messages.create(
                    body=message,
                    from_=TWILIO_PHONE_NUMBER,
                    to=recipient_phone
                )
                logger.info(f"SMS reminder sent to {recipient_phone} for appointment {appointment.id}")
            except Exception as e:
                logger.error(f"Failed to send SMS reminder to {recipient_phone}: {str(e)}")
        
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

@shared_task
def send_cancellation_notification(appointment_id):
    """Send notification to the patient when an appointment is cancelled"""
    try:
        appointment = Appointment.objects.get(id=appointment_id)
        subject = 'Appointment Cancelled'
        message = f"Your appointment with Dr. {appointment.doctor.get_full_name()} on {appointment.date} at {appointment.time_slot} has been cancelled. Please contact us if you need to reschedule."
        recipient_email = [appointment.patient.user.email]
        recipient_phone = appointment.patient.user.phone_number
        
        # Send email notification
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_email,
            fail_silently=True
        )
        
        # Send SMS notification
        if recipient_phone:
            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            try:
                client.messages.create(
                    body=message,
                    from_=TWILIO_PHONE_NUMBER,
                    to=recipient_phone
                )
                logger.info(f"SMS cancellation notification sent to {recipient_phone} for appointment {appointment.id}")
            except Exception as e:
                logger.error(f"Failed to send SMS cancellation notification to {recipient_phone}: {str(e)}")
        
        logger.info(f"Cancellation notification sent to {appointment.patient.user.email} for appointment {appointment.id}")
    except Appointment.DoesNotExist:
        logger.error(f"Appointment {appointment_id} not found for cancellation notification.")
