from rest_framework import viewsets, permissions, status, parsers, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage
from django.db.models import Q
from django.utils.timezone import now
from .models import Patient, MedicalHistory, Document, HL7Message, Notification
from .serializers import (
    PatientSerializer, 
    MedicalHistorySerializer,
    DocumentSerializer,
    HL7MessageSerializer,
    NotificationSerializer
)
from .services import ImageProcessor, FHIRExporter, HL7Processor
from .tasks import process_medical_image, notify_missed_follow_ups, notify_irregular_progress
from users.models import User, Role, AuditLog

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = [
        'user__first_name',
        'user__last_name',
        'patient_id',
        'user__email',
        'user__phone_number'
    ]

    def get_queryset(self):
        """Filter queryset based on user role and search query"""
        user = self.request.user
        queryset = Patient.objects.select_related('user').prefetch_related('documents', 'medicalhistory_set')

        # Filter based on user role
        if user.role == Role.RoleType.PATIENT:
            return queryset.filter(user=user)

        # Handle search query
        search_query = self.request.query_params.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(patient_id__icontains=search_query) |
                Q(user__email__icontains=search_query) |
                Q(user__phone_number__icontains=search_query)
            ).distinct()

        return queryset

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
            if request.user.role != Role.RoleType.DOCTOR and request.user != patient.user:
                return Response(
                    {"detail": "Permission denied"},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        medical_history = MedicalHistory.objects.filter(patient=patient)

        # Add pagination
        page = self.paginate_queryset(medical_history)
        if page is not None:
            serializer = MedicalHistorySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

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

    @action(detail=True, methods=['post'])
    def update_follow_up(self, request, pk=None):
        """Update next follow-up date for a specific patient."""
        patient = self.get_object()
        next_follow_up_date = request.data.get('next_follow_up_date')

        if not next_follow_up_date:
            return Response({"detail": "Next follow-up date is required."}, status=status.HTTP_400_BAD_REQUEST)

        patient.next_follow_up_date = next_follow_up_date
        patient.save()

        return Response({"detail": "Next follow-up date updated successfully."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def notifications(self, request):
        """Retrieve notifications for the current user."""
        notifications = Notification.objects.filter(recipient=request.user)

        # Add pagination
        page = self.paginate_queryset(notifications)
        if page is not None:
            serializer = NotificationSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def trigger_notifications(self, request):
        """Manually trigger missed follow-up and irregular progress notifications."""
        notify_missed_follow_ups.delay()
        notify_irregular_progress.delay()
        return Response({"detail": "Notification tasks triggered."}, status=status.HTTP_200_OK)
