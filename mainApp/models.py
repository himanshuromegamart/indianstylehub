from django.db import models
from tinymce.models import HTMLField



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
    image = models.URLField(max_length=1024)
    title=models.CharField(max_length=200)
    slug=models.CharField(max_length=200)
    description=HTMLField(default='')
    meta_description=models.TextField(default='',null=True,blank=True)
    views=models.IntegerField(default=0)
    date=models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.title
    

#User Models
class Buyer(models.Model):
    id=models.AutoField(primary_key=True)
    name=models.CharField(max_length=150,default='')
    phone=models.CharField(max_length=10,default='')
    email=models.EmailField(default='')
    password=models.CharField(max_length=50,default='')
    verification=models.CharField(max_length=30,default="pending")
    date=models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return str(self.name)
    


class Address(models.Model):
    id=models.AutoField(primary_key=True)
    buyer=models.ForeignKey(Buyer,on_delete=models.CASCADE)
    addressType= models.CharField(max_length=100,default='')
    alternatePhone= models.CharField(max_length=10,default='')
    address= models.CharField(max_length=10,default='')
    landmark= models.CharField(max_length=10,default='')
    city= models.CharField(max_length=10,default='')
    state= models.CharField(max_length=10,default='')
    pin= models.CharField(max_length=10,default='')


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

    def __str__(self):
        return f"Order {self.id} - {self.buyer}"



class Enquiry(models.Model):
    id = models.AutoField(primary_key=True)
    product = models.ForeignKey(Product, on_delete=models.SET_DEFAULT, default=None)
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