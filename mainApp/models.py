from django.db import models
from tinymce.models import HTMLField
from django.contrib.auth.models import User



class Slider(models.Model):
    id=models.AutoField(primary_key=True)
    link = models.URLField(max_length=1024)
    image = models.URLField(max_length=1024,default='')
    def __str__(self):
        return str(self.id)


class Supercategory(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    image = models.URLField(max_length=1024, default='', null=True, blank=True)
    title = models.CharField(max_length=100, default='', null=True, blank=True)
    description = models.TextField(default='', null=True, blank=True)
    
    def __str__(self):
        return self.name
    

class Maincategory(models.Model):
    id = models.AutoField(primary_key=True)
    supercategory = models.ForeignKey(Supercategory, on_delete=models.SET_NULL, related_name="maincategories", default=None, null=True, blank=True)
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    image = models.URLField(max_length=1024, default='', null=True, blank=True)
    banner1 = models.URLField(max_length=1024,default='')
    banner2 = models.URLField(max_length=1024,default='')
    banner3 = models.URLField(max_length=1024,default='')
    banner4 = models.URLField(max_length=1024,default='')
    title=models.CharField(max_length=100,default='',null=True,blank=True)
    description=models.TextField(default='',null=True,blank=True)
    banner = models.URLField(max_length=1024,default='')

    def __str__(self):
        return self.name

    def get_hierarchy_url(self):
        if self.supercategory:
            return f"/{self.supercategory.slug}/{self.slug}/"
        return f"/{self.slug}/"


class Category(models.Model):
    id = models.AutoField(primary_key=True)
    maincategory = models.ForeignKey(Maincategory, on_delete=models.SET_DEFAULT, default=None, null=True, blank=True)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    image = models.URLField(max_length=1024, default='', null=True, blank=True)
    app_background = models.URLField(max_length=1024, default='', null=True, blank=True)
    specifications = models.JSONField(default=dict)  # Requires Django 3.1+
    title=models.CharField(max_length=100,default='',null=True,blank=True)
    description=models.TextField(default='',null=True,blank=True)
    def __str__(self):
        return self.name
    
    def get_hierarchy_url(self):
        if self.maincategory and self.maincategory.supercategory:
            return f"/{self.maincategory.supercategory.slug}/{self.maincategory.slug}/{self.slug}/"
        elif self.maincategory:
            return f"/{self.maincategory.slug}/{self.slug}/"
        return f"/{self.slug}/"


class Subcategory(models.Model):
    id = models.AutoField(primary_key=True)
    category = models.ForeignKey(Category, on_delete=models.SET_DEFAULT, default=None, null=True, blank=True)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    image = models.URLField(max_length=1024, default='', null=True, blank=True)
    title=models.CharField(max_length=100,default='',null=True,blank=True)
    description=models.TextField(default='',null=True,blank=True)
    def __str__(self):
        return self.name

    def get_hierarchy_url(self):
        if self.category and self.category.maincategory and self.category.maincategory.supercategory:
            return f"/{self.category.maincategory.supercategory.slug}/{self.category.maincategory.slug}/{self.category.slug}/{self.slug}/"
        elif self.category and self.category.maincategory:
            return f"/{self.category.maincategory.slug}/{self.category.slug}/{self.slug}/"
        elif self.category:
            return f"/{self.category.slug}/{self.slug}/"
        return f"/{self.slug}/"


class Brand(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    image = models.URLField(max_length=1024, default='', null=True, blank=True)
    title=models.CharField(max_length=100,default='',null=True,blank=True)
    description=models.TextField(default='',null=True,blank=True)

    def __str__(self):
        return self.name
    

class Color(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200, unique=True)
    
    def __str__(self):
        return self.name
    
class Size(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200, unique=True)
    
    def __str__(self):
        return self.name
    

class Product(models.Model):
    id=models.AutoField(primary_key=True)
    supercategory=models.ForeignKey(Supercategory,on_delete=models.SET_NULL,related_name="supercategory_products",default=None,null=True,blank=True)
    offers=models.ForeignKey(Supercategory,on_delete=models.SET_DEFAULT,related_name="offers",default=None,null=True,blank=True)
    maincategory=models.ForeignKey(Maincategory,on_delete=models.SET_DEFAULT,related_name="maincategory",default=None, null=True, blank=True)
    category=models.ForeignKey(Category,on_delete=models.SET_DEFAULT,related_name="categories",default=None, null=True, blank=True)
    subcategory=models.ForeignKey(Subcategory,on_delete=models.SET_DEFAULT,related_name="subcategories",default=None, null=True, blank=True)
    brand=models.ForeignKey(Brand,on_delete=models.SET_DEFAULT,related_name="brands",default=None, null=True, blank=True)
    image1 = models.URLField(max_length=1024, default='', null=True, blank=True)
    image2= models.URLField(max_length=1024,null=True,blank=True)
    image3= models.URLField(max_length=1024,null=True,blank=True)
    image4= models.URLField(max_length=1024,null=True,blank=True)
    name=models.CharField(max_length=300)
    base_price=models.FloatField(default=0,null=True,blank=True)
    discount=models.FloatField(default=0,null=True,blank=True)
    price=models.FloatField()
    seller_price=models.FloatField(default=0,null=True,blank=True)
    quantity=models.IntegerField(default=1)
    size=models.CharField(max_length=300,null=True,blank=True)
    color=models.CharField(max_length=300,null=True,blank=True)
    specifications = models.JSONField(default=dict)
    rating=models.FloatField(default=0,null=True,blank=True)
    reviews=models.IntegerField(default=0,null=True,blank=True)

    #delhivery details
    weight=models.IntegerField(default=0,null=True,blank=True)
    length=models.FloatField(default=0,null=True,blank=True)
    height=models.FloatField(default=0,null=True,blank=True)
    width=models.FloatField(default=0,null=True,blank=True)
    #discount
    tax=models.FloatField(default=18,null=True,blank=True)

    description=models.TextField(null=True,blank=True)
    faq = models.JSONField(default=dict)
    sku=models.CharField(max_length=200,default='',null=True,blank=True)
    date=models.DateTimeField(auto_now_add=True)

    # SEO & Search Optimization Fields
    tags = models.TextField(default='', null=True, blank=True, help_text="Comma-separated SEO tags/keywords (e.g. party wear, luxury handbag, bridal collection)")
    meta_title = models.CharField(max_length=255, default='', null=True, blank=True, help_text="SEO Meta Title (recommended 50-60 characters)")
    meta_description = models.TextField(default='', null=True, blank=True, help_text="SEO Meta Description (recommended 150-160 characters)")
    meta_keywords = models.TextField(default='', null=True, blank=True, help_text="SEO Meta Keywords (comma separated)")

    @property
    def tags_list(self):
        """Returns clean list of tags for frontend pills and search filters"""
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(',') if t.strip()]

    def get_tags_list(self):
        return self.tags_list

    @property
    def profit(self):
        try:
            p = float(self.price or 0.0)
            sp = float(self.seller_price or 0.0)
            return round(p - sp, 2)
        except (ValueError, TypeError):
            return 0.0

    @property
    def profit_percentage(self):
        try:
            p = float(self.price or 0.0)
            sp = float(self.seller_price or 0.0)
            if sp > 0:
                return round(((p - sp) / sp) * 100, 1)
            return 0.0
        except (ValueError, TypeError):
            return 0.0

    def __str__(self):
        return str(self.name)

    def get_hierarchy_url(self):
        from django.utils.text import slugify
        slug_name = slugify(self.name) if self.name else str(self.id)
        return f"/product-details/{slug_name}/{self.id}/"

    def save(self, *args, **kwargs):
        if not self.supercategory:
            if self.maincategory and self.maincategory.supercategory:
                self.supercategory = self.maincategory.supercategory
            elif self.category and self.category.maincategory and self.category.maincategory.supercategory:
                self.supercategory = self.category.maincategory.supercategory
        super().save(*args, **kwargs)
    


class Blog(models.Model):
    id=models.AutoField(primary_key=True)
    supercategory = models.ForeignKey(Supercategory, on_delete=models.SET_NULL, default=None, null=True, blank=True, related_name="blogs")
    maincategory = models.ForeignKey(Maincategory, on_delete=models.SET_NULL, default=None, null=True, blank=True, related_name="blogs")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, default=None, null=True, blank=True, related_name="blogs")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, default=None, null=True, blank=True, related_name="blogs")
    image = models.URLField(max_length=1024, default='', null=True, blank=True)
    title=models.CharField(max_length=200)
    slug=models.CharField(max_length=200)
    description=models.TextField(default='')
    meta_description=models.TextField(default='',null=True,blank=True)
    views=models.IntegerField(default=0)
    date=models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.title
    

