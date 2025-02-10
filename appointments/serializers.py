from rest_framework import serializers
from .models import Appointment
from users.models import User, Role
from django.utils.timezone import now
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
            'is_onsite',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, data):
        """Validate appointment slot availability and role-based restrictions"""
        user = self.context['request'].user
        is_onsite = data.get('is_onsite', False)
        date = data.get('date')
        time_slot = data.get('time_slot')
        doctor = data.get('doctor')
        
        # Ensure onsite appointments can only be booked by receptionists
        if is_onsite and user.role != Role.RECEPTIONIST:
            raise serializers.ValidationError("Only receptionists can book onsite appointments.")
        
        # Ensure patients cannot book appointments as doctors
        if user.role == Role.DOCTOR and data.get('patient').user == user:
            raise serializers.ValidationError("Doctors cannot book appointments for themselves.")
        
        # Prevent booking past dates
        if date < now().date():
            raise serializers.ValidationError("Cannot book appointments in the past.")
        
        # Check for scheduling conflicts only if this is a new appointment
        if self.instance is None:
            existing = Appointment.objects.filter(
                doctor=doctor,
                date=date,
                time_slot=time_slot,
                status=Appointment.Status.SCHEDULED
            )
            if existing.exists():
                raise serializers.ValidationError("This time slot is already booked.")
        
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