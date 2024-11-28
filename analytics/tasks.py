from celery import shared_task
from django.db.models import Count, Avg
from django.utils import timezone
from datetime import timedelta
from patients.models import Patient
from appointments.models import Appointment
from billing.models import Invoice

@shared_task
def generate_daily_analytics():
    """Generate daily analytics report"""
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    
    analytics = {
        'new_patients': Patient.objects.filter(created_at__date=yesterday).count(),
        'appointments': Appointment.objects.filter(date=yesterday).count(),
        'revenue': Invoice.objects.filter(
            created_at__date=yesterday,
            status=Invoice.Status.PAID
        ).aggregate(total=Sum('total_amount'))['total'] or 0,
    }
    
    return analytics

@shared_task
def generate_monthly_report():
    """Generate comprehensive monthly analytics report"""
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    report = {
        'patient_demographics': Patient.objects.filter(
            created_at__range=[start_date, end_date]
        ).aggregate(
            total=Count('id'),
            avg_age=Avg('date_of_birth')
        ),
        'appointment_stats': Appointment.objects.filter(
            date__range=[start_date, end_date]
        ).values('status').annotate(count=Count('id')),
        'financial_summary': Invoice.objects.filter(
            created_at__range=[start_date, end_date]
        ).aggregate(
            total_revenue=Sum('total_amount'),
            paid_amount=Sum('total_amount', filter=Q(status=Invoice.Status.PAID)),
            pending_amount=Sum('total_amount', filter=Q(status=Invoice.Status.PENDING))
        )
    }
    
    return report