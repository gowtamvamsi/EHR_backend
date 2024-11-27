from rest_framework import viewsets, permissions, status, parsers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage
from .models import Patient, MedicalHistory, Document, HL7Message
from .serializers import (
    PatientSerializer, 
    MedicalHistorySerializer,
    DocumentSerializer,
    HL7MessageSerializer
)
from .services import ImageProcessor, FHIRExporter, HL7Processor
from .tasks import process_medical_image
from users.models import User, AuditLog

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter queryset based on user role"""
        user = self.request.user
        if user.role == User.Role.PATIENT:
            return Patient.objects.filter(user=user)
        return Patient.objects.all()

    def perform_create(self, serializer):
        """Create new patient and log action"""
        patient = serializer.save()
        AuditLog.objects.create(
            user=self.request.user,
            action='CREATE',
            resource_type='PATIENT',
            resource_id=str(patient.id),
            ip_address=self.request.META.get('REMOTE_ADDR'),
            details={'patient_id': patient.patient_id}
        )

    def perform_update(self, serializer):
        """Update patient and log action"""
        patient = serializer.save()
        AuditLog.objects.create(
            user=self.request.user,
            action='UPDATE',
            resource_type='PATIENT',
            resource_id=str(patient.id),
            ip_address=self.request.META.get('REMOTE_ADDR'),
            details={'patient_id': patient.patient_id}
        )

    @action(detail=True, methods=['get'])
    def medical_history(self, request, pk=None):
        """Retrieve medical history for a specific patient"""
        patient = self.get_object()
        
        # Check permissions
        if not request.user.has_perm('users.can_view_patient_records'):
            if request.user.role != User.Role.DOCTOR and request.user != patient.user:
                return Response(
                    {"detail": "Permission denied"},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        medical_history = MedicalHistory.objects.filter(patient=patient)
        serializer = MedicalHistorySerializer(medical_history, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def documents(self, request, pk=None):
        """Upload document for a patient"""
        patient = self.get_object()
        
        # Check permissions
        if not request.user.has_perm('users.can_edit_patient_records'):
            if request.user != patient.user:
                return Response(
                    {"detail": "Permission denied"},
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer = DocumentSerializer(data=request.data)
        if serializer.is_valid():
            document = serializer.save(
                patient=patient,
                uploaded_by=request.user
            )
            
            # Process image asynchronously if it's an image
            if document.mime_type.startswith('image/'):
                process_medical_image.delay(document.id)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def fhir(self, request, pk=None):
        """Export patient data in FHIR format"""
        patient = self.get_object()
        
        # Check permissions
        if not request.user.has_perm('users.can_view_patient_records'):
            if request.user != patient.user:
                return Response(
                    {"detail": "Permission denied"},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        fhir_data = FHIRExporter.export_patient_data(patient)
        return Response(fhir_data)

    @action(detail=False, methods=['post'])
    def import_hl7(self, request):
        """Import patient data from HL7 message"""
        if not request.user.has_perm('users.can_edit_patient_records'):
            return Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = HL7MessageSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Parse HL7 message
                parsed_data = HL7Processor.parse_message(
                    serializer.validated_data['message_content']
                )
                
                # Create or update patient based on parsed data
                patient_id = parsed_data['patient_id']
                patient = Patient.objects.filter(patient_id=patient_id).first()
                
                if not patient:
                    # Create new patient if not exists
                    patient = Patient.objects.create(
                        patient_id=patient_id,
                        # Add other fields from parsed data
                    )
                
                # Create HL7 message record
                HL7Message.objects.create(
                    patient=patient,
                    message_type=parsed_data['message_type'],
                    message_content=serializer.validated_data['message_content']
                )
                
                return Response(
                    {"detail": "HL7 message processed successfully"},
                    status=status.HTTP_201_CREATED
                )
            except ValueError as e:
                return Response(
                    {"detail": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)