#User Models
class Buyer(models.Model):
    id=models.AutoField(primary_key=True)
    name=models.CharField(max_length=150,default='')
    phone=models.CharField(max_length=20,default='')
    email=models.EmailField(default='', blank=True, null=True)
    password=models.CharField(max_length=50,default='', blank=True, null=True)
    verification=models.CharField(max_length=30,default="pending")
    date=models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return str(self.name)
    


class Address(models.Model):
    id=models.AutoField(primary_key=True)
    buyer=models.ForeignKey(Buyer,on_delete=models.CASCADE)
    addressType= models.CharField(max_length=100,default='Home')
    alternatePhone= models.CharField(max_length=20,default='',blank=True,null=True)
    address= models.TextField(default='')
    landmark= models.CharField(max_length=255,default='',blank=True,null=True)
    city= models.CharField(max_length=150,default='',blank=True,null=True)
    state= models.CharField(max_length=150,default='',blank=True,null=True)
    pin= models.CharField(max_length=20,default='',blank=True,null=True)


class Wishlist(models.Model):
    id=models.AutoField(primary_key=True)
    buyer=models.ForeignKey(Buyer,on_delete=models.CASCADE)
    product=models.ForeignKey(Product,on_delete=models.CASCADE)


class Order(models.Model):
    id = models.AutoField(primary_key=True)
    buyer = models.ForeignKey(Buyer, on_delete=models.SET_DEFAULT, default=None, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.SET_DEFAULT,default=None, null=True, blank=True)
    address = models.ForeignKey(Address, on_delete=models.SET_DEFAULT,default=None, null=True, blank=True)
    quantity = models.IntegerField()
    totalPrice = models.FloatField()
    shippingPrice = models.FloatField()
    finalPrice = models.FloatField()
    transactionId = models.CharField(max_length=100, default='')
    orderDate = models.CharField(max_length=100, default='')
    orderStatus = models.CharField(max_length=100, default="pending")
    cancelled_by = models.CharField(max_length=100, default="")
    waywill = models.CharField(max_length=100, default="")
    payment_status = models.CharField(max_length=50, default="Pending")
    razorpay_order_id = models.CharField(max_length=100, default="", blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, default="", blank=True, null=True)
    razorpay_signature = models.TextField(default="", blank=True, null=True)

    def __str__(self):
        return f"Order {self.id} - {self.buyer}"

