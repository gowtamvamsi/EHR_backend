from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from datetime import datetime, timedelta
from .models import Appointment
from .serializers import AppointmentSerializer, ScheduleSerializer

class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Check for conflicts
            date = serializer.validated_data['date']
            time_slot = serializer.validated_data['time_slot']
            doctor = serializer.validated_data['doctor']
            
            conflicts = Appointment.objects.filter(
                doctor=doctor,
                date=date,
                time_slot=time_slot,
                status=Appointment.Status.SCHEDULED
            )
            
            if conflicts.exists():
                return Response(
                    {'detail': 'Time slot not available'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            appointment = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['put'])
    def status(self, request, pk=None):
        appointment = self.get_object()
        new_status = request.data.get('status')
        if new_status not in dict(Appointment.Status.choices):
            return Response(
                {'detail': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        appointment.status = new_status
        appointment.save()
        return Response(self.get_serializer(appointment).data)

    @action(detail=False, methods=['get'])
    def doctor_schedule(self, request):
        doctor_id = request.query_params.get('doctor_id')
        start_date = request.query_params.get('start_date', datetime.now().date())
        end_date = request.query_params.get(
            'end_date', 
            datetime.now().date() + timedelta(days=7)
        )
        
        appointments = Appointment.objects.filter(
            doctor_id=doctor_id,
            date__range=[start_date, end_date]
        )
        
        serializer = ScheduleSerializer(appointments, many=True)
        return Response(serializer.data)