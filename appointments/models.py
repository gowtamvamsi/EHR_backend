from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now
from users.models import User
from patients.models import Patient
import uuid

class Appointment(models.Model):
    """Model to manage patient appointments."""
    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", _("Scheduled")
        CONFIRMED = "CONFIRMED", _("Confirmed")
        RESCHEDULED = "RESCHEDULED", _("Rescheduled")
        CHECKED_IN = "CHECKED_IN", _("Checked-In")
        CANCELLED = "CANCELLED", _("Cancelled")
        COMPLETED = "COMPLETED", _("Completed")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="appointments")
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="appointments")
    date = models.DateField()
    time_slot = models.TimeField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED
    )
    reason = models.TextField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    is_onsite = models.BooleanField(default=False)  # NEW FIELD for onsite booking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def cancel(self):
        """Cancel the appointment and log the action."""
        self.status = self.Status.CANCELLED
        self.save()

    def reschedule(self, new_date, new_time_slot):
        """Reschedule the appointment to a new date and time slot."""
        if new_date < now().date():
            raise ValueError("Cannot reschedule to a past date.")
        self.date = new_date
        self.time_slot = new_time_slot
        self.status = self.Status.RESCHEDULED
        self.save()

    def check_in(self):
        """Mark the patient as checked in."""
        if self.status != self.Status.CONFIRMED:
            raise ValueError("Only confirmed appointments can be checked in.")
        self.status = self.Status.CHECKED_IN
        self.save()

    def __str__(self):
        return f"Appointment({self.patient}, {self.date}, {self.time_slot}, {self.status})"
