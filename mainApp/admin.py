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
    ))