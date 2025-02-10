from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils.timezone import now
from datetime import datetime, timedelta
from .models import Appointment
from .serializers import AppointmentSerializer, ScheduleSerializer
from .tasks import send_appointment_reminders, send_reschedule_notification, send_cancellation_notification
from users.models import User, Role
import logging

logger = logging.getLogger(__name__)

class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """Create a new appointment (Online or Onsite)"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Check for conflicts
            date = serializer.validated_data['date']
            time_slot = serializer.validated_data['time_slot']
            doctor = serializer.validated_data['doctor']
            patient = serializer.validated_data['patient']
            is_onsite = request.data.get('is_onsite', False)

            # Restrict onsite booking to receptionists only
            if is_onsite and request.user.role != Role.RECEPTIONIST:
                return Response(
                    {"detail": "Only receptionists can book onsite appointments."},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Prevent booking past dates
            if date < now().date():
                return Response({"detail": "Cannot book appointments in the past."}, status=status.HTTP_400_BAD_REQUEST)

            # Check for scheduling conflicts
            conflicts = Appointment.objects.filter(
                doctor=doctor, date=date, time_slot=time_slot, status=Appointment.Status.SCHEDULED
            )
            if conflicts.exists():
                return Response({"detail": "Time slot not available."}, status=status.HTTP_400_BAD_REQUEST)

            # Save appointment
            appointment = serializer.save()
            appointment.status = Appointment.Status.CONFIRMED if request.data.get('is_onsite', False) else Appointment.Status.SCHEDULED
            appointment.save()
            logger.info(f"New appointment created: {appointment}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['put'])
    def reschedule(self, request, pk=None):
        """Reschedule an appointment and notify the patient"""
        appointment = self.get_object()
        new_date = request.data.get('date')
        new_time_slot = request.data.get('time_slot')

        if not new_date or not new_time_slot:
            return Response({"detail": "New date and time slot are required."}, status=status.HTTP_400_BAD_REQUEST)

        new_date = datetime.strptime(new_date, '%Y-%m-%d').date()

        # Prevent rescheduling to a past date
        if new_date < now().date():
            return Response({"detail": "Cannot reschedule to a past date."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the new slot is available
        conflicts = Appointment.objects.filter(
            doctor=appointment.doctor, date=new_date, time_slot=new_time_slot, status=Appointment.Status.SCHEDULED
        ).exclude(id=appointment.id)

        if conflicts.exists():
            return Response({"detail": "Time slot not available."}, status=status.HTTP_400_BAD_REQUEST)

        appointment.date = new_date
        appointment.time_slot = new_time_slot
        appointment.status = Appointment.Status.RESCHEDULED
        appointment.save()

        send_reschedule_notification.delay(appointment.id)
        logger.info(f"Appointment {appointment.id} rescheduled to {new_date} at {new_time_slot}")
        return Response(self.get_serializer(appointment).data)

    @action(detail=True, methods=['put'])
    def cancel(self, request, pk=None):
        """Cancel an appointment and notify the patient"""
        appointment = self.get_object()
        appointment.status = Appointment.Status.CANCELLED
        appointment.save()

        send_cancellation_notification.delay(appointment.id)
        logger.info(f"Appointment {appointment.id} cancelled.")
        return Response({"detail": "Appointment cancelled."})

    @action(detail=True, methods=['put'])
    def check_in(self, request, pk=None):
        """Ensure only doctors can check in a patient"""
        if request.user.role != Role.DOCTOR:
            return Response(
                {"detail": "Only doctors can check in patients."},
                status=status.HTTP_403_FORBIDDEN
            )

        appointment = self.get_object()
        if appointment.status != Appointment.Status.CONFIRMED:
            return Response({"detail": "Only confirmed appointments can be checked in."}, status=status.HTTP_400_BAD_REQUEST)
        
        appointment.status = Appointment.Status.CHECKED_IN
        appointment.save()
        
        logger.info(f"Patient checked in for appointment {appointment.id}")
        return Response({"detail": "Patient checked in successfully."})

    @action(detail=False, methods=['get'])
    def doctor_schedule(self, request):
        """Retrieve a doctor's schedule within a date range"""
        doctor_id = request.query_params.get('doctor_id')
        start_date = request.query_params.get('start_date', now().date())
        end_date = request.query_params.get('end_date', now().date() + timedelta(days=7))
        
        appointments = Appointment.objects.filter(doctor_id=doctor_id, date__range=[start_date, end_date])
        serializer = ScheduleSerializer(appointments, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def trigger_reminders(self, request):
        """Manually trigger appointment reminders."""
        send_appointment_reminders.delay()
        return Response({"detail": "Reminder tasks triggered."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def filter_appointments(self, request):
        """Filter appointments based on date range, doctor, patient, and status"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        doctor_id = request.query_params.get('doctor_id')
        patient_id = request.query_params.get('patient_id')
        status_filter = request.query_params.get('status')

        query = Q()
        if start_date and end_date:
            query &= Q(date__range=[start_date, end_date])
        if doctor_id:
            query &= Q(doctor_id=doctor_id)
        if patient_id:
            query &= Q(patient_id=patient_id)
        if status_filter:
            query &= Q(status=status_filter)

        appointments = Appointment.objects.filter(query)
        serializer = self.get_serializer(appointments, many=True)
        return Response(serializer.data)
