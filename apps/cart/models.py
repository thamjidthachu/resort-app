from django.db import models
from decimal import Decimal
from django.contrib.auth import get_user_model
from apps.service.models import Service
from utils.abstract_models import ActiveModel, TimeStampedModel
from utils import CartStatusChoices
from utils.choices import OrderStatusChoices, PaymentStatusChoices

User = get_user_model()


class Cart(TimeStampedModel, ActiveModel):
    """Shopping cart model for users to add services before booking"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts')
    session_id = models.CharField(max_length=100, null=True, blank=True, help_text="For guest users")
    status = models.CharField(max_length=24, choices=CartStatusChoices.choices, default=CartStatusChoices.OPEN)

    # Cart totals
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Cart metadata
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Cart expiration time")
    last_activity = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['session_id', 'status']),
            models.Index(fields=['-last_activity']),
        ]
    
    def __str__(self):
        user_identifier = self.user.username if self.user else f"Guest-{self.session_id}"
        return f"Cart #{self.id} - {user_identifier} ({self.status})"
    
    def calculate_totals(self):
        """Calculate cart totals from cart items"""
        cart_items = self.cart_items.filter(is_active=True)
        self.subtotal = sum(item.total_price for item in cart_items)
        self.tax = self.subtotal * Decimal('0.05')  # 5% tax
        self.total_amount = self.subtotal + self.tax
    
    def get_items_count(self):
        """Get total number of items in cart"""
        return self.cart_items.filter(is_active=True).aggregate(total=models.Sum('quantity'))['total'] or 0
    
    def close_cart(self):
        """Close cart after successful payment"""
        self.status = CartStatusChoices.CLOSED
        self.save()
    
    def is_empty(self):
        """Check if cart is empty"""
        return not self.cart_items.filter(is_active=True).exists()


class CartItem(TimeStampedModel, ActiveModel):
    """Individual items in a shopping cart"""
    
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='cart_items')
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Additional options for the service
    booking_date = models.DateField(null=True, blank=True)
    booking_time = models.TimeField(null=True, blank=True)
    special_requests = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['created_at']
        unique_together = ['cart', 'service', 'booking_date', 'booking_time']
    
    def __str__(self):
        return f"{self.service.name} x{self.quantity} - ${self.total_price}"
    
    def save(self, *args, **kwargs):
        # Set unit price from service if not provided
        if not self.unit_price:
            self.unit_price = self.service.price
        
        # Calculate total price
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)
        
        # Update cart totals
        if self.cart_id:
            self.cart.calculate_totals()
            self.cart.save()


class OrderDetail(TimeStampedModel):
    """Order details created when user checks out the cart"""
    
    # Order Information
    order_number = models.CharField(max_length=50, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    cart = models.ForeignKey(Cart, on_delete=models.SET_NULL, null=True, related_name='orders')
    
    # Customer Information (copied user at checkout)
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    
    # Order Status
    status = models.CharField(max_length=24, choices=OrderStatusChoices.choices, default=OrderStatusChoices.PENDING)
    payment_status = models.CharField(max_length=24, choices=PaymentStatusChoices.choices, default=PaymentStatusChoices.INITIATED)

    # Order Totals (snapshot from cart at checkout)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Order Dates
    order_date = models.DateTimeField(auto_now_add=True)
    checkout_date = models.DateTimeField()
    fulfillment_date = models.DateTimeField(null=True, blank=True)
    
    # Additional Information
    special_instructions = models.TextField(null=True, blank=True)
    admin_notes = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['-order_date']
        indexes = [
            models.Index(fields=['-order_date']),
            models.Index(fields=['order_number']),
            models.Index(fields=['user']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_status']),
        ]
    
    def __str__(self):
        return f"Order #{self.order_number} - {self.customer_name}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate unique order number
            import uuid
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d')
            unique_id = str(uuid.uuid4())[:8].upper()
            self.order_number = f"ORD-{timestamp}-{unique_id}"
        
        super().save(*args, **kwargs)
    
    def mark_as_completed(self):
        """Mark order as completed and close associated cart"""
        self.status = 'completed'
        self.payment_status = 'paid'
        if self.cart:
            self.cart.close_cart()
        self.save()


class OrderItem(TimeStampedModel):
    """Individual items in an order (copied from cart items at checkout)"""
    
    order = models.ForeignKey(OrderDetail, on_delete=models.CASCADE, related_name='order_items')
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    
    # Item details (snapshot from cart item)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Item status
    status = models.CharField(max_length=20, default='pending')
    
    class Meta:
        ordering = ['id']
    
    def __str__(self):
        return f"{self.service.name} x {self.quantity} - ${self.total_price}"
