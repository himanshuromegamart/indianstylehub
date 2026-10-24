from django.contrib import admin
from django.utils.html import format_html

# Register your models here.
from .models import *
admin.site.register((
    Supercategory,
    Maincategory,
    Category,
    Subcategory,
    Brand,
    Color,
    Size,
    Buyer,
    Order,
    Address,
    Wishlist,
    Slider,
    Gallery,
    Blog,
))


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'seller_price', 'display_profit', 'quantity', 'category', 'brand')
    list_filter = ('supercategory', 'maincategory', 'category', 'brand')
    search_fields = ('name', 'sku', 'tags', 'meta_title')

    def display_profit(self, obj):
        if obj.seller_price:
            return f"₹{obj.profit} ({obj.profit_percentage}%)"
        return "-"
    display_profit.short_description = "Profit"


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ('id', 'device_type', 'user', 'token_snippet', 'created_at', 'updated_at')
    search_fields = ('token', 'user__username')
    list_filter = ('device_type', 'created_at')

    def token_snippet(self, obj):
        return f"{obj.token[:30]}..." if obj.token else ""


@admin.register(PushNotification)
class PushNotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'total_sent', 'url', 'created_at')
    search_fields = ('title', 'body', 'url')
    list_filter = ('created_at',)


@admin.register(PopularLink)
class PopularLinkAdmin(admin.ModelAdmin):
    list_display = ('title', 'state', 'show_on_home', 'category', 'subcategory', 'maincategory', 'supercategory', 'is_active', 'order')
    list_filter = ('is_active', 'show_on_home', 'state', 'supercategory', 'maincategory', 'category')
    search_fields = ('title', 'url', 'state')
    list_editable = ('is_active', 'show_on_home', 'order')
    list_per_page = 50





@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_number', 'buyer_info', 'amount_inr', 'status_badge', 'payment_method', 'razorpay_payment_id', 'razorpay_order_id', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('order_number', 'razorpay_order_id', 'razorpay_payment_id', 'buyer__name', 'buyer__email', 'buyer__phone', 'error_reason', 'error_description')
    readonly_fields = ('id', 'order_number', 'buyer', 'amount', 'currency', 'status', 'payment_method', 'razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature', 'error_code', 'error_description', 'error_source', 'error_step', 'error_reason', 'notes', 'created_at', 'updated_at')
    list_per_page = 30

    def buyer_info(self, obj):
        if obj.buyer:
            return f"{obj.buyer.name} ({obj.buyer.phone})"
        return "-"
    buyer_info.short_description = "Customer"

    def amount_inr(self, obj):
        return f"₹{obj.amount:.2f}"
    amount_inr.short_description = "Amount"

    def status_badge(self, obj):
        colors = {
            'SUCCESS': '#28a745',
            'FAILED': '#dc3545',
            'CANCELLED': '#6c757d',
            'PENDING': '#ffc107',
            'REFUNDED': '#17a2b8',
        }
        text_colors = {'PENDING': '#000'}
        bg = colors.get(obj.status, '#6c757d')
        fg = text_colors.get(obj.status, '#fff')
        return format_html(
            '<span style="background-color: {}; color: {}; font-weight: bold; padding: 3px 8px; border-radius: 4px; font-size: 11px;">{}</span>',
            bg, fg, obj.status
        )
    status_badge.short_description = "Status"
