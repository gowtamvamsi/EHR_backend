from django.db import models
from django.core.validators import RegexValidator, FileExtensionValidator
from users.models import User
from django.utils.translation import gettext_lazy as _
from fhir.resources.patient import Patient as FHIRPatient
from fhir.resources.observation import Observation as FHIRObservation

# New Notification Model
class Notification(models.Model):
    """Model for storing notifications sent to users."""
    class NotificationType(models.TextChoices):
        MISSED_FOLLOW_UP = 'MISSED_FOLLOW_UP', _('Missed Follow-Up')
        IRREGULAR_PROGRESS = 'IRREGULAR_PROGRESS', _('Irregular Progress')

    recipient = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices
    )
    sent_at = models.DateTimeField(auto_now_add=True)
    is_sent = models.BooleanField(default=False)
    medium = models.CharField(
        max_length=10,
        choices=[('EMAIL', 'Email'), ('SMS', 'SMS'), ('PUSH', 'Push Notification')]
    )

    def __str__(self):
        return f"Notification({self.notification_type}) for {self.recipient}"  # NEW MODEL ADDED


class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    patient_id = models.CharField(max_length=20, unique=True)
    date_of_birth = models.DateField()
    blood_group = models.CharField(
        max_length=5,
        validators=[RegexValidator(
            regex=r'^(A|B|AB|O)[+-]$',
            message="Enter a valid blood group (e.g., A+, O-)."
        )]
    )  # VALIDATOR ADDED
    emergency_contact = models.CharField(
        max_length=15,
        validators=[RegexValidator(
            regex=r'^\+?\d{10,15}$',
            message="Enter a valid phone number."
        )]
    )  # VALIDATOR ADDED
    address = models.TextField()
    next_follow_up_date = models.DateField(null=True, blank=True)  # NEW FIELD ADDED
    fhir_id = models.CharField(max_length=64, unique=True, null=True)
    fhir_resource = models.JSONField(null=True, blank=True)  # Allow blank FHIR resources
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

    def __str__(self):
        return f"Patient({self.patient_id})"


class MedicalHistory(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    condition = models.CharField(max_length=100)
    diagnosis_date = models.DateField()
    next_follow_up_date = models.DateField(null=True, blank=True)  # NEW FIELD ADDED
    notes = models.TextField()
    is_active = models.BooleanField(default=True)
    fhir_observation = models.JSONField(null=True, blank=True)  # Allow blank FHIR observations
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

    def __str__(self):
        return f"MedicalHistory({self.condition} for {self.patient.patient_id})"


class Document(models.Model):
    class DocumentType(models.TextChoices):
        XRAY = 'XRAY', _('X-Ray')
        ULTRASOUND = 'ULTRASOUND', _('Ultrasound')
        MRI = 'MRI', _('MRI')
        CT = 'CT', _('CT Scan')
        LAB_REPORT = 'LAB', _('Laboratory Report')
        PRESCRIPTION = 'PRESCRIPTION', _('Prescription')
        OTHER = 'OTHER', _('Other')

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='documents')
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

    def save(self, *args, **kwargs):
        """Override save to automatically calculate file size and MIME type"""
        if self.file:
            self.file_size = self.file.size
            self.mime_type = self.file.file.content_type
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Document({self.title} for {self.patient.patient_id})"


class HL7Message(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='hl7_messages')
    message_type = models.CharField(max_length=50)
    message_content = models.TextField()
    processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['message_type', 'processed'])
        ]

    def save(self, *args, **kwargs):
        """Automatically process HL7 message content"""
        if not self.processed:
            self.processed = True  # Automatically mark as processed
        super().save(*args, **kwargs)

    def __str__(self):
        return f"HL7Message({self.message_type} for {self.patient.patient_id})"