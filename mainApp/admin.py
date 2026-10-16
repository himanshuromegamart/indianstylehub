from django.contrib import admin

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
    Product,
    Buyer,
    Order,
    Address,
    Wishlist,
    Slider,
    Gallery,
    Blog,
))


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



