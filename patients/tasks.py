from celery import shared_task
from django.utils.timezone import now
from datetime import timedelta
from .models import Patient, MedicalHistory, Notification
from .models import Document
from .services import ImageProcessor
import logging

# Initialize logger
logger = logging.getLogger(__name__)

@shared_task
def notify_missed_follow_ups():
    """Send notifications for missed follow-ups."""
    try:
        overdue_patients = Patient.objects.filter(
            next_follow_up_date__lt=now()
        )
        for patient in overdue_patients:
            Notification.objects.create(
                recipient=patient.user,
                message=f"You missed your follow-up scheduled for {patient.next_follow_up_date}. Please reschedule.",
                notification_type="MISSED_FOLLOW_UP",
                medium="EMAIL"
            )
            logger.info(f"Missed follow-up notification sent to {patient.user.email}.")
    except Exception as e:
        logger.error(f"Error in notify_missed_follow_ups task: {str(e)}")


@shared_task
def notify_irregular_progress():
    """Send notifications for patients with irregular progress."""
    try:
        overdue_threshold = now() - timedelta(days=90)  # No updates for 90 days

        # Detect patients with no recent medical history updates
        patients_with_irregular_progress = Patient.objects.filter(
            medicalhistory__updated_at__lt=overdue_threshold
        ).distinct()

        for patient in patients_with_irregular_progress:
            Notification.objects.create(
                recipient=patient.user,
                message="We noticed a gap in your treatment updates. Please contact your doctor.",
                notification_type="IRREGULAR_PROGRESS",
                medium="EMAIL"
            )
            logger.info(f"Irregular progress notification sent to {patient.user.email}.")
    except Exception as e:
        logger.error(f"Error in notify_irregular_progress task: {str(e)}")


@shared_task
def process_medical_image(document_id):
    """Asynchronous task to process and compress medical images."""

    try:
        document = Document.objects.get(id=document_id)
        ImageProcessor.compress_image(document)
        logger.info(f"Successfully processed document {document_id}")
        return f"Successfully processed document {document_id}"
    except Document.DoesNotExist:
        logger.error(f"Document {document_id} not found")
        return f"Document {document_id} not found"
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}")
        return f"Error processing document {document_id}: {str(e)}"