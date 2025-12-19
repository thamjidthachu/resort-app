from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from utils.choices import BookingStatusChoices, PaymentMethodChoices, PaymentStatusChoices, CartStatusChoices

from .models import Cart, CartItem, OrderDetail, OrderItem
from .serializers import (
    CartSerializer, CartItemSerializer, AddToCartSerializer,
    UpdateCartItemSerializer, OrderDetailSerializer, CheckoutSerializer
)
from apps.service.models import Service
from .models import CartItem  # Ensure CartItem is imported before use
from .serializers import CartItemSerializer  # Import serializer before use
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated

class CartItemViewSet(mixins.UpdateModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only allow access to user's own cart items in open carts
        return CartItem.objects.filter(cart__user=self.request.user, cart__status='open', is_active=True)



class CartDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a specific cart"""
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user, is_active=True)


class ActiveCartView(APIView):
    """Get user's active cart or create one if none exists"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            cart = Cart.objects.get(user=request.user, status=CartStatusChoices.OPEN, is_active=True)
        except Cart.DoesNotExist:
            cart = Cart.objects.create(user=request.user, status=CartStatusChoices.OPEN)

        serializer = CartSerializer(cart)
        return Response(serializer.data)


class AddToCartView(APIView):
    """Add an item to the user's active cart"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)
        if serializer.is_valid():
            # Get or create active cart
            cart, created = Cart.objects.get_or_create(
                user=request.user,
                status=CartStatusChoices.OPEN,
                is_active=True,
                defaults={'user': request.user}
            )

            # Get the service
            service = get_object_or_404(Service, id=serializer.validated_data['service_id'], is_active=True)

            # Check if item already exists in cart
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                service=service,
                booking_date=serializer.validated_data.get('booking_date'),
                booking_time=serializer.validated_data.get('booking_time'),
                defaults={
                    'quantity': serializer.validated_data['quantity'],
                    'unit_price': service.price,
                    'special_requests': serializer.validated_data.get('special_requests', '')
                }
            )

            if not created:
                # Update quantity if item already exists
                cart_item.quantity += serializer.validated_data['quantity']
                cart_item.save()

            # Update cart totals
            cart.calculate_totals()
            cart.save()

            cart_serializer = CartSerializer(cart)
            return Response(
                {"message": "Item added to cart!!", "data": cart_serializer.data},
                status=status.HTTP_201_CREATED
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdateCartItemView(APIView):
    """Update a cart item"""
    permission_classes = [IsAuthenticated]

    def put(self, request, item_id):
        return self._update(request, item_id)

    def patch(self, request, item_id):
        return self._update(request, item_id)

    def _update(self, request, item_id):
        cart_item = get_object_or_404(
            CartItem,
            id=item_id,
            cart__user=request.user,
            cart__status=CartStatusChoices.OPEN,
            is_active=True
        )

        serializer = UpdateCartItemSerializer(cart_item, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()

            # Update cart totals
            cart_item.cart.calculate_totals()
            cart_item.cart.save()

            return Response(CartItemSerializer(cart_item).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CartItemRemoveView(APIView):
    """Remove an item from cart"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, item_id):
        cart_item = get_object_or_404(
            CartItem,
            id=item_id,
            cart__user=request.user,
            cart__status=CartStatusChoices.OPEN,
            is_active=True
        )

        cart = cart_item.cart
        cart_item.delete()

        # Update cart totals
        cart.calculate_totals()
        cart.save()

        return Response({'message': 'Item removed from cart'}, status=status.HTTP_204_NO_CONTENT)


class ClearCartView(APIView):
    """Clear all items from user's active cart"""
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        try:
            cart = Cart.objects.get(user=request.user, status='open', is_active=True)
            cart.cart_items.filter(is_active=True).delete()
            # Update cart totals
            cart.calculate_totals()
            cart.save()
            return Response({'message': 'Cart cleared'}, status=status.HTTP_200_OK)
        except Cart.DoesNotExist:
            return Response({'error': 'No active cart found'}, status=status.HTTP_404_NOT_FOUND)


class CheckoutCartView(APIView):
    """Checkout cart and create order"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            cart = Cart.objects.get(user=request.user, status='open', is_active=True)
        except Cart.DoesNotExist:
            return Response({'error': 'No active cart found'}, status=status.HTTP_404_NOT_FOUND)

        if cart.is_empty():
            return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = CheckoutSerializer(data=request.data)
        if serializer.is_valid():
            # Create order
            order = OrderDetail.objects.create(
                user=request.user,
                cart=cart,
                customer_name=serializer.validated_data['customer_name'],
                customer_email=serializer.validated_data['customer_email'],
                customer_phone=serializer.validated_data['customer_phone'],
                special_instructions=serializer.validated_data.get('special_instructions', ''),
                subtotal=cart.subtotal,
                tax=cart.tax,
                total_amount=cart.total_amount,
                checkout_date=timezone.now()
            )

            # Create order items from cart items
            cart_items = cart.cart_items.filter(is_active=True)
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    service=cart_item.service,
                    quantity=cart_item.quantity,
                    unit_price=cart_item.unit_price,
                    total_price=cart_item.total_price
                )

            # --- Create or reuse Booking and Payment records ---
            from apps.bookings.models import Booking, Payment
            # Try to find an existing booking for this user/cart/session that is not paid/cancelled
            booking = Booking.objects.filter(
                user=request.user,
                status__in=['pending', 'confirmed', 'in_progress'],
                payment_status__in=['unpaid', 'partial']
            ).order_by('-created_at').first()

            if booking:
                # Update booking details
                booking.order = order
                booking.booking_date = timezone.now().date()
                booking.booking_time = timezone.now().time()
                booking.number_of_guests = cart.get_items_count()
                booking.subtotal = cart.subtotal
                booking.tax = cart.tax
                booking.total_amount = cart.total_amount
                booking.special_requests = serializer.validated_data.get('special_instructions', '')
                booking.save()
            else:
                booking = Booking(
                    user=request.user,
                    order=order,
                    booking_date=timezone.now().date(),
                    booking_time=timezone.now().time(),
                    number_of_guests=cart.get_items_count(),
                    status=BookingStatusChoices.PENDING,
                    payment_status=PaymentStatusChoices.INITIATED,
                    subtotal=cart.subtotal,
                    tax=cart.tax,
                    total_amount=cart.total_amount,
                    special_requests=serializer.validated_data.get('special_instructions', '')
                )
                booking.save()

            booking.calculate_totals()
            booking.save()

            # Try to find an existing pending payment for this booking
            payment = Payment.objects.filter(
                booking=booking,
                payment_status=PaymentStatusChoices.INITIATED,
                payment_method=PaymentMethodChoices.ONLINE
            ).order_by('-payment_date').first()

            if payment:
                payment.amount = cart.total_amount
                payment.notes = 'Stripe payment initiated from cart checkout.'
                payment.save()
            else:
                payment = Payment.objects.create(
                    booking=booking,
                    amount=cart.total_amount,
                    payment_method=PaymentMethodChoices.ONLINE,
                    payment_status=PaymentStatusChoices.INITIATED,
                    notes='Stripe payment initiated from cart checkout.'
                )

            # --- Initiate Stripe checkout ---
            from apps.bookings.stripe_utils import create_checkout_session
            stripe_result = create_checkout_session(booking)
            if stripe_result['success']:
                # Save the Stripe session_id to the Payment record (dedicated field)
                payment.session_id = stripe_result['session_id']
                payment.save(update_fields=['session_id'])
                return Response({
                    'order': OrderDetailSerializer(order).data,
                    'booking_number': booking.booking_number,
                    'payment_id': payment.id,
                    'stripe_checkout_url': stripe_result['checkout_url'],
                    'stripe_session_id': stripe_result['session_id'],
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({'error': 'Failed to create Stripe checkout session', 'details': stripe_result.get('error')}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderListView(generics.ListAPIView):
    """List user's orders"""
    serializer_class = OrderDetailSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return OrderDetail.objects.filter(user=self.request.user)


class OrderDetailView(generics.RetrieveAPIView):
    """Retrieve a specific order"""
    serializer_class = OrderDetailSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return OrderDetail.objects.filter(user=self.request.user)


class CompletePaymentView(APIView):
    """Mark order as completed and close cart after successful payment"""
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        order = get_object_or_404(OrderDetail, id=order_id, user=request.user)

        if order.payment_status == PaymentStatusChoices.COMPLETED:
            return Response({'error': 'Order already paid'}, status=status.HTTP_400_BAD_REQUEST)

        # Mark order as completed
        order.mark_as_completed()
        order.fulfillment_date = timezone.now()
        order.save()

        return Response({
            'message': 'Payment completed successfully',
            'order_number': order.order_number
        }, status=status.HTTP_200_OK)
