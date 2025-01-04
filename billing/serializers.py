from rest_framework import serializers
from .models import Invoice, Payment

class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = [
            'id',
            'patient',
            'appointment',
            'invoice_number',
            'amount',
            'tax',
            'total_amount',
            'status',
            'due_date',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'invoice_number',
            'tax',
            'total_amount',
            'created_at',
            'updated_at'
        ]

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id',
            'invoice',
            'amount',
            'payment_date',
            'payment_method',
            'transaction_id',
            'status',
            'metadata'
        ]
        read_only_fields = ['payment_date']