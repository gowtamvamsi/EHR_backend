from celery import shared_task
from .models import Document
from .services import ImageProcessor

@shared_task
def process_medical_image(document_id):
    """Asynchronous task to process and compress medical images"""
    try:
        document = Document.objects.get(id=document_id)
        ImageProcessor.compress_image(document)
        return f"Successfully processed document {document_id}"
    except Document.DoesNotExist:
        return f"Document {document_id} not found"
    except Exception as e:
        return f"Error processing document {document_id}: {str(e)}"

@shared_task
def process_hl7_messages():
    """Process pending HL7 messages"""
    from .models import HL7Message
    from .services import HL7Processor
    
    pending_messages = HL7Message.objects.filter(processed=False)
    for message in pending_messages:
        try:
            parsed_data = HL7Processor.parse_message(message.message_content)
            # Process the message based on message type
            # Update patient records accordingly
            message.processed = True
            message.save()
        except Exception as e:
            print(f"Error processing HL7 message {message.id}: {str(e)}")
            continue