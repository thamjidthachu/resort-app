from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse
from rest_framework import status, generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

from utils.choices import BookingStatusChoices, OrderStatusChoices, PaymentStatusChoices


from .models import Booking
from .serializers import (
    BookingListSerializer, BookingDetailSerializer, 
    BookingCreateSerializer, PaymentSerializer
)
from .stripe_utils import (
    create_checkout_session, retrieve_checkout_session,
    verify_webhook_signature, handle_checkout_session_completed
)
import logging

booking_logger = logging.getLogger('system_logs')
payment_logger = logging.getLogger('payment_logs')


class BookingPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class BookingCreateView(generics.CreateAPIView):
    """Create a new booking (public or authenticated)"""
    permission_classes = [AllowAny]
    serializer_class = BookingCreateSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            booking = serializer.save()
            detail_serializer = BookingDetailSerializer(booking)
            booking_logger.info(f"Booking created: booking_number={booking.booking_number}, user={getattr(booking.user, 'id', None)}")
            return Response({
                "message": "Your booking has been created successfully! A confirmation email has been sent.",
                "booking": detail_serializer.data
            }, status=status.HTTP_201_CREATED)
        booking_logger.warning(f"Booking creation failed: errors={serializer.errors}")
        return Response({
            "error": "Something went wrong. Please check your booking details and try again.",
            "details": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class BookingListView(generics.ListAPIView):
    """List all bookings for authenticated user"""
    permission_classes = [IsAuthenticated]
    serializer_class = BookingListSerializer
    pagination_class = BookingPagination
    
    def get_queryset(self):
        user = self.request.user
        # Return bookings for authenticated user
        return Booking.objects.filter(user=user).order_by('-created_at')


class BookingDetailView(generics.RetrieveAPIView):
    """Get booking details by booking number"""
    permission_classes = [AllowAny]
    serializer_class = BookingDetailSerializer
    lookup_field = 'booking_number'
    
    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Booking.objects.filter(user=self.request.user)
        return None


class BookingUpdateStatusView(APIView):
    """Update booking status (admin only)"""
    permission_classes = [IsAuthenticated]
    
    def patch(self, request, booking_number):
        if not request.user.is_staff:
            booking_logger.warning(f"Unauthorized booking status update attempt by user_id={request.user.id}")
            return Response({
                "error": "You don't have permission to update booking status"
            }, status=status.HTTP_403_FORBIDDEN)
        
        booking = get_object_or_404(Booking, booking_number=booking_number)
        new_status = request.data.get('status')
        admin_notes = request.data.get('admin_notes') 

        if new_status and new_status in dict(BookingStatusChoices.choices).keys():
            booking.status = new_status

        if admin_notes:
            booking.admin_notes = admin_notes
            
        booking.save()
        booking_logger.info(f"Booking status updated: booking_number={booking.booking_number}, new_status={booking.status}, admin_id={request.user.id}")
        serializer = BookingDetailSerializer(booking)
        return Response({
            "message": "Booking status updated successfully",
            "booking": serializer.data
        }, status=status.HTTP_200_OK)


class BookingCancelView(APIView):
    """Cancel a booking"""
    permission_classes = [AllowAny]
    
    def post(self, request, booking_number):
        booking = get_object_or_404(Booking, booking_number=booking_number)
        reason = request.data.get('reason')
        if request.user.is_authenticated:
            if booking.user != request.user and not request.user.is_staff:
                booking_logger.warning(f"Unauthorized booking cancel attempt: booking_number={booking.booking_number}, user_id={request.user.id}")
                return Response({"error": "You don't have permission to cancel this booking"}, status=status.HTTP_403_FORBIDDEN)
        else:
            guest_email = request.data.get('email')
            if booking.guest_email != guest_email:
                booking_logger.warning(f"Guest booking cancel failed: booking_number={booking.booking_number}, guest_email={guest_email}")
                return Response({
                    "error": "Invalid email for this booking"
                }, status=status.HTTP_403_FORBIDDEN)
            
        if booking.status in ['completed', 'cancelled']:
            booking_logger.info(f"Cancel attempt on completed/cancelled booking: booking_number={booking.booking_number}, status={booking.status}")
            return Response({
                "error": f"Cannot cancel a booking that is already {booking.status}"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Record cancellation reason into admin_notes for staff visibility
        if reason:
            existing = booking.admin_notes or ""
            note = f"Cancellation reason: {reason}"
            # keep previous admin notes and append the reason
            booking.admin_notes = (existing + '\n' + note).strip()

        booking.status = BookingStatusChoices.CANCELLED
        booking.save()
        booking_logger.info(f"Booking cancelled: booking_number={booking.booking_number}")
        return Response({
            "message": "Booking cancelled successfully",
            "booking_number": booking.booking_number,
            "reason": reason
        }, status=status.HTTP_200_OK)


class PaymentCreateView(generics.CreateAPIView):
    """Create a payment for a booking (admin only)"""
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentSerializer
    
    def create(self, request, booking_number):
        if not request.user.is_staff:
            payment_logger.warning(f"Unauthorized payment creation attempt by user_id={request.user.id}")
            return Response({
                "error": "You don't have permission to create payments"
            }, status=status.HTTP_403_FORBIDDEN)
        
        booking = get_object_or_404(Booking, booking_number=booking_number)
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            payment = serializer.save(booking=booking)
            total_paid = sum(p.amount for p in booking.payments.filter(payment_status=PaymentStatusChoices.COMPLETED))
            if total_paid >= booking.total_amount:
                booking.payment_status = PaymentStatusChoices.COMPLETED
            elif total_paid > 0:
                booking.payment_status = PaymentStatusChoices.FAILED

            booking.save()
            payment_logger.info(f"Payment created: payment_id={payment.id}, booking_number={booking.booking_number}, amount={payment.amount}, user_id={request.user.id}")
            return Response({
                "message": "Payment recorded successfully",
                "payment": PaymentSerializer(payment).data
            }, status=status.HTTP_201_CREATED)
        
        payment_logger.warning(f"Payment creation failed: errors={serializer.errors}")
        return Response({
            "error": "Invalid payment data",
            "details": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class MyBookingsView(generics.ListAPIView):
    """List all bookings for the authenticated user"""
    permission_classes = [IsAuthenticated]
    serializer_class = BookingListSerializer
    pagination_class = BookingPagination
    
    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user).order_by('-created_at')


# ===== Stripe Payment Views =====

class CreateCheckoutSessionView(APIView):
    """Create a Stripe Checkout Session for a booking"""
    permission_classes = [AllowAny]
    
    def post(self, request, booking_number):
        booking = get_object_or_404(Booking, booking_number=booking_number)
        if request.user.is_authenticated:
            if booking.user and booking.user != request.user and not request.user.is_staff:
                payment_logger.warning(f"Unauthorized checkout session attempt: booking_number={booking.booking_number}, user_id={request.user.id}")
                return Response({
                    "error": "You don't have permission to pay for this booking"
                }, status=status.HTTP_403_FORBIDDEN)
        else:
            guest_email = request.data.get('email')
            if booking.guest_email != guest_email:
                payment_logger.warning(f"Guest checkout session failed: booking_number={booking.booking_number}, guest_email={guest_email}")
                return Response({
                    "error": "Invalid email for this booking"
                }, status=status.HTTP_403_FORBIDDEN)

        if booking.payment_status == PaymentStatusChoices.COMPLETED:
            payment_logger.info(f"Checkout session attempt for already paid booking: booking_number={booking.booking_number}")
            return Response({
                "error": "This booking has already been paid"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if booking.status == BookingStatusChoices.CANCELLED:
            payment_logger.info(f"Checkout session attempt for cancelled booking: booking_number={booking.booking_number}")
            return Response({
                "error": "Cannot pay for a cancelled booking"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        result = create_checkout_session(booking)
        if result['success']:
            payment_logger.info(f"Checkout session created: booking_number={booking.booking_number}, session_id={result['session_id']}")
            return Response({
                "message": "Checkout session created successfully",
                "session_id": result['session_id'],
                "checkout_url": result['checkout_url'],
            }, status=status.HTTP_200_OK)
        else:
            payment_logger.error(f"Checkout session creation failed: booking_number={booking.booking_number}, error={result.get('error')}")
            return Response({
                "error": "Failed to create checkout session",
                "details": result.get('error')
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifyPaymentView(APIView):
    """Verify payment status from Stripe"""
    permission_classes = [AllowAny]

    def post(self, request):
        from apps.cart.models import Cart, OrderDetail, OrderItem
        from django.utils import timezone
        session_id = request.data.get('session_id')
        booking_number = request.data.get('booking_number')
        if not session_id:
            payment_logger.warning(f"Verify payment failed: session_id missing")
            return Response({
                "error": "session_id is required"
            }, status=status.HTTP_400_BAD_REQUEST)
        session = retrieve_checkout_session(session_id)
        if not session:
            payment_logger.warning(f"Verify payment failed: invalid session_id={session_id}")
            return Response({
                "error": "Invalid session"
            }, status=status.HTTP_404_NOT_FOUND)
        booking = get_object_or_404(Booking, booking_number=booking_number)
        booking.status = BookingStatusChoices.CONFIRMED
        booking.payment_status = PaymentStatusChoices.COMPLETED
        booking.order.status = OrderStatusChoices.COMPLETED
        booking.save()
        cart = None
        if booking.user:
            cart = Cart.objects.filter(user=booking.user, status='open').order_by('-last_activity').first()
        else:
            cart = Cart.objects.filter(session_id=session_id, status='open').order_by('-last_activity').first()
        if cart:
            cart.close_cart()
        payment_logger.info(f"Payment verified: booking_number={booking.booking_number}, session_id={session_id}, user_id={getattr(booking.user, 'id', None)}")
        return Response({
            "booking_number": booking.booking_number,
            "customer_email": session.customer_email,
            "payment_status": session.payment_status,
            "booking_status": booking.status,
            "booking_payment_status": booking.payment_status,
            "paid_amount": session.amount_total / 100,
            "sub_total": booking.subtotal,
            "tax": booking.tax,
            "total_amount": booking.total_amount,
        }, status=status.HTTP_200_OK)
    
    
@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    """Handle Stripe webhook events"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        payload = request.body
        payment_logger.info(f"Stripe webhook Data: {request.body}")
        payment_logger.info(f"Stripe webhook Headers: {request.headers}")

        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        if not sig_header:
            return HttpResponse("Missing signature", status=400)
        
        # Verify webhook signature
        event = verify_webhook_signature(payload, sig_header)
        
        if not event:
            return HttpResponse("Invalid signature", status=400)
        
        # Handle different event types
        event_type = event['type']
        
        if event_type == 'checkout.session.completed':
            session = event['data']['object']
            
            # Handle successful payment
            success = handle_checkout_session_completed(session)
            
            if success:
                return HttpResponse("Webhook handled successfully", status=200)
            else:
                return HttpResponse("Error processing webhook", status=500)
        
        elif event_type == 'payment_intent.succeeded':
            # Additional handling for payment intent succeeded
            payment_intent = event['data']['object']
            # Add custom logic here if needed
            return HttpResponse("Payment intent succeeded", status=200)
        
        elif event_type == 'payment_intent.payment_failed':
            # Handle payment failure
            payment_intent = event['data']['object']
            # Add custom logic for failed payments
            return HttpResponse("Payment failed", status=200)
        
        # Return success for unhandled event types
        return HttpResponse(f"Unhandled event type: {event_type}", status=200)


class BookingPaymentStatusView(APIView):
    """Get payment status for a booking"""
    permission_classes = [AllowAny]
    
    def get(self, request, booking_number):
        booking = get_object_or_404(Booking, booking_number=booking_number)
        
        # Calculate payment details
        total_paid = sum(
            p.amount for p in booking.payments.filter(payment_status='completed')
        )
        
        remaining = booking.total_amount - total_paid
        
        return Response({
            "booking_number": booking.booking_number,
            "status": booking.status,
            "payment_status": booking.payment_status,
            "total_amount": str(booking.total_amount),
            "total_paid": str(total_paid),
            "remaining": str(remaining),
            "payments": PaymentSerializer(booking.payments.all(), many=True).data
        }, status=status.HTTP_200_OK)