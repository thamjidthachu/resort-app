from rest_framework import serializers
from django.conf import settings

from apps.authentication.serializers import UserSerializer
from apps.cart.serializers import OrderDetailSerializer
from .models import Booking, Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'amount', 'payment_method', 'payment_status', 'transaction_id', 'payment_date', 'notes']
        read_only_fields = ['id', 'payment_date']


class BookingListSerializer(serializers.ModelSerializer):
    """Serializer for listing bookings"""
    
    class Meta:
        model = Booking
        fields = [
            'id', 'booking_number', 'booking_date', 'booking_time',
            'number_of_guests', 'status', 'payment_status', 'total_amount', 'created_at'
        ]
        read_only_fields = ['id', 'booking_number', 'created_at']


class BookingDetailSerializer(serializers.ModelSerializer):
    """Serializer for booking details"""
    payments = PaymentSerializer(many=True, read_only=True)
    checkout_url = serializers.SerializerMethodField()
    order = OrderDetailSerializer(read_only=True)
    
    class Meta:
        model = Booking
        fields = '__all__'
        read_only_fields = ['id', 'booking_number', 'created_at', 'updated_at', 'subtotal', 'tax', 'total_amount']
    
    def get_checkout_url(self, obj):
        """Generate checkout URL for unpaid bookings"""
        request = self.context.get('request')
        if request and obj.payment_status != 'paid' and obj.status != 'cancelled':
            return request.build_absolute_uri(f'/bookings/{obj.booking_number}/create-checkout-session/')
        return None


class BookingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating bookings"""
    
    class Meta:
        model = Booking
        fields = [
            'booking_date', 'booking_time', 'number_of_guests', 'special_requests', 'services'
        ]
    
    def validate(self, attrs):
        # Validate that at least one service is provided
        services = attrs.get('services', [])
        if not services:
            raise serializers.ValidationError({"services": "At least one service must be selected"})
        
        # Validate guest count
        number_of_guests = attrs.get('number_of_guests', 1)
        for service_data in services:
            service = service_data.get('service')
            quantity = service_data.get('quantity', 1)
            
            # Check min/max people constraints
            if service.min_people and quantity < service.min_people:
                raise serializers.ValidationError({
                    "services": f"Service '{service.name}' requires minimum {service.min_people} people"
                })
            
            if service.max_people and quantity > service.max_people:
                raise serializers.ValidationError({
                    "services": f"Service '{service.name}' allows maximum {service.max_people} people"
                })
        
        return attrs
    
    def create(self, validated_data):
        services_data = validated_data.pop('services')
        
        # Get user from request if authenticated
        request = self.context.get('request')
        user = request.user if request and request.user.is_authenticated else None
        
        # Create booking
        booking = Booking.objects.create(user=user, **validated_data)
        
        # Recalculate totals
        booking.calculate_totals()
        booking.save()
        
        # Send confirmation emails asynchronously
        from utils import send_email_message
        
        # Email to customer
        send_email_message.delay(
            subject=f"Booking Confirmation | {booking.booking_number} | Azure Horizon",
            template_name="booking-confirmation.html",
            context={
                "booking": BookingDetailSerializer(booking).data,
                "booking_number": booking.booking_number,
                "guest_name": booking.order.customer_name,
                "booking_date": booking.booking_date.strftime('%B %d, %Y'),
                "booking_time": booking.booking_time.strftime('%I:%M %p') if booking.booking_time else 'N/A',
                "number_of_guests": booking.number_of_guests,
                "total_amount": str(booking.total_amount),
            },
            recipient_list=[booking.guest_email]
        )
        
        # Email to admin
        send_email_message.delay(
            subject=f"New Booking Received | {booking.booking_number} | Azure Horizon",
            template_name="admin-booking-notification.html",
            context={
                "booking": BookingDetailSerializer(booking).data,
                "booking_number": booking.booking_number,
                "guest_name": booking.order.customer_name,
                "guest_email": booking.order.customer_email,
                "guest_phone": booking.order.customer_phone,
                "booking_date": booking.booking_date.strftime('%B %d, %Y'),
                "number_of_guests": booking.number_of_guests,
                "total_amount": str(booking.total_amount),
            },
            recipient_list=[settings.DEFAULT_FROM_EMAIL]
        )
        
        return booking
