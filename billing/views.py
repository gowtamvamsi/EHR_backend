from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Invoice, Payment
from .serializers import InvoiceSerializer, PaymentSerializer

class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Calculate total amount with tax
            amount = serializer.validated_data['amount']
            tax = amount * 0.18  # 18% GST
            total_amount = amount + tax
            
            invoice = serializer.save(
                tax=tax,
                total_amount=total_amount
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def payments(self, request, pk=None):
        invoice = self.get_object()
        payments = Payment.objects.filter(invoice=invoice)
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            payment = serializer.save()
            
            # Update invoice status if payment successful
            invoice = payment.invoice
            if payment.status == 'SUCCESS':
                total_paid = Payment.objects.filter(
                    invoice=invoice,
                    status='SUCCESS'
                ).sum('amount')
                
                if total_paid >= invoice.total_amount:
                    invoice.status = Invoice.Status.PAID
                    invoice.save()
                    
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)