from rest_framework import serializers
from .models import Patient, MedicalHistory, Document, HL7Message, Notification

class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model."""
    class Meta:
        model = Notification
        fields = [
            'id',
            'recipient',
            'message',
            'notification_type',
            'sent_at',
            'is_sent',
            'medium'
        ]
        read_only_fields = ['sent_at', 'is_sent']  # Mark sent_at and is_sent as read-only


class PatientSerializer(serializers.ModelSerializer):
    """Serializer for Patient model."""
    documents = serializers.StringRelatedField(many=True, read_only=True)
    hl7_messages = serializers.StringRelatedField(many=True, read_only=True)
    next_follow_up_date = serializers.DateField(required=False, allow_null=True)  # NEW FIELD ADDED

    class Meta:
        model = Patient
        fields = [
            'id',
            'user',
            'patient_id',
            'date_of_birth',
            'blood_group',
            'emergency_contact',
            'address',
            'next_follow_up_date',  # NEW FIELD ADDED
            'fhir_id',
            'created_at',
            'updated_at',
            'documents',
            'hl7_messages'
        ]
        read_only_fields = ['fhir_id', 'created_at', 'updated_at']


class MedicalHistorySerializer(serializers.ModelSerializer):
    """Serializer for MedicalHistory model."""
    next_follow_up_date = serializers.DateField(required=False, allow_null=True)  # NEW FIELD ADDED

    class Meta:
        model = MedicalHistory
        fields = [
            'id',
            'patient',
            'condition',
            'diagnosis_date',
            'next_follow_up_date',  # NEW FIELD ADDED
            'notes',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for Document model."""
    class Meta:
        model = Document
        fields = [
            'id',
            'patient',
            'title',
            'file',
            'document_type',
            'mime_type',
            'file_size',
            'metadata',
            'is_compressed',
            'uploaded_at',
            'uploaded_by'
        ]
        read_only_fields = [
            'file_size',
            'is_compressed',
            'uploaded_at',
            'uploaded_by'
        ]

    def validate_file(self, value):
        """Validate file size and MIME type."""
        if value.size > 10 * 1024 * 1024:  # 10MB limit
            raise serializers.ValidationError("File size cannot exceed 10MB.")
        allowed_mime_types = ['application/pdf', 'image/jpeg', 'image/png', 'application/dicom']
        if value.content_type not in allowed_mime_types:
            raise serializers.ValidationError("Unsupported file type.")
        return value


class HL7MessageSerializer(serializers.ModelSerializer):
    """Serializer for HL7Message model."""
    class Meta:
        model = HL7Message
        fields = [
            'id',
            'patient',
            'message_type',
            'message_content',
            'processed',
            'created_at'
        ]
        read_only_fields = ['processed', 'created_at']
