import pytest
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from patients.models import Patient, Document, MedicalHistory
from patients.services import ImageProcessor, FHIRExporter, HL7Processor
from users.models import User

class PatientModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testpatient',
            password='testpass',
            role=User.Role.PATIENT
        )
        self.patient = Patient.objects.create(
            user=self.user,
            patient_id='P12345',
            date_of_birth='1990-01-01',
            blood_group='O+',
            emergency_contact='+911234567890',
            address='Test Address'
        )

    def test_patient_creation(self):
        self.assertEqual(self.patient.patient_id, 'P12345')
        self.assertEqual(self.patient.blood_group, 'O+')

    def test_fhir_conversion(self):
        fhir_data = self.patient.to_fhir()
        self.assertEqual(fhir_data['identifier'][0]['value'], 'P12345')

class DocumentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.patient = Patient.objects.create(
            user=self.user,
            patient_id='P12345',
            date_of_birth='1990-01-01'
        )
        self.test_image = SimpleUploadedFile(
            "test.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        self.document = Document.objects.create(
            patient=self.patient,
            title='Test X-Ray',
            file=self.test_image,
            document_type=Document.DocumentType.XRAY,
            mime_type='image/jpeg',
            file_size=1000,
            uploaded_by=self.user
        )

    def test_document_creation(self):
        self.assertEqual(self.document.document_type, Document.DocumentType.XRAY)
        self.assertEqual(self.document.mime_type, 'image/jpeg')

@pytest.mark.django_db
class TestHL7Integration:
    def test_hl7_message_parsing(self):
        test_message = """MSH|^~\\&|SENDING_APP|SENDING_FACILITY|RECEIVING_APP|RECEIVING_FACILITY|20230801123456||ADT^A01|MSG00001|P|2.5.1
PID|||P12345||Doe^John||19800101|"""
        
        parsed_data = HL7Processor.parse_message(test_message)
        assert parsed_data['message_type'] == 'ADT'
        assert parsed_data['patient_id'] == 'P12345'