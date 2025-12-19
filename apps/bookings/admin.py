from django.contrib import admin
from django.utils.html import format_html

from .models import Booking, Payment
from .forms import BookingAdminForm, PaymentInlineForm

class PaymentInline(admin.TabularInline):
    model = Payment
    form = PaymentInlineForm
    extra = 0
    fields = ['amount', 'payment_method', 'payment_status', 'transaction_id', 'payment_date', 'notes']
    readonly_fields = ['payment_date']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    form = BookingAdminForm
    inlines = [PaymentInline]
    
    list_display = [
        'booking_number', 'booking_date', 'number_of_guests', 'status_badge', 'payment_status_badge', 
        'total_amount', 'created_at'
    ]
    
    list_filter = ['status', 'payment_status', 'booking_date', 'created_at']
    
    search_fields = [
        'booking_number', 'user__email', 'user__username'
    ]
    
    readonly_fields = [
        'booking_number', 'subtotal', 'tax', 'total_amount', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Booking Information', {
            'fields': ('booking_number', 'user', 'order', 'status', 'payment_status')
        }),
        ('Reservation Details', {
            'fields': ('booking_date', 'booking_time', 'number_of_guests', 'special_requests', 'subtotal', 'tax', 'total_amount')
        }),
        ('Admin', {
            'fields': ('admin_notes', 'is_active', 'is_deleted'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    date_hierarchy = 'booking_date'
    
    def status_badge(self, obj):
        """Display status with color coding"""
        colors = {
            'pending': '#FFA500',      # Orange
            'confirmed': '#4CAF50',    # Green
            'in_progress': '#2196F3',  # Blue
            'completed': '#9E9E9E',    # Grey
            'cancelled': '#F44336',    # Red
        }
        color = colors.get(obj.status, '#000000')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def payment_status_badge(self, obj):
        """Display payment status with color coding"""
        colors = {
            'unpaid': '#F44336',    # Red
            'partial': '#FFA500',   # Orange
            'paid': '#4CAF50',      # Green
            'refunded': '#9E9E9E',  # Grey
        }
        color = colors.get(obj.payment_status, '#000000')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_payment_status_display()
        )
    payment_status_badge.short_description = 'Payment Status'
    
    def save_model(self, request, obj, form, change):
        """Recalculate totals before saving"""
        super().save_model(request, obj, form, change)
        obj.calculate_totals()
        obj.save()


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'booking', 'amount', 'session_id', 'payment_method', 'payment_status_badge', 'transaction_id', 'payment_date'
    ]
    
    list_filter = ['payment_status', 'payment_method', 'payment_date']
    
    search_fields = [
        'booking__booking_number', 'transaction_id', 'booking__user__email', 'session_id'
    ]
    
    readonly_fields = ['payment_date']
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('booking', 'amount', 'session_id', 'payment_method', 'payment_status')
        }),
        ('Transaction Details', {
            'fields': ('transaction_id', 'payment_date', 'notes')
        }),
    )
    
    def payment_status_badge(self, obj):
        """Display payment status with color coding"""
        colors = {
            'pending': '#FFA500',    # Orange
            'completed': '#4CAF50',  # Green
            'failed': '#F44336',     # Red
            'refunded': '#9E9E9E',   # Grey
        }
        color = colors.get(obj.payment_status, '#000000')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_payment_status_display()
        )
    payment_status_badge.short_description = 'Status'
