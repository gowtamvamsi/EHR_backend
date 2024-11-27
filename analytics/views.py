from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Sum, Avg
from django.db.models.functions import TruncMonth
from patients.models import Patient
from appointments.models import Appointment
from billing.models import Invoice
from datetime import datetime, timedelta

class AnalyticsViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['get'])
    def patient_demographics(self, request):
        # Age distribution
        current_year = datetime.now().year
        age_ranges = {
            '0-18': (0, 18),
            '19-30': (19, 30),
            '31-50': (31, 50),
            '51+': (51, 150)
        }
        
        demographics = {
            'age_distribution': {},
            'gender_distribution': {},
            'blood_groups': {},
            'total_patients': Patient.objects.count()
        }
        
        for range_name, (min_age, max_age) in age_ranges.items():
            min_date = datetime(current_year - max_age, 1, 1)
            max_date = datetime(current_year - min_age, 12, 31)
            count = Patient.objects.filter(
                date_of_birth__range=(min_date, max_date)
            ).count()
            demographics['age_distribution'][range_name] = count
            
        return Response(demographics)

    @action(detail=False, methods=['get'])
    def financial_summary(self, request):
        period = request.query_params.get('period', 'month')
        end_date = datetime.now()
        
        if period == 'month':
            start_date = end_date - timedelta(days=30)
        elif period == 'year':
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=7)
            
        invoices = Invoice.objects.filter(
            created_at__range=(start_date, end_date)
        )
        
        summary = {
            'total_revenue': invoices.aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
            'paid_amount': invoices.filter(status=Invoice.Status.PAID).aggregate(
                Sum('total_amount')
            )['total_amount__sum'] or 0,
            'pending_amount': invoices.filter(status=Invoice.Status.PENDING).aggregate(
                Sum('total_amount')
            )['total_amount__sum'] or 0,
            'invoice_count': invoices.count(),
            'average_invoice_amount': invoices.aggregate(
                Avg('total_amount')
            )['total_amount__avg'] or 0
        }
        
        return Response(summary)

    @action(detail=False, methods=['get'])
    def appointment_statistics(self, request):
        period = request.query_params.get('period', 'month')
        end_date = datetime.now()
        
        if period == 'month':
            start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=7)
            
        appointments = Appointment.objects.filter(
            date__range=(start_date, end_date)
        )
        
        stats = {
            'total_appointments': appointments.count(),
            'status_distribution': appointments.values('status').annotate(
                count=Count('id')
            ),
            'daily_distribution': appointments.values('date').annotate(
                count=Count('id')
            ),
            'doctor_distribution': appointments.values(
                'doctor__first_name',
                'doctor__last_name'
            ).annotate(count=Count('id'))
        }
        
        return Response(stats)