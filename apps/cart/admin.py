from django.contrib import admin
from .models import Cart, CartItem, OrderDetail, OrderItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('total_price',)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_amount', 'get_items_count', 'last_activity')
    list_filter = ('status', 'created_at', 'last_activity')
    search_fields = ('user__username', 'user__email', 'session_id')
    readonly_fields = ('subtotal', 'tax', 'total_amount', 'created_at', 'updated_at')
    inlines = [CartItemInline]
    
    def get_items_count(self, obj):
        return obj.get_items_count()
    get_items_count.short_description = 'Items Count'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart', 'service', 'quantity', 'unit_price', 'total_price', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('service__name', 'cart__user__username')
    readonly_fields = ('total_price', 'created_at', 'updated_at')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('total_price',)


@admin.register(OrderDetail)
class OrderDetailAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer_name', 'status', 'payment_status', 'total_amount', 'order_date')
    list_filter = ('status', 'payment_status', 'order_date')
    search_fields = ('order_number', 'customer_name', 'customer_email', 'user__username')
    readonly_fields = ('order_number', 'subtotal', 'tax', 'total_amount', 'order_date', 'created_at', 'updated_at')
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'cart', 'status', 'payment_status')
        }),
        ('Customer Information', {
            'fields': ('customer_name', 'customer_email', 'customer_phone')
        }),
        ('Order Totals', {
            'fields': ('subtotal', 'tax', 'total_amount')
        }),
        ('Dates', {
            'fields': ('order_date', 'checkout_date', 'fulfillment_date')
        }),
        ('Additional Information', {
            'fields': ('special_instructions', 'admin_notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'service', 'quantity', 'unit_price', 'total_price', 'status')
    list_filter = ('status', 'created_at')
    search_fields = ('service__name', 'order__order_number', 'order__customer_name')
    readonly_fields = ('total_price', 'created_at', 'updated_at')
