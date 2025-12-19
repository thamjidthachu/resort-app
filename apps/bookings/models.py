# Create your models here.
from django.db import models
from decimal import Decimal

from apps.authentication.models import User
from apps.cart.models import OrderDetail
from utils import ActiveModel, TimeStampedModel, BookingStatusChoices, PaymentMethodChoices, PaymentStatusChoices


class Booking(TimeStampedModel, ActiveModel):
    """Main booking model for resort service reservations"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings', null=True, blank=True)
    order = models.ForeignKey(OrderDetail, on_delete=models.SET_NULL, null=True, blank=True) 

    # Booking Details
    booking_number = models.CharField(max_length=50, unique=True, editable=False)
    booking_date = models.DateField(help_text="Date of the booking/reservation")
    booking_time = models.TimeField(null=True, blank=True, help_text="Time of the booking (if applicable)")
    number_of_guests = models.PositiveIntegerField(default=1)
    
    # Status and Payment
    status = models.CharField(max_length=24, choices=BookingStatusChoices.choices, default=BookingStatusChoices.PENDING)
    payment_status = models.CharField(max_length=24, choices=PaymentStatusChoices.choices, default=PaymentStatusChoices.INITIATED)
    
    # Pricing
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Additional Information
    special_requests = models.TextField(null=True, blank=True)
    admin_notes = models.TextField(null=True, blank=True, help_text="Internal notes for staff")
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['booking_number']),
            models.Index(fields=['user']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Booking #{self.booking_number} - {self.user.full_name}"
    
    def save(self, *args, **kwargs):
        if not self.booking_number:
            # Generate unique booking number
            import uuid
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d')
            unique_id = str(uuid.uuid4())[:8].upper()
            self.booking_number = f"BK-{timestamp}-{unique_id}"
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if not is_new:
            self.calculate_totals()
            super().save(update_fields=['subtotal', 'tax', 'total_amount'])
    
    def calculate_totals(self):
        """Calculate subtotal, tax, and total from booking services"""
        items = self.order.order_items.all()
        self.subtotal = sum(item.total_price for item in items)
        self.tax = self.subtotal * Decimal('0.05')  # 5% tax
        self.total_amount = self.subtotal + self.tax


class Payment(TimeStampedModel):
    """Payment records for bookings"""
    
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payments')
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=24, choices=PaymentMethodChoices.choices, default=PaymentMethodChoices.ONLINE)
    payment_status = models.CharField(max_length=24, choices=PaymentStatusChoices.choices, default=PaymentStatusChoices.INITIATED)
    
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    session_id = models.CharField(max_length=200, null=True, blank=True, help_text="Stripe session ID for payment tracking")
    payment_date = models.DateTimeField(auto_now_add=True)
    
    notes = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"Payment #{self.id} - {self.booking.booking_number} - ${self.amount}"
