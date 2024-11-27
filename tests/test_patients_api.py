import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock
from patients.models import Patient, Document, MedicalHistory
from patients.services import FHIRExporter, HL7Processor
from users.models import User

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def authenticated_client(api_client, create_user):
    api_client.force_authenticate(user=create_user)
    return api_client

@pytest.fixture
def patient_data():
    return {
        'patient_id': 'P12345',
        'date_of_birth': '1990-01-01',
        'blood_group': 'O+',
        'emergency_contact': '+911234567890',
        'address': 'Test Address'
    }

@pytest.mark.django_db
class TestPatientAPI:
    def test_list_patients(self, authenticated_client):
        response = authenticated_client.get(reverse('patient-list'))
        assert response.status_code == status.HTTP_200_OK

    def test_create_patient(self, authenticated_client, patient_data):
        response = authenticated_client.post(
            reverse('patient-list'),
            patient_data,
            format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert Patient.objects.count() == 1

    def test_get_patient_detail(self, authenticated_client, create_user, patient_data):
        patient = Patient.objects.create(user=create_user, **patient_data)
        response = authenticated_client.get(
            reverse('patient-detail', kwargs={'pk': patient.pk})
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['patient_id'] == patient_data['patient_id']

    @patch('patients.services.FHIRExporter.export_patient_data')
    def test_export_fhir(self, mock_export, authenticated_client, create_user, patient_data):
        patient = Patient.objects.create(user=create_user, **patient_data)
        mock_export.return_value = {'resourceType': 'Patient'}
        
        response = authenticated_client.get(
            reverse('patient-fhir', kwargs={'pk': patient.pk})
        )
        assert response.status_code == status.HTTP_200_OK
        mock_export.assert_called_once()

    @patch('patients.services.HL7Processor.parse_message')
    def test_import_hl7(self, mock_parse, authenticated_client):
        mock_parse.return_value = {
            'message_type': 'ADT',
            'patient_id': 'P12345'
        }
        
        hl7_data = {
            'message_content': 'MSH|^~\\&|SENDING|RECEIVING|20240101||ADT^A01'
        }
        
        response = authenticated_client.post(
            reverse('patient-import-hl7'),
            hl7_data,
            format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED
        mock_parse.assert_called_once()

    def test_medical_history(self, authenticated_client, create_user, patient_data):
        patient = Patient.objects.create(user=create_user, **patient_data)
        MedicalHistory.objects.create(
            patient=patient,
            condition='Hypertension',
            diagnosis_date='2024-01-01',
            notes='Initial diagnosis'
        )
        
        response = authenticated_client.get(
            reverse('patient-medical-history', kwargs={'pk': patient.pk})
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    @patch('patients.tasks.process_medical_image.delay')
    def test_upload_document(self, mock_task, authenticated_client, create_user, patient_data):
        patient = Patient.objects.create(user=create_user, **patient_data)
        
        with open('tests/test_files/test_image.jpg', 'rb') as image_file:
            response = authenticated_client.post(
                reverse('patient-documents', kwargs={'pk': patient.pk}),
                {
                    'title': 'Test X-Ray',
                    'file': image_file,
                    'document_type': 'XRAY',
                    'mime_type': 'image/jpeg'
                },
                format='multipart'
            )
        
        assert response.status_code == status.HTTP_201_CREATED
        mock_task.assert_called_once()