from django.urls import path
from .views import (
    BookingCreateView, BookingListView, BookingDetailView,
    BookingUpdateStatusView, BookingCancelView, PaymentCreateView,
    MyBookingsView, CreateCheckoutSessionView, VerifyPaymentView,
    StripeWebhookView, BookingPaymentStatusView
)

app_name = 'bookings'

urlpatterns = [
    # Booking endpoints
    path('create/', BookingCreateView.as_view(), name='booking-create'),
    path('my-bookings/', MyBookingsView.as_view(), name='my-bookings'),
    path('list/', BookingListView.as_view(), name='booking-list'),
    path('<str:booking_number>/details/', BookingDetailView.as_view(), name='booking-detail'),
    path('<str:booking_number>/update-status/', BookingUpdateStatusView.as_view(), name='booking-update-status'),
    path('<str:booking_number>/cancel/', BookingCancelView.as_view(), name='booking-cancel'),
    
    # Payment endpoints
    path('<str:booking_number>/payment/', PaymentCreateView.as_view(), name='payment-create'),
    
    # Stripe payment endpoints
    path('<str:booking_number>/create-checkout-session/', CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
    path('<str:booking_number>/payment-status/', BookingPaymentStatusView.as_view(), name='booking-payment-status'),
    path('verify-payment/', VerifyPaymentView.as_view(), name='verify-payment'),
    path('stripe-webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
]