class Payment(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
        ('REFUNDED', 'Refunded'),
    )
    id = models.AutoField(primary_key=True)
    buyer = models.ForeignKey(Buyer, on_delete=models.SET_NULL, null=True, blank=True)
    order_number = models.CharField(max_length=100, db_index=True)
    razorpay_order_id = models.CharField(max_length=100, blank=True, default='', db_index=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, default='', db_index=True)
    razorpay_signature = models.TextField(blank=True, default='')
    amount = models.FloatField(help_text="Amount in INR Rupees")
    currency = models.CharField(max_length=10, default='INR')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    payment_method = models.CharField(max_length=50, default='Razorpay')
    error_code = models.CharField(max_length=100, blank=True, default='')
    error_description = models.TextField(blank=True, default='')
    error_source = models.CharField(max_length=100, blank=True, default='')
    error_step = models.CharField(max_length=100, blank=True, default='')
    error_reason = models.CharField(max_length=100, blank=True, default='')
    notes = models.TextField(blank=True, default='')
    order_items_json = models.TextField(blank=True, default='[]')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order_number} - {self.status} - ₹{self.amount}"




class Enquiry(models.Model):
    id = models.AutoField(primary_key=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, default=None, null=True, blank=True)
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=10)
    email = models.EmailField()
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=6)
    date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.phone}"



class Gallery(models.Model):
    id = models.AutoField(primary_key=True)
    image = models.URLField(max_length=1024)
    url=models.URLField(max_length=1024,default='')


class Contact(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=10)
    email = models.EmailField()
    message = models.TextField()
    date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.phone}"


class PopularLink(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255, help_text="Anchor text / SEO keyword display title")
    url = models.CharField(max_length=1024, help_text="Target URL or redirect destination (e.g. /search/?query=... or custom URL)")
    supercategory = models.ForeignKey(Supercategory, on_delete=models.CASCADE, null=True, blank=True, related_name="popular_links")
    maincategory = models.ForeignKey(Maincategory, on_delete=models.CASCADE, null=True, blank=True, related_name="popular_links")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True, related_name="popular_links")
    subcategory = models.ForeignKey(Subcategory, on_delete=models.CASCADE, null=True, blank=True, related_name="popular_links")
    state = models.CharField(max_length=100, blank=True, default='', help_text="State / City name (optional)")
    show_on_home = models.BooleanField(default=False, help_text="Show in Home Page SEO Hub")
    order = models.IntegerField(default=0, help_text="Display priority order")
    is_active = models.BooleanField(default=True, help_text="Toggle link visibility")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = "Popular Link"
        verbose_name_plural = "Popular Links"

    def __str__(self):
        return self.title


class DeviceToken(models.Model):
    id = models.AutoField(primary_key=True)
    token = models.CharField(max_length=500, unique=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    device_type = models.CharField(max_length=50, default='web')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.device_type} - {self.token[:20]}..."


class PushNotification(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    body = models.TextField()
    url = models.CharField(max_length=500, default='/')
    icon = models.CharField(max_length=500, default='/default-icon.png', blank=True)
    image = models.CharField(max_length=500, blank=True, default='')
    total_sent = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class PasswordResetOTP(models.Model):
    id = models.AutoField(primary_key=True)
    email = models.EmailField(max_length=254)
    otp = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def is_valid(self):
        import datetime
        from django.utils import timezone
        return not self.is_used and (timezone.now() - self.created_at) < datetime.timedelta(minutes=15)

    def __str__(self):
        return f"{self.email} - {self.otp}"


