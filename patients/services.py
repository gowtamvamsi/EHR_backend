import logging
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
from fhir.resources.patient import Patient as FHIRPatient
from fhir.resources.bundle import Bundle
import hl7

logger = logging.getLogger(__name__)

class ImageProcessor:
    @staticmethod
    def compress_image(document):
        """Compress image while maintaining quality"""
        try:
            if document.mime_type.startswith('image/'):
                img = Image.open(document.file)

                # Convert RGBA to RGB if necessary
                if img.mode == 'RGBA':
                    img = img.convert('RGB')

                # Calculate new dimensions while maintaining aspect ratio
                max_size = (2000, 2000)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)

                # Save compressed image
                buffer = BytesIO()
                img.save(buffer, format='JPEG', quality=85, optimize=True)

                # Save original file if not already saved
                if not document.original_file:
                    document.original_file.save(
                        f'original_{document.file.name}',
                        document.file,
                        save=False
                    )

                # Update compressed file
                document.file.save(
                    document.file.name,
                    ContentFile(buffer.getvalue()),
                    save=False
                )
                document.is_compressed = True
                document.save()

                logger.info(f"Successfully compressed image for document {document.id}")
        except Exception as e:
            logger.error(f"Error compressing image for document {document.id}: {str(e)}")
            raise


class FHIRExporter:
    @staticmethod
    def export_patient_data(patient):
        """Export patient data in FHIR format"""
        try:
            # Create FHIR Patient resource
            fhir_patient = patient.to_fhir()

            # Create FHIR Bundle with patient data and observations
            bundle = Bundle(
                type="collection",
                entry=[
                    {"resource": fhir_patient}
                ]
            )

            # Add medical history as observations
            for history in patient.medicalhistory_set.all():
                observation = history.to_fhir_observation()
                bundle.entry.append({"resource": observation})

            # Validate FHIR bundle (optional, add actual validation here if needed)
            if not bundle.is_valid():
                logger.error("FHIR Bundle validation failed.")
                raise ValueError("Invalid FHIR Bundle generated.")

            logger.info(f"Successfully exported FHIR data for patient {patient.patient_id}")
            return bundle.dict()

        except Exception as e:
            logger.error(f"Error exporting FHIR data for patient {patient.patient_id}: {str(e)}")
            raise


class HL7Processor:
    @staticmethod
    def parse_message(message_content):
        """Parse HL7 message"""
        try:
            parsed_message = hl7.parse(message_content)

            # Validate required segments (e.g., MSH, PID)
            if not parsed_message.segment('MSH') or not parsed_message.segment('PID'):
                logger.error("HL7 message missing required segments (MSH, PID).")
                raise ValueError("HL7 message missing required segments (MSH, PID).")

            return {
                'message_type': parsed_message.segment('MSH')[9][0],
                'patient_id': parsed_message.segment('PID')[3][0],
                'content': parsed_message
            }

        except Exception as e:
            logger.error(f"Error parsing HL7 message: {str(e)}")
            raise ValueError(f"Invalid HL7 message: {str(e)}")

    @staticmethod
    def create_hl7_message(patient, message_type="ADT^A01"):
        """Create HL7 message for patient"""
        try:
            # Basic HL7 message template
            message = f"""MSH|^~\\&|EHS|HOSPITAL|RECEIVER|FACILITY|{patient.created_at:%Y%m%d%H%M%S}||{message_type}|MSG00001|P|2.5.1
PID|||{patient.patient_id}||{patient.user.last_name}^{patient.user.first_name}||{patient.date_of_birth:%Y%m%d}|"""

            logger.info(f"Successfully created HL7 message for patient {patient.patient_id}")
            return message

        except Exception as e:
            logger.error(f"Error creating HL7 message for patient {patient.patient_id}: {str(e)}")
            raise