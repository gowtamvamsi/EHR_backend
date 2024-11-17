import os
import json
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
from django.conf import settings
from fhir.resources.patient import Patient as FHIRPatient
from fhir.resources.bundle import Bundle
import hl7

class ImageProcessor:
    @staticmethod
    def compress_image(document):
        """Compress image while maintaining quality"""
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

class FHIRExporter:
    @staticmethod
    def export_patient_data(patient):
        """Export patient data in FHIR format"""
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
        
        return bundle.dict()

class HL7Processor:
    @staticmethod
    def parse_message(message_content):
        """Parse HL7 message"""
        try:
            parsed_message = hl7.parse(message_content)
            return {
                'message_type': parsed_message.segment('MSH')[9][0],
                'patient_id': parsed_message.segment('PID')[3][0],
                'content': parsed_message
            }
        except Exception as e:
            raise ValueError(f"Invalid HL7 message: {str(e)}")
    
    @staticmethod
    def create_hl7_message(patient, message_type="ADT^A01"):
        """Create HL7 message for patient"""
        # Basic HL7 message template
        message = f"""MSH|^~\\&|EHS|HOSPITAL|RECEIVER|FACILITY|{patient.created_at:%Y%m%d%H%M%S}||{message_type}|MSG00001|P|2.5.1
PID|||{patient.patient_id}||{patient.user.last_name}^{patient.user.first_name}||{patient.date_of_birth:%Y%m%d}|"""
        return message