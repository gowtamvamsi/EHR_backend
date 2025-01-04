from rest_framework import serializers
from .models import Appointment
from users.models import User
from patients.models import Patient

class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = [
            'id',
            'patient',
            'doctor',
            'date',
            'time_slot',
            'status',
            'reason',
            'notes',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, data):
        """Validate appointment slot availability"""
        if self.instance is None:  # Only check for new appointments
            existing = Appointment.objects.filter(
                doctor=data['doctor'],
                date=data['date'],
                time_slot=data['time_slot'],
                status=Appointment.Status.SCHEDULED
            )
            if existing.exists():
                raise serializers.ValidationError(
                    "This time slot is already booked"
                )
        return data

class ScheduleSerializer(serializers.ModelSerializer):
    """Serializer for doctor's schedule view"""
    class Meta:
        model = Appointment
        fields = [
            'id',
            'date',
            'time_slot',
            'status',
            'patient'
        ]