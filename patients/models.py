from django.db import models
from django.core.validators import FileExtensionValidator
from users.models import User
from django.utils.translation import gettext_lazy as _
from fhir.resources.patient import Patient as FHIRPatient
from fhir.resources.observation import Observation as FHIRObservation

class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    patient_id = models.CharField(max_length=20, unique=True)
    date_of_birth = models.DateField()
    blood_group = models.CharField(max_length=5)
    emergency_contact = models.CharField(max_length=15)
    address = models.TextField()
    fhir_id = models.CharField(max_length=64, unique=True, null=True)
    fhir_resource = models.JSONField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def to_fhir(self):
        """Convert patient data to FHIR format"""
        return FHIRPatient(
            id=self.fhir_id,
            identifier=[{
                "system": "urn:oid:2.16.840.1.113883.2.4.6.3",
                "value": self.patient_id
            }],
            name=[{
                "use": "official",
                "family": self.user.last_name,
                "given": [self.user.first_name]
            }],
            birthDate=self.date_of_birth.isoformat(),
            telecom=[{
                "system": "phone",
                "value": self.emergency_contact,
                "use": "mobile"
            }]
        ).dict()

class MedicalHistory(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    condition = models.CharField(max_length=100)
    diagnosis_date = models.DateField()
    notes = models.TextField()
    is_active = models.BooleanField(default=True)
    fhir_observation = models.JSONField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def to_fhir_observation(self):
        """Convert medical history to FHIR Observation"""
        return FHIRObservation(
            subject={"reference": f"Patient/{self.patient.fhir_id}"},
            status="final",
            code={
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "55607-6",
                    "display": self.condition
                }]
            },
            effectiveDateTime=self.diagnosis_date.isoformat(),
            note=[{"text": self.notes}]
        ).dict()

class Document(models.Model):
    class DocumentType(models.TextChoices):
        XRAY = 'XRAY', _('X-Ray')
        ULTRASOUND = 'ULTRASOUND', _('Ultrasound')
        MRI = 'MRI', _('MRI')
        CT = 'CT', _('CT Scan')
        LAB_REPORT = 'LAB', _('Laboratory Report')
        PRESCRIPTION = 'PRESCRIPTION', _('Prescription')
        OTHER = 'OTHER', _('Other')

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    file = models.FileField(
        upload_to='patient_documents/',
        validators=[FileExtensionValidator(
            allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'dcm', 'dicom']
        )]
    )
    document_type = models.CharField(
        max_length=50,
        choices=DocumentType.choices
    )
    mime_type = models.CharField(max_length=100)
    file_size = models.BigIntegerField()  # in bytes
    metadata = models.JSONField(default=dict)
    is_compressed = models.BooleanField(default=False)
    original_file = models.FileField(
        upload_to='patient_documents/original/',
        null=True,
        blank=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

class HL7Message(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    message_type = models.CharField(max_length=50)
    message_content = models.TextField()
    processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['message_type', 'processed'])
        ]