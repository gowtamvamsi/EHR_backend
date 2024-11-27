from rest_framework import serializers
from .models import Patient, MedicalHistory, Document, HL7Message

class PatientSerializer(serializers.ModelSerializer):
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
            'fhir_id',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['fhir_id', 'created_at', 'updated_at']

class MedicalHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalHistory
        fields = [
            'id',
            'condition',
            'diagnosis_date',
            'notes',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            'id',
            'title',
            'file',
            'document_type',
            'mime_type',
            'file_size',
            'metadata',
            'is_compressed',
            'uploaded_at'
        ]
        read_only_fields = [
            'file_size',
            'is_compressed',
            'uploaded_at'
        ]

    def validate_file(self, value):
        """Validate file size and type"""
        if value.size > 10 * 1024 * 1024:  # 10MB limit
            raise serializers.ValidationError(
                "File size cannot exceed 10MB"
            )
        return value

class HL7MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = HL7Message
        fields = [
            'id',
            'message_type',
            'message_content',
            'processed',
            'created_at'
        ]
        read_only_fields = ['processed', 'created_at']