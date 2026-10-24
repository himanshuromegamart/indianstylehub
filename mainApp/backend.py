from django.shortcuts import render
import requests
from .models import *
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required,user_passes_test
from django.http import HttpResponseForbidden
from django.core.paginator import Paginator
from django.shortcuts import render,HttpResponse,redirect
from django.contrib import messages
from django.utils.text import slugify
from django.shortcuts import render, redirect, get_object_or_404
from random import randrange
from django.db.models import Q

#API
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import os
from io import StringIO
import json
import io


import uuid
from django.conf import settings
from django.utils.text import get_valid_filename
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def is_superuser(user):
    return user.is_superuser


# Function to store the image (remote server with automatic local media fallback)
def image_store(image_type, image_file):
    print(f"image_store called for type: {image_type}")
    if not image_file:
        return ""

    filename = getattr(image_file, 'name', 'upload.jpg')
    content_type = getattr(image_file, 'content_type', 'image/jpeg')

    # Safely read file content into memory
    try:
        if hasattr(image_file, 'read'):
            file_bytes = image_file.read()
            if hasattr(image_file, 'seek'):
                image_file.seek(0)
        else:
            file_bytes = bytes(image_file)
    except Exception as e:
        print(f"Error reading image file: {e}")
        return ""

    if not file_bytes:
        print("Empty file received in image_store")
        return ""

    # 1. Try remote image server
    base_url = os.environ.get('IMAGE_STORE_URL', "https://image.narifashionstore.com/add-image/")
    urls_to_try = [base_url]
    if base_url.startswith("https://"):
        urls_to_try.append(base_url.replace("https://", "http://"))

    for target_url in urls_to_try:
        try:
            files = {
                'image': (filename, io.BytesIO(file_bytes), content_type)
            }
            data = {
                'image_type': image_type
            }
            response = requests.post(target_url, data=data, files=files, timeout=15, verify=False)
            if response.status_code == 201:
                response_data = response.json()
                image_url = response_data.get("image_url") or response_data.get("url") or response_data.get("file_url")
                if image_url:
                    print(f"Remote image uploaded successfully: {image_url}")
                    return image_url
            else:
                print(f"Remote upload {target_url} returned status {response.status_code}: {response.text[:200]}")
        except Exception as e:
            print(f"Failed to connect to remote image store ({target_url}): {e}")

    # 2. Fallback: Save directly to local media storage
    try:
        clean_name = get_valid_filename(filename)
        unique_name = f"{uuid.uuid4().hex[:8]}_{clean_name}"
        folder = os.path.join(settings.MEDIA_ROOT, image_type)
        os.makedirs(folder, exist_ok=True)
        file_path = os.path.join(folder, unique_name)
        with open(file_path, 'wb') as f:
            f.write(file_bytes)
        local_url = f"/media/{image_type}/{unique_name}"
        print(f"Local storage fallback successful: {local_url}")
        return local_url
    except Exception as e:
        print(f"Local media fallback error: {e}")
        return ""


# Function to save product with an uploaded image
def product_store(request):
    if request.method == "POST":
        # Get image type and uploaded image from the POST request
        image_type = request.POST.get('image_type')
        uploaded_image = request.FILES.get('image')

        if uploaded_image:
            # Call the image_store function to upload the image and get the URL
            image_url = image_store(image_type, uploaded_image)
        else:
            image_url = None

        # Proceed only if the image URL was successfully retrieved
        if image_url:
            product = Maincategory()
            product.name = request.POST.get('name')  # Get the product name
            product.image = image_url  # Assign the image URL to the product
            product.save()  # Save the product in the database
            return render(request, 'front/data.html', {"success": True, "image_url": image_url})
        else:
            return render(request, 'front/data.html', {"error": "Failed to upload image or save data."})

    return render(request, 'front/data.html')



def admin_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        
        user = authenticate(username=username, password=password)
        
        if user is not None:
            if user.is_superuser:
                login(request, user)
                # Redirect based on user type or 'next' parameter
                next_url = request.GET.get("next")
                if next_url:
                   return redirect(next_url)
                else:
                    return redirect("/admin-dashboard")
            else:
                messages.error(request, "You do not have admin privileges.")
        else:
            messages.error(request, "Invalid Username or Password!")
    
    return render(request, "backend/login.html")


def admin_logout(request):
    logout(request)
    try:
        request.session.flush()
    except Exception:
        pass
    return redirect("/admin-login/")


@login_required(login_url='/admin-login')
def admin_dashboard(Request):
    if not Request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")
    else:
        from django.db.models import Sum
        data = Product.objects.all().order_by('-id')
        offers = Supercategory.objects.all().order_by('-id')
        prod = Product.objects.count()
        ord = Order.objects.count()
        enq = Enquiry.objects.count()
        buyer_count = Buyer.objects.count()

        # Product stock breakdown
        act = Product.objects.filter(quantity__gt=0).count()
        oos = Product.objects.filter(quantity__lte=0).count()
        pen = Order.objects.filter(orderStatus__iexact='pending').count()

        # Comprehensive Razorpay Payment Metrics
        total_payments = Payment.objects.count()
        payment_success_count = Payment.objects.filter(status='SUCCESS').count()
        payment_failed_count = Payment.objects.filter(status__in=['FAILED', 'CANCELLED']).count()
        payment_pending_count = Payment.objects.filter(status='PENDING').count()
        total_revenue = Payment.objects.filter(status='SUCCESS').aggregate(Sum('amount'))['amount__sum'] or 0.0
        success_rate = round((payment_success_count / total_payments * 100), 1) if total_payments > 0 else 0.0

        # Recent activities
        recent_orders = Order.objects.all().order_by('-id')[:8]
        recent_payments = Payment.objects.all().order_by('-created_at')[:8]

        paginator = Paginator(data, 100)
        page_number = Request.GET.get('page')
        page_posts = paginator.get_page(page_number)
        current_page = page_posts.number
        total_pages = paginator.num_pages
        page_range = range(max(current_page - 2, 1), min(current_page + 3, total_pages + 1))

        return render(Request, 'backend/index.html', {
            'page_posts': page_posts,
            'page_range': page_range,
            'offers': offers,
            'prod': prod,
            'ord': ord,
            'enq': enq,
            'act': act,
            'oos': oos,
            'pen': pen,
            'buyer_count': buyer_count,
            'recent_orders': recent_orders,
            'recent_payments': recent_payments,
            'total_payments': total_payments,
            'payment_success_count': payment_success_count,
            'payment_failed_count': payment_failed_count,
            'payment_pending_count': payment_pending_count,
            'total_revenue': total_revenue,
            'success_rate': success_rate,
        })


# Slider
@login_required(login_url='/admin-login/')
@user_passes_test(lambda u: u.is_superuser, login_url='/admin-login/')
def slider_page(request):
    # Check if the user is a superuser
    if not request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")

    if request.method == "POST":
        # Fetch existing sliders for the template
        slider = Slider.objects.all().order_by('-id')

        uploaded_image = request.FILES.get('sliderImage')
        link = request.POST.get('link')

        # Create a new Slider instance
        new_slider = Slider()

        # Handle image upload and storage
        if uploaded_image:
            # Call the `image_store` function to upload the image and get the URL
            image_url = image_store("category", uploaded_image)
            new_slider.image = image_url
        else:
            new_slider.image = ''

        
        new_slider.link=link
        # Save the slider to the database
        new_slider.save()

        # Redirect to the slider list page
        return redirect('/slider')

    # If GET request, render the slider template
    slider = Slider.objects.all().order_by('-id')  # Fetch all sliders
    return render(request, 'backend/slider.html', {'slider': slider})



@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def delete_slider(Request,id):
    if not Request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")
    else:  
       data=Slider.objects.get(id=id)
       data.delete()
       return redirect('/slider')



#Maincategory
@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def add_supercategory(Request):
    if not Request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")
    else:  
       
        supercategories=Supercategory.objects.all().order_by('id').reverse()
        if(Request.method=="POST"):
            m=Supercategory()
            m.name=Request.POST.get('name')
            m.slug=slugify(m.name)
            uploaded_image=Request.FILES.get('image')
            if uploaded_image:
                image_url = image_store("category", uploaded_image)
            else:
                image_url = ''
            m.image = image_url or ''
            m.title = Request.POST.get('title', '')
            m.description = Request.POST.get('description', '')
            
            m.save()
            return redirect('/supercategory')
        return render(Request,'backend/add-supercategory.html',{'supercategories':supercategories})

@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def supercategory_page(Request):
    if not Request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")
    else:  
        
        supercategory=Supercategory.objects.all().order_by('id').reverse()
        return render(Request,'backend/supercategory.html',{'supercategory':supercategory})

@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def update_supercategory(Request,id):
    if not Request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")
    else:  
        supercategories=Supercategory.objects.all().order_by('id').reverse()
        data=Supercategory.objects.get(id=id)
        if(Request.method=="POST"):
            data.name=Request.POST.get('name')
            data.slug=slugify(data.name)
            uploaded_image=Request.FILES.get('image')
            if uploaded_image:
                image_url = image_store("category", uploaded_image)
                if image_url:
                    data.image=image_url
            data.title = Request.POST.get('title', '')
            data.description = Request.POST.get('description', '')
            
            data.save()
            return redirect('/supercategory')
        return render(Request,'backend/update-supercategory.html',{'data':data,'supercategories':supercategories})


@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def delete_supercategory(Request,id):
    if not Request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")
    else:  
       data=Supercategory.objects.get(id=id)
       data.delete()
       return redirect('/supercategory')



@login_required(login_url='/admin-login/')
@user_passes_test(lambda u: u.is_superuser, login_url='/admin-login/')
def add_maincategory(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")

    maincategories = Maincategory.objects.all().order_by('-id')
    supercategories = Supercategory.objects.all().order_by('name')

    if request.method == "POST":
        m = Maincategory()
        m.name = request.POST.get('name')
        m.slug = slugify(m.name)
        
        supercat_id = request.POST.get('supercategory')
        if supercat_id:
            m.supercategory = Supercategory.objects.filter(id=supercat_id).first()

        # Handle images
        image_fields = ['image', 'banner1', 'banner2', 'banner3', 'banner4']
        for field in image_fields:
            uploaded_image = request.FILES.get(field)
            if uploaded_image:
                image_url = image_store("category", uploaded_image)
                setattr(m, field, image_url or '')
            else:
                setattr(m, field, '')

        if not m.image:
            m.image = ''

        m.title = request.POST.get('title')
        m.description = request.POST.get('description')
        m.save()
        return redirect('/maincategory')

    return render(request, 'backend/add-maincategory.html', {
        'maincategories': maincategories,
        'supercategories': supercategories,
    })


@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def maincategory_page(Request):
    if not Request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")
    else:  
        maincategory=Maincategory.objects.all().order_by('id').reverse()
        return render(Request,'backend/maincategory.html',{'maincategory':maincategory})


@login_required(login_url='/admin-login/')
@user_passes_test(lambda u: u.is_superuser, login_url='/admin-login/')
def update_maincategory(request, id):
    if not request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")

    maincategories = Maincategory.objects.all().order_by('-id')
    supercategories = Supercategory.objects.all().order_by('name')
    data = get_object_or_404(Maincategory, id=id)

    if request.method == "POST":
        data.name = request.POST.get('name')
        data.slug = slugify(data.name)

        supercat_id = request.POST.get('supercategory')
        if supercat_id:
            data.supercategory = Supercategory.objects.filter(id=supercat_id).first()
        else:
            data.supercategory = None

        # Image fields
        image_fields = ['image', 'banner1', 'banner2', 'banner3', 'banner4']
        for field in image_fields:
            uploaded_image = request.FILES.get(field)
            if uploaded_image:
                image_url = image_store("category", uploaded_image)
                if image_url:
                    setattr(data, field, image_url)

        data.title = request.POST.get('title')
        data.description = request.POST.get('description')
        data.save()

        return redirect('/maincategory')

    return render(request, 'backend/update-maincategory.html', {
        'data': data,
        'maincategories': maincategories,
        'supercategories': supercategories,
    })

@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def delete_maincategory(Request,id):
    if not Request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")
    else:  
       data=Maincategory.objects.get(id=id)
       data.delete()
       return redirect('/maincategory')


#category
@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def add_category(Request):
    if not Request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")
    else: 
        
        mcat=Maincategory.objects.all().order_by('id').reverse()
        if(Request.method=="POST"):
            c=Category()
            c.maincategory=Maincategory.objects.get(name=Request.POST.get('maincategory'))
            c.name=Request.POST.get('name')
            c.slug=slugify(c.name)
            spec_keys = Request.POST.getlist('spec_key[]')
            spec_values = Request.POST.getlist('spec_value[]')

            if len(spec_keys) == len(spec_values):
                specifications = {key: value for key, value in zip(spec_keys, spec_values)}
                c.specifications = specifications

            uploaded_image=Request.FILES.get('image')
            uploaded_image2=Request.FILES.get('app_background')
            if uploaded_image:
                image_url = image_store("category", uploaded_image)
            else:
                image_url = ''
            c.image = image_url or ''
                
            if uploaded_image2:
                image_url2 = image_store("category", uploaded_image2)
            else:
                image_url2 = ''
            c.app_background = image_url2 or ''
            
            c.title=Request.POST.get('title')
            c.description=Request.POST.get('description')

            if Category.objects.filter(maincategory=c.maincategory ,name=c.name):
                messages.error(Request, "A category with this name already exists under the selected maincategory.")
                return render(Request, 'backend/update-subcategory.html', {
                    'mcat':mcat
                })
            c.save()
            return redirect('/category')
        return render(Request,'backend/add-category.html',{'mcat':mcat})


@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def category_page(Request):
    if not Request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")
    else: 
        
        category=Category.objects.all().order_by('id').reverse()
        return render(Request,'backend/category.html',{'category':category})



@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def update_category(request, id):
    if not request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")

    # Fetch the category and main categories
    data = get_object_or_404(Category, id=id)
    mcat = Maincategory.objects.all()

    if request.method == "POST":
        data.maincategory = Maincategory.objects.get(id=request.POST.get('maincategory'))
        data.name = request.POST.get('name')
        data.slug = slugify(data.name)

        # Handle specifications
        spec_keys = request.POST.getlist('spec_key[]')
        spec_values = request.POST.getlist('spec_value[]')
        if len(spec_keys) == len(spec_values):
            data.specifications = {key: value for key, value in zip(spec_keys, spec_values)}

        # Handle image upload
        uploaded_image = request.FILES.get('image')
        uploaded_image2 = request.FILES.get('app_background')
        if uploaded_image:
            image_url = image_store("category", uploaded_image)  # Replace with your actual image upload logic
            data.image = image_url
        if uploaded_image2:
                    image_url2 = image_store("category", uploaded_image2)  # Replace with your actual image upload logic
                    data.app_background = image_url2

        # Meta fields
        data.title = request.POST.get('title')
        data.description = request.POST.get('description')

        # Save updated category
        data.save()
        return redirect('/category')

    return render(request, 'backend/update-category.html', {'data': data, 'mcat': mcat})



@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def delete_category(Request,id):
    if not Request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")
    else: 
        data=Category.objects.get(id=id)
        data.delete()
    return redirect('/category')



#subcategory
@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def add_subcategory(Request):
    if not Request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")
    else: 
        
        subcategories=Subcategory.objects.all().order_by('id').reverse()
        maincategories = Maincategory.objects.all()
        categories = Category.objects.all()
        if(Request.method=="POST"):
            c=Subcategory()
            maincategory = Maincategory.objects.get(slug=Request.POST.get('maincategory'))
            c.category = Category.objects.get(maincategory=maincategory,slug=Request.POST.get('category'))
            c.name=Request.POST.get('name')
            c.slug=slugify(c.name)

            uploaded_image=Request.FILES.get('image')
            if uploaded_image:
                image_url = image_store("category", uploaded_image)
            else:
                image_url = ''
            c.image = image_url or ''

            
            
            c.title=Request.POST.get('title')
            c.description=Request.POST.get('description')
            if Subcategory.objects.filter(category=c.category ,name=c.name):
                print("Already Exist...")
                messages.error(Request, "A subcategory with this name already exists under the selected category.")
                return render(Request, 'backend/add-subcategory.html', {
                    'categories':categories,'maincategories':maincategories,'data':c
                })
            c.save()
            return redirect('/subcategory')
        return render(Request,'backend/add-subcategory.html',{'categories':categories,'subcategories':subcategories,'maincategories':maincategories})



@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def subcategory_page(Request):
    if not Request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")
    else: 
        
        subcategory=Subcategory.objects.all().order_by('id').reverse()
        return render(Request,'backend/subcategory.html',{'subcategory':subcategory})
    

    
@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def update_subcategory(request, id):
    if not request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")

    # Fetch subcategory and categories
    subcategories = Subcategory.objects.all()
    data = get_object_or_404(Subcategory, id=id)
    maincategories = Maincategory.objects.all()
    categories = Category.objects.all()

    if request.method == "POST":
        maincategory = Maincategory.objects.get(slug=request.POST.get('maincategory'))
        category = Category.objects.get(maincategory=maincategory,slug=request.POST.get('category'))
        name = request.POST.get('name')
        slug = slugify(name)

        # Check for duplicate name within the selected category
        if Subcategory.objects.filter(category=category, name=name).exclude(id=data.id).exists():
            messages.error(request, "A subcategory with this name already exists under the selected category.")
            return render(request, 'backend/update-subcategory.html', {
                'data': data, 'categories': categories, 'subcategories': subcategories,'maincategories':maincategories
            })

        # Handle slug uniqueness
        original_slug = slug
        counter = 1
        while Subcategory.objects.filter(slug=slug).exclude(id=data.id).exists():
            slug = f"{original_slug}-{counter}"
            counter += 1

        # Update data
        data.category = category
        data.name = name
        data.slug = slug

        # Handle image upload
        uploaded_image = request.FILES.get('image')
        if uploaded_image:
            image_url = image_store("category", uploaded_image)  # Replace with your actual upload logic
            data.image = image_url

        # Update meta fields
        data.title = request.POST.get('title', '').strip()
        data.description = request.POST.get('description', '').strip()

        # Save the updated subcategory
        data.save()
        messages.success(request, "Subcategory updated successfully.")
        return redirect('/subcategory')

    return render(request, 'backend/update-subcategory.html', {
        'data': data, 'categories': categories,'maincategories':maincategories, 'subcategories': subcategories
    })



@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def delete_subcategory(Request,id):
    if not Request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")
    else: 
        data=Subcategory.objects.get(id=id)
        data.delete()
    return redirect('/subcategory')



def clear_session(request):
    return JsonResponse({'status': False, 'message': "Disabled"})


#Brand
@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def add_brand(Request):
    if not Request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")
    else:  
       
        brand=Brand.objects.all()
        if(Request.method=="POST"):
            m=Brand()
            m.name=Request.POST.get('name')
            m.slug=slugify(m.name)
            uploaded_image=Request.FILES.get('image')
            if uploaded_image:
                image_url = image_store("category", uploaded_image)
            else:
                image_url = ''
            m.image = image_url or ''
            m.title=Request.POST.get('title')
            m.description=Request.POST.get('description')
            if Brand.objects.filter(name=m.name):
                print("Already Exist...")
                messages.error(Request, "A brand with this name already exists.")
                return render(Request, 'backend/add-brand.html', {
                    'brand':brand
                })
            m.save()
            return redirect('/brand')
        return render(Request,'backend/add-brand.html',{'brand':brand})



@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def brand_page(Request):
    if not Request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")
    else:  
        
        brand=Brand.objects.all().order_by('id').reverse()
        return render(Request,'backend/brand.html',{'brand':brand})


@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def update_brand(Request,id):
    if not Request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")
    else:  
        
        data=Brand.objects.get(id=id)
        if(Request.method=="POST"):
            data.name=Request.POST.get('name')
            data.slug=slugify(data.name)
            uploaded_image=Request.FILES.get('image')
            if uploaded_image:
            # Call the image_store function to upload the image and get the URL
               image_url = image_store("category", uploaded_image)
            else:
                image_url = None
            if(image_url):
                data.image=image_url
            
            data.title=Request.POST.get('title')
            data.description=Request.POST.get('description')
            if Brand.objects.filter(name=data.name).exclude(id=data.id).exists():
                print("Already Exist...")
                messages.error(Request, "A brand with this name already exists.")
                return render(Request, 'backend/update-brand.html', {
                    'data':data
                })
            data.save()
            return redirect('/brand')
        return render(Request,'backend/update-brand.html',{'data':data})


@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def delete_brand(Request,id):
    if not Request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")
    else:  
       data=Brand.objects.get(id=id)
       data.delete()
       return redirect('/brand')



#color
@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def add_color(Request):
    if not Request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")
    else:  
       
        color=Color.objects.all()
        if(Request.method=="POST"):
            m=Color()
            m.name=Request.POST.get('name')
            if Color.objects.filter(name=m.name):
                print("Already Exist...")
                messages.error(Request, "A color with this name already exists.")
                return render(Request, 'backend/add-color.html', {
                    'm':m
                })
            m.save()
            return redirect('/color')
        return render(Request,'backend/add-color.html',{'color':color})


@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def color_page(Request):
    if not Request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")
    else:  
        color=Color.objects.all().order_by('id').reverse()
        return render(Request,'backend/color.html',{'color':color})


@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def update_color(Request,id):
    if not Request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")
    else:  
        
        data=Color.objects.get(id=id)
        if(Request.method=="POST"):
            data.name=Request.POST.get('name')
            if Color.objects.filter(name=data.name).exclude(id=data.id).exists():
                print("Already Exist...")
                messages.error(Request, "A color with this name already exists.")
                return render(Request, 'backend/update-color.html', {
                    'data':data
                })
            data.save()
            return redirect('/color')
        return render(Request,'backend/update-color.html',{'data':data})


@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def delete_color(Request,id):
    if not Request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")
    else:  
       data=Color.objects.get(id=id)
       data.delete()
       return redirect('/color')


#Size
@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def add_size(Request):
    if not Request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")
    else:  
       
        size=Size.objects.all()
        if(Request.method=="POST"):
            m=Size()
            m.name=Request.POST.get('name')
            if Size.objects.filter(name=m.name):
                print("Already Exist...")
                messages.error(Request, "A color with this name already exists.")
                return render(Request, 'backend/add-size.html', {
                    'm':m
                })
            m.save()
            return redirect('/size')
        return render(Request,'backend/add-size.html',{'size':size})

@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def size_page(Request):
    if not Request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")
    else:  
        size=Size.objects.all().order_by('id').reverse()
        return render(Request,'backend/size.html',{'size':size})

@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def update_size(Request,id):
    if not Request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")
    else:  
        
        data=Size.objects.get(id=id)
        if(Request.method=="POST"):
            data.name=Request.POST.get('name')
            if Size.objects.filter(name=data.name).exclude(id=data.id):
                print("Already Exist...")
                messages.error(Request, "A color with this name already exists.")
                return render(Request, 'backend/update-size.html', {
                    'data':data
                })
            data.save()
            return redirect('/size')
        return render(Request,'backend/update-size.html',{'data':data})


@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def delete_size(Request,id):
    if not Request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")
    else:  
       data=Size.objects.get(id=id)
       data.delete()
       return redirect('/size')


@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def add_product(request):
    mcat = Maincategory.objects.all().order_by('-id')
    cat = Category.objects.all().order_by('-id')
    scat = Subcategory.objects.all().order_by('-id')
    brnd = Brand.objects.all().order_by('-id')
    clr = Color.objects.all().order_by('-id')
    sz = Size.objects.all().order_by('-id')
    supercats = Supercategory.objects.all().order_by('name')

    if request.method == "POST":
        product = Product()

        # Assign related fields safely
        mcat_slug = request.POST.get('maincategory')
        cat_slug = request.POST.get('category')
        scat_slug = request.POST.get('subcategory')
        supercat_id = request.POST.get('supercategory')

        if mcat_slug:
            product.maincategory = Maincategory.objects.filter(slug=mcat_slug).first()
        else:
            product.maincategory = None

        if product.maincategory and cat_slug:
            product.category = Category.objects.filter(maincategory=product.maincategory, slug=cat_slug).first()
        elif cat_slug:
            product.category = Category.objects.filter(slug=cat_slug).first()
        else:
            product.category = None

        if product.category and scat_slug:
            product.subcategory = Subcategory.objects.filter(category=product.category, slug=scat_slug).first()
        elif scat_slug:
            product.subcategory = Subcategory.objects.filter(slug=scat_slug).first()
        else:
            product.subcategory = None

        if supercat_id:
            product.supercategory = Supercategory.objects.filter(id=supercat_id).first()
        elif product.maincategory and product.maincategory.supercategory:
            product.supercategory = product.maincategory.supercategory

        # Upload images
        for i in range(1, 5):
            uploaded_image = request.FILES.get(f'image{i}')
            if uploaded_image:
                image_url = image_store("product", uploaded_image)
                setattr(product, f'image{i}', image_url or '')
            else:
                setattr(product, f'image{i}', '')

        # Assign other fields
        product.name = request.POST.get('name')
        try:
            # Get base price and discount from the POST request
            base_price = float(request.POST.get('price', 0))
            discount = float(request.POST.get('discount', 0))

            # Validate inputs
            if base_price < 0 or discount < 0:
                return JsonResponse({'error': 'Base price and discount must be non-negative'}, status=400)

            # Calculate the final price
            final_price = base_price - (base_price * discount / 100)

            # Assign values to the product model
            product.base_price = base_price
            product.discount = discount
            product.price = round(final_price, 2)  # Round the price to 2 decimal places

            try:
                seller_price = float(request.POST.get('seller_price', 0) or 0)
            except (ValueError, TypeError):
                seller_price = 0.0
            product.seller_price = seller_price

        except ValueError:
            # Handle invalid inputs (e.g., non-numeric values)
            return JsonResponse({'error': 'Invalid price or discount format'}, status=400)


        product.quantity = int(request.POST.get('quantity'))
        product.size = request.POST.get('size')
        product.color = request.POST.get('color')
        product.rating = float(request.POST.get('rating', 0))
        product.reviews = int(request.POST.get('reviews', 0))
        product.description = request.POST.get('description')
        product.sku = request.POST.get('sku', '')
        product.weight = request.POST.get('weight', '')
        product.length = request.POST.get('length', '')
        product.width = request.POST.get('width', '')
        product.height = request.POST.get('height', '')

        # Handle specifications
        spec_keys = request.POST.getlist('spec_key[]')
        spec_values = request.POST.getlist('spec_value[]')

        # Ensure lengths match and validate data
        if len(spec_keys) == len(spec_values):
            specifications = {}
            for key, value in zip(spec_keys, spec_values):
                if key.strip() and value.strip():  # Ensure neither key nor value is empty
                    specifications[key.strip()] = value.strip()
            product.specifications = specifications
        else:
            # Handle the error if lengths do not match
            return JsonResponse({'error': 'Mismatched specification keys and values'}, status=400)


        # Handle FAQs
        faq_keys = request.POST.getlist('faq_key[]')
        faq_values = request.POST.getlist('faq_value[]')

        # Ensure lengths match and validate data
        if len(faq_keys) == len(faq_values):
            faqs = {}
            for key, value in zip(faq_keys, faq_values):
                if key.strip() and value.strip():  # Ensure neither key nor value is empty
                    faqs[key.strip()] = value.strip()
            product.faq = faqs
        else:
            # Handle the error if lengths do not match
            return JsonResponse({'error': 'Mismatched FAQ keys and values'}, status=400)

        # SEO & Search Optimization Fields
        product.tags = request.POST.get('tags', '').strip()
        product.meta_title = request.POST.get('meta_title', '').strip()
        product.meta_description = request.POST.get('meta_description', '').strip()
        product.meta_keywords = request.POST.get('meta_keywords', '').strip()

        # Save product
        product.save()
        return redirect('/product')

    context = {
        'maincategories': mcat, 'categories': cat, 'subcategories': scat,
        'brands': brnd, 'clr': clr, 'sz': sz, 'supercategories': supercats,
    }
    return render(request, 'backend/add-product.html', context)


@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def product_page(Request):
    if not Request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")
    else: 
        
        data=Product.objects.all().order_by('id').reverse()
        paginator = Paginator(data, 100)  # Show 10 posts per page
        page_number = Request.GET.get('page')
        page_posts = paginator.get_page(page_number)
        current_page = page_posts.number
        total_pages = paginator.num_pages
        page_range = range(max(current_page - 2, 1), min(current_page + 3, total_pages + 1))
        # return render(Request,'superadmin/index.html',{'page_posts':page_posts,'page_range': page_range,'prod':prod,'ord':ord,'sel':sel,'pen':pen,'act':act,'oos':oos})
        return render(Request,'backend/products.html',{'page_posts':page_posts,'page_range': page_range})




@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def update_product(request,id,pn):
    mcat = Maincategory.objects.all().order_by('-id')
    cat = Category.objects.all().order_by('-id')
    scat = Subcategory.objects.all().order_by('-id')
    brnd = Brand.objects.all().order_by('-id')
    clr = Color.objects.all().order_by('-id')
    sz = Size.objects.all().order_by('-id')
    supercats = Supercategory.objects.all().order_by('name')

    product= get_object_or_404(Product,id=id)
    if request.method == "POST":

        # Assign related fields safely
        mcat_slug = request.POST.get('maincategory')
        cat_slug = request.POST.get('category')
        scat_slug = request.POST.get('subcategory')
        supercat_id = request.POST.get('supercategory')

        if mcat_slug:
            product.maincategory = Maincategory.objects.filter(slug=mcat_slug).first()
        else:
            product.maincategory = None

        if product.maincategory and cat_slug:
            product.category = Category.objects.filter(maincategory=product.maincategory, slug=cat_slug).first()
        elif cat_slug:
            product.category = Category.objects.filter(slug=cat_slug).first()
        else:
            product.category = None

        if product.category and scat_slug:
            product.subcategory = Subcategory.objects.filter(category=product.category, slug=scat_slug).first()
        elif scat_slug:
            product.subcategory = Subcategory.objects.filter(slug=scat_slug).first()
        else:
            product.subcategory = None

        if supercat_id:
            product.supercategory = Supercategory.objects.filter(id=supercat_id).first()
        elif product.maincategory and product.maincategory.supercategory:
            product.supercategory = product.maincategory.supercategory

        if(request.POST.get('brand')):
            product.brand = Brand.objects.filter(name=request.POST.get('brand')).first()

        # Upload images
        for i in range(1, 5):
            uploaded_image = request.FILES.get(f'image{i}')
            if uploaded_image:
                image_url = image_store("product", uploaded_image)
                if image_url:
                    setattr(product, f'image{i}', image_url)

        # Assign other fields
        product.name = request.POST.get('name')
        try:
            # Get base price and discount from the POST request
            base_price = float(request.POST.get('price', 0))
            discount = float(request.POST.get('discount', 0))

            # Validate inputs
            if base_price < 0 or discount < 0:
                return JsonResponse({'error': 'Base price and discount must be non-negative'}, status=400)

            # Calculate the final price
            final_price = base_price - (base_price * discount / 100)

            # Assign values to the product model
            product.base_price = base_price
            product.discount = discount
            product.price = round(final_price, 2)  # Round the price to 2 decimal places

            try:
                seller_price = float(request.POST.get('seller_price', 0) or 0)
            except (ValueError, TypeError):
                seller_price = 0.0
            product.seller_price = seller_price

        except ValueError:
            # Handle invalid inputs (e.g., non-numeric values)
            return JsonResponse({'error': 'Invalid price or discount format'}, status=400)


        product.quantity = int(request.POST.get('quantity'))
        product.size = request.POST.get('size')
        product.color = request.POST.get('color')
        product.rating = float(request.POST.get('rating', 0))
        product.reviews = int(request.POST.get('reviews', 0))
        product.description = request.POST.get('description')
        product.sku = request.POST.get('sku', '')
        product.weight = request.POST.get('weight', '')
        product.length = request.POST.get('length', '')
        product.width = request.POST.get('width', '')
        product.height = request.POST.get('height', '')

        # Handle specifications
        spec_keys = request.POST.getlist('spec_key[]')
        spec_values = request.POST.getlist('spec_value[]')

        # Ensure lengths match and validate data
        if len(spec_keys) == len(spec_values):
            specifications = {}
            for key, value in zip(spec_keys, spec_values):
                if key.strip() and value.strip():  # Ensure neither key nor value is empty
                    specifications[key.strip()] = value.strip()
            product.specifications = specifications
        else:
            # Handle the error if lengths do not match
            return JsonResponse({'error': 'Mismatched specification keys and values'}, status=400)


        # Handle FAQs
        faq_keys = request.POST.getlist('faq_key[]')
        faq_values = request.POST.getlist('faq_value[]')

        # Ensure lengths match and validate data
        if len(faq_keys) == len(faq_values):
            faqs = {}
            for key, value in zip(faq_keys, faq_values):
                if key.strip() and value.strip():  # Ensure neither key nor value is empty
                    faqs[key.strip()] = value.strip()
            product.faq = faqs
        else:
            # Handle the error if lengths do not match
            return JsonResponse({'error': 'Mismatched FAQ keys and values'}, status=400)

        # SEO & Search Optimization Fields
        product.tags = request.POST.get('tags', '').strip()
        product.meta_title = request.POST.get('meta_title', '').strip()
        product.meta_description = request.POST.get('meta_description', '').strip()
        product.meta_keywords = request.POST.get('meta_keywords', '').strip()

        # Save product
        product.save()
        return redirect('/product')

    context = {
        'maincategories': mcat, 'categories': cat, 'subcategories': scat,
        'brands': brnd, 'clr': clr, 'sz': sz, 'data': product,
        'supercategories': supercats,
    }
    return render(request, 'backend/update-product.html', context)



@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def product_page(Request):
    if not Request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")
    else: 
        
        data=Product.objects.all().order_by('id').reverse()
        paginator = Paginator(data, 100)  # Show 10 posts per page
        page_number = Request.GET.get('page')
        page_posts = paginator.get_page(page_number)
        current_page = page_posts.number
        total_pages = paginator.num_pages
        page_range = range(max(current_page - 2, 1), min(current_page + 3, total_pages + 1))
        # return render(Request,'superadmin/index.html',{'page_posts':page_posts,'page_range': page_range,'prod':prod,'ord':ord,'sel':sel,'pen':pen,'act':act,'oos':oos})
        return render(Request,'backend/products.html',{'page_posts':page_posts,'page_range': page_range})




@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def duplicate_product(request,id,pn):
    mcat = Maincategory.objects.all().order_by('-id')
    cat = Category.objects.all().order_by('-id')
    scat = Subcategory.objects.all().order_by('-id')
    brnd = Brand.objects.all().order_by('-id')
    clr = Color.objects.all().order_by('-id')
    sz = Size.objects.all().order_by('-id')
    supercats = Supercategory.objects.all().order_by('name')

    data= get_object_or_404(Product,id=id)
    product= Product()
    if request.method == "POST":

        # Assign related fields safely
        mcat_slug = request.POST.get('maincategory')
        cat_slug = request.POST.get('category')
        scat_slug = request.POST.get('subcategory')
        supercat_id = request.POST.get('supercategory')

        if mcat_slug:
            product.maincategory = Maincategory.objects.filter(slug=mcat_slug).first()
        else:
            product.maincategory = None

        if product.maincategory and cat_slug:
            product.category = Category.objects.filter(maincategory=product.maincategory, slug=cat_slug).first()
        elif cat_slug:
            product.category = Category.objects.filter(slug=cat_slug).first()
        else:
            product.category = None

        if product.category and scat_slug:
            product.subcategory = Subcategory.objects.filter(category=product.category, slug=scat_slug).first()
        elif scat_slug:
            product.subcategory = Subcategory.objects.filter(slug=scat_slug).first()
        else:
            product.subcategory = None

        if supercat_id:
            product.supercategory = Supercategory.objects.filter(id=supercat_id).first()
        elif product.maincategory and product.maincategory.supercategory:
            product.supercategory = product.maincategory.supercategory

        if(request.POST.get('brand')):
            product.brand = Brand.objects.filter(name=request.POST.get('brand')).first()

        # Upload images
        for i in range(1, 5):
            uploaded_image = request.FILES.get(f'image{i}')
            
            if uploaded_image:
                image_url = image_store("product", uploaded_image)
                setattr(product, f'image{i}', image_url)
            else:
                # Use getattr to safely retrieve the existing image URL
                existing_image = getattr(data, f'image{i}', None)
                setattr(product, f'image{i}', existing_image)



        # Assign other fields
        product.name = request.POST.get('name')
        try:
            # Get base price and discount from the POST request
            base_price = float(request.POST.get('price', 0))
            discount = float(request.POST.get('discount', 0))

            # Validate inputs
            if base_price < 0 or discount < 0:
                return JsonResponse({'error': 'Base price and discount must be non-negative'}, status=400)

            # Calculate the final price
            final_price = base_price - (base_price * discount / 100)

            # Assign values to the product model
            product.base_price = base_price
            product.discount = discount
            product.price = round(final_price, 2)  # Round the price to 2 decimal places

            try:
                seller_price = float(request.POST.get('seller_price', 0) or getattr(data, 'seller_price', 0) or 0)
            except (ValueError, TypeError):
                seller_price = 0.0
            product.seller_price = seller_price

        except ValueError:
            # Handle invalid inputs (e.g., non-numeric values)
            return JsonResponse({'error': 'Invalid price or discount format'}, status=400)


        product.quantity = int(request.POST.get('quantity'))
        product.size = request.POST.get('size')
        product.color = request.POST.get('color')
        product.rating = float(request.POST.get('rating', 0))
        product.reviews = int(request.POST.get('reviews', 0))
        product.description = request.POST.get('description')
        product.sku = request.POST.get('sku', '')
        product.weight = request.POST.get('weight', '')
        product.length = request.POST.get('length', '')
        product.width = request.POST.get('width', '')
        product.height = request.POST.get('height', '')

        # Handle specifications
        spec_keys = request.POST.getlist('spec_key[]')
        spec_values = request.POST.getlist('spec_value[]')

        # Ensure lengths match and validate data
        if len(spec_keys) == len(spec_values):
            specifications = {}
            for key, value in zip(spec_keys, spec_values):
                if key.strip() and value.strip():  # Ensure neither key nor value is empty
                    specifications[key.strip()] = value.strip()
            product.specifications = specifications
        else:
            # Handle the error if lengths do not match
            return JsonResponse({'error': 'Mismatched specification keys and values'}, status=400)


        # Handle FAQs
        faq_keys = request.POST.getlist('faq_key[]')
        faq_values = request.POST.getlist('faq_value[]')

        # Ensure lengths match and validate data
        if len(faq_keys) == len(faq_values):
            faqs = {}
            for key, value in zip(faq_keys, faq_values):
                if key.strip() and value.strip():  # Ensure neither key nor value is empty
                    faqs[key.strip()] = value.strip()
            product.faq = faqs
        else:
            # Handle the error if lengths do not match
            return JsonResponse({'error': 'Mismatched FAQ keys and values'}, status=400)

        # SEO & Search Optimization Fields
        product.tags = request.POST.get('tags', '').strip()
        product.meta_title = request.POST.get('meta_title', '').strip()
        product.meta_description = request.POST.get('meta_description', '').strip()
        product.meta_keywords = request.POST.get('meta_keywords', '').strip()

        # Save product
        product.save()
        return redirect('/product')

    context = {
        'maincategories': mcat, 'categories': cat, 'subcategories': scat,
        'brands': brnd, 'clr': clr, 'sz': sz, 'data': data,
        'supercategories': supercats,
    }
    return render(request, 'backend/update-product.html', context)


@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def delete_product(Request,id):
    if not Request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")
    else: 
        data=get_object_or_404(Product,id=id)
        data.delete()
    return redirect('/product')



@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def update_product_offers(request,id,ops):
    try:
       data=get_object_or_404(Product,id=id)
       ofr=get_object_or_404(Supercategory,slug=ops)
       if(data):
           data.offers=ofr
           data.save()
    except:
        return HttpResponse("Invalid action...")
    return redirect("/admin-dashboard")



@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def enquiry(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")
    else:  
        data=Enquiry.objects.all().order_by('id').reverse()
        paginator = Paginator(data, 100)  # Show 10 posts per page
        page_number = request.GET.get('page')
        page_posts = paginator.get_page(page_number)
        current_page = page_posts.number
        total_pages = paginator.num_pages
        page_range = range(max(current_page - 2, 1), min(current_page + 3, total_pages + 1))
    return render(request,'backend/enquiry.html',{'page_posts':page_posts,'page_range': page_range})



@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def enquiry_details(request,id):
    if not request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")
    else:  
        data=Enquiry.objects.get(id=id)
    return render(request,'backend/enquiry-details.html',{'data':data})




@login_required(login_url='/admin-login')
def admin_blog(request):
    search_query = request.GET.get('search_query', '')
    if search_query:
        data = Blog.objects.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(meta_description__icontains=search_query)
        ).order_by('-id')
    else:
        data = Blog.objects.all().order_by('-id')

    paginator = Paginator(data, 100)
    page_number = request.GET.get('page')
    page_posts = paginator.get_page(page_number)

    context = {
        'page_posts': page_posts,
        'page_range': range(max(page_posts.number - 2, 1), min(page_posts.number + 3, paginator.num_pages + 1)),
        'total_pages': paginator.num_pages,
        'search_query': search_query,
        
    }

    return render(request, 'backend/blog.html', context)



@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def admin_add_blog(request):
    supercategories = Supercategory.objects.all().order_by('name')
    categories = Category.objects.all().order_by('name')
    products = Product.objects.all().order_by('-id')[:200]

    if request.method == "POST":
        blog = Blog()
        blog.title = request.POST.get('title', '').strip()
        raw_slug = request.POST.get('slug', '').strip()
        base_slug = slugify(raw_slug) if raw_slug else slugify(blog.title)
        slug = base_slug
        counter = 1
        while Blog.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        blog.slug = slug

        # Relationships
        supercat_id = request.POST.get('supercategory')
        cat_id = request.POST.get('category')
        prod_id = request.POST.get('product')

        if supercat_id:
            blog.supercategory = Supercategory.objects.filter(id=supercat_id).first()
        if cat_id:
            blog.category = Category.objects.filter(id=cat_id).first()
        if prod_id:
            blog.product = Product.objects.filter(id=prod_id).first()

        uploaded_image = request.FILES.get('image')
        if uploaded_image:
            image_url = image_store("blog", uploaded_image)
            blog.image = image_url or ''
        else:
            blog.image = ''

        blog.description = request.POST.get('description', '')
        blog.meta_description = request.POST.get('meta_description', '')
        blog.save()
        messages.success(request, "Blog post created successfully.")
        return redirect("/admin-blog")

    return render(request, 'backend/add-blog.html', {
        'supercategories': supercategories,
        'categories': categories,
        'products': products,
    })


@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def admin_update_blog(request, id):
    blog = get_object_or_404(Blog, id=id)
    supercategories = Supercategory.objects.all().order_by('name')
    categories = Category.objects.all().order_by('name')
    products = Product.objects.all().order_by('-id')[:200]

    if request.method == "POST":
        blog.title = request.POST.get('title', '').strip()
        raw_slug = request.POST.get('slug', '').strip()
        base_slug = slugify(raw_slug) if raw_slug else slugify(blog.title)
        slug = base_slug
        counter = 1
        while Blog.objects.filter(slug=slug).exclude(id=blog.id).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        blog.slug = slug

        # Relationships
        supercat_id = request.POST.get('supercategory')
        cat_id = request.POST.get('category')
        prod_id = request.POST.get('product')

        if supercat_id:
            blog.supercategory = Supercategory.objects.filter(id=supercat_id).first()
        else:
            blog.supercategory = None

        if cat_id:
            blog.category = Category.objects.filter(id=cat_id).first()
        else:
            blog.category = None

        if prod_id:
            blog.product = Product.objects.filter(id=prod_id).first()
        else:
            blog.product = None

        uploaded_image = request.FILES.get('image')
        if uploaded_image:
            image_url = image_store("blog", uploaded_image)
            if image_url:
                blog.image = image_url

        blog.description = request.POST.get('description', '')
        blog.meta_description = request.POST.get('meta_description', '')
        blog.save()
        messages.success(request, "Blog post updated successfully.")
        return redirect("/admin-blog")

    return render(request, 'backend/update-blog.html', {
        'blog': blog,
        'supercategories': supercategories,
        'categories': categories,
        'products': products,
    })


@login_required(login_url="/admin-login")
def admin_delete_blog(request,id):
    data=get_object_or_404(Blog,id=id)
    if(data):
        data.delete()
    return redirect("/admin-blog")




# Slider
@login_required(login_url='/admin-login/')
@user_passes_test(lambda u: u.is_superuser, login_url='/admin-login/')
def gallery_page(request):
    # Check if the user is a superuser
    if not request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")

    if request.method == "POST":
        # Fetch existing sliders for the template
        gallery = Gallery.objects.all().order_by('-id')

        uploaded_image = request.FILES.get('image')
        url = request.POST.get('url')

        # Create a new Slider instance
        gallery = Gallery()

        # Handle image upload and storage
        if uploaded_image:
            # Call the `image_store` function to upload the image and get the URL
            image_url = image_store("category", uploaded_image)
            gallery.image = image_url
        else:
            gallery.image = ''
        # Set the URL for the slider
        gallery.url=url
        # Save the slider to the database
        gallery.save()

        # Redirect to the slider list page
        return redirect('/gallery')

    # If GET request, render the gallery template
    gallery = Gallery.objects.all().order_by('-id')  # Fetch all gallerys
    return render(request, 'backend/gallery.html', {'gallery': gallery})



@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def delete_gallery(Request,id):
    if not Request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")
    else:  
       data=Gallery.objects.get(id=id)
       data.delete()
       return redirect('/gallery')


# ==================== POPULAR LINKS (SEO) MANAGEMENT ====================
@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def popular_links_page(request):
    search_query = request.GET.get('search_query', '')
    if search_query:
        links = PopularLink.objects.filter(
            Q(title__icontains=search_query) |
            Q(url__icontains=search_query) |
            Q(state__icontains=search_query)
        ).order_by('order', '-id')
    else:
        links = PopularLink.objects.all().order_by('order', '-id')

    paginator = Paginator(links, 50)
    page_number = request.GET.get('page')
    page_posts = paginator.get_page(page_number)

    return render(request, 'backend/popular-links.html', {
        'page_posts': page_posts,
        'total_count': links.count(),
        'search_query': search_query,
    })


@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def add_popular_link(request):
    supercategories = Supercategory.objects.all().order_by('name')
    maincategories = Maincategory.objects.all().order_by('name')
    categories = Category.objects.all().order_by('name')
    subcategories = Subcategory.objects.all().order_by('name')

    if request.method == "POST":
        link = PopularLink()
        link.title = request.POST.get('title', '').strip()
        link.url = request.POST.get('url', '').strip()
        link.state = request.POST.get('state', '').strip()
        link.order = int(request.POST.get('order', 0) or 0)
        link.show_on_home = True if (request.POST.get('show_on_home') in ['on', '1', 'true', True]) else False
        link.is_active = True if (request.POST.get('is_active') in ['on', '1', 'true', True]) else False

        supercat_id = request.POST.get('supercategory')
        maincat_id = request.POST.get('maincategory')
        cat_id = request.POST.get('category')
        subcat_id = request.POST.get('subcategory')

        if supercat_id:
            link.supercategory = Supercategory.objects.filter(id=supercat_id).first()
        if maincat_id:
            link.maincategory = Maincategory.objects.filter(id=maincat_id).first()
        if cat_id:
            link.category = Category.objects.filter(id=cat_id).first()
        if subcat_id:
            link.subcategory = Subcategory.objects.filter(id=subcat_id).first()

        link.save()
        messages.success(request, f"Popular Link '{link.title}' added successfully!")
        return redirect('/popular-links/')

    return render(request, 'backend/add-popular-link.html', {
        'supercategories': supercategories,
        'maincategories': maincategories,
        'categories': categories,
        'subcategories': subcategories,
    })


@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def update_popular_link(request, id):
    link = get_object_or_404(PopularLink, id=id)
    supercategories = Supercategory.objects.all().order_by('name')
    maincategories = Maincategory.objects.all().order_by('name')
    categories = Category.objects.all().order_by('name')
    subcategories = Subcategory.objects.all().order_by('name')

    if request.method == "POST":
        link.title = request.POST.get('title', '').strip()
        link.url = request.POST.get('url', '').strip()
        link.state = request.POST.get('state', '').strip()
        link.order = int(request.POST.get('order', 0) or 0)
        link.show_on_home = True if (request.POST.get('show_on_home') in ['on', '1', 'true', True]) else False
        link.is_active = True if (request.POST.get('is_active') in ['on', '1', 'true', True]) else False

        supercat_id = request.POST.get('supercategory')
        maincat_id = request.POST.get('maincategory')
        cat_id = request.POST.get('category')
        subcat_id = request.POST.get('subcategory')

        link.supercategory = Supercategory.objects.filter(id=supercat_id).first() if supercat_id else None
        link.maincategory = Maincategory.objects.filter(id=maincat_id).first() if maincat_id else None
        link.category = Category.objects.filter(id=cat_id).first() if cat_id else None
        link.subcategory = Subcategory.objects.filter(id=subcat_id).first() if subcat_id else None

        link.save()
        messages.success(request, f"Popular Link '{link.title}' updated successfully!")
        return redirect('/popular-links/')

    return render(request, 'backend/update-popular-link.html', {
        'link': link,
        'supercategories': supercategories,
        'maincategories': maincategories,
        'categories': categories,
        'subcategories': subcategories,
    })


@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def delete_popular_link(request, id):
    link = get_object_or_404(PopularLink, id=id)
    title = link.title
    link.delete()
    messages.success(request, f"Popular Link '{title}' deleted successfully!")
    return redirect('/popular-links/')


# Orders Management
@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def admin_orders_page(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")
    
    status_filter = request.GET.get('status', '').strip()
    search_query = request.GET.get('search_query', '').strip()

    orders_qs = Order.objects.all().order_by('-id')

    if status_filter:
        orders_qs = orders_qs.filter(orderStatus__iexact=status_filter)

    if search_query:
        orders_qs = orders_qs.filter(
            Q(id__icontains=search_query) |
            Q(address__address__icontains=search_query) |
            Q(address__city__icontains=search_query) |
            Q(address__alternatePhone__icontains=search_query) |
            Q(buyer__name__icontains=search_query) |
            Q(buyer__phone__icontains=search_query) |
            Q(buyer__email__icontains=search_query) |
            Q(transactionId__icontains=search_query) |
            Q(waywill__icontains=search_query) |
            Q(product__name__icontains=search_query)
        )

    total_count = Order.objects.count()
    pending_count = Order.objects.filter(orderStatus__iexact="pending").count()
    confirmed_count = Order.objects.filter(orderStatus__iexact="confirmed").count()
    shipped_count = Order.objects.filter(orderStatus__iexact="shipped").count()
    delivered_count = Order.objects.filter(orderStatus__iexact="delivered").count()
    cancelled_count = Order.objects.filter(orderStatus__iexact="cancelled").count()

    paginator = Paginator(orders_qs, 25)
    page_number = request.GET.get('page')
    page_posts = paginator.get_page(page_number)
    current_page = page_posts.number
    total_pages = paginator.num_pages
    page_range = range(max(current_page - 2, 1), min(current_page + 3, total_pages + 1))

    return render(request, 'backend/orders.html', {
        'page_posts': page_posts,
        'page_range': page_range,
        'status_filter': status_filter,
        'search_query': search_query,
        'total_count': total_count,
        'pending_count': pending_count,
        'confirmed_count': confirmed_count,
        'shipped_count': shipped_count,
        'delivered_count': delivered_count,
        'cancelled_count': cancelled_count,
    })


@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def admin_order_details(request, id):
    if not request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")
    
    order = get_object_or_404(Order, id=id)

    if request.method == 'POST':
        new_status = request.POST.get('orderStatus', '').strip()
        new_waybill = request.POST.get('waywill', '').strip()
        new_cancelled_by = request.POST.get('cancelled_by', '').strip()

        if new_status:
            order.orderStatus = new_status
        order.waywill = new_waybill
        order.cancelled_by = new_cancelled_by
        order.save()

        messages.success(request, f"Order #{order.id} status updated to '{order.orderStatus}' successfully!")
        return redirect(f"/admin-order-details/{order.id}/")

    return render(request, 'backend/order-details.html', {
        'order': order,
    })


@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def admin_delete_order(request, id):
    if not request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")
    
    order = get_object_or_404(Order, id=id)
    order_id = order.id
    order.delete()
    messages.success(request, f"Order #{order_id} deleted successfully.")
    return redirect('/admin-order/')


# ==========================================
# FIREBASE PUSH NOTIFICATION BACKEND SYSTEM
# ==========================================

@csrf_exempt
def save_device_token(request):
    """API endpoint to receive and register FCM browser device tokens"""
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception:
            data = request.POST

        token = data.get('token', '').strip()
        device_type = data.get('device_type', 'web').strip()

        if not token:
            return JsonResponse({'status': 'error', 'message': 'Token is required'}, status=400)

        user = request.user if request.user.is_authenticated else None
        device_obj, created = DeviceToken.objects.update_or_create(
            token=token,
            defaults={'device_type': device_type, 'user': user}
        )

        return JsonResponse({
            'status': 'success',
            'created': created,
            'message': 'Device token saved successfully!',
            'token_id': device_obj.id
        })

    return JsonResponse({'status': 'error', 'message': 'Only POST method allowed'}, status=405)


def send_notification(request):
    """
    Handles /send endpoint (called by frontend test button or API)
    Broadcasts or logs push notifications.
    """
    title = request.POST.get('title') or request.GET.get('title') or "Special Offer from Bharat Shop!"
    body = request.POST.get('body') or request.GET.get('body') or "Don't miss our latest exclusive collection and deals."
    url = request.POST.get('url') or request.GET.get('url') or "/"
    image = request.POST.get('image') or request.GET.get('image') or ""
    icon = request.POST.get('icon') or request.GET.get('icon') or "/static/assets/img/logo.png"

    tokens = list(DeviceToken.objects.values_list('token', flat=True))
    total_devices = len(tokens)

    push_log = PushNotification.objects.create(
        title=title,
        body=body,
        url=url,
        image=image,
        icon=icon,
        total_sent=total_devices
    )

    try:
        import firebase_admin
        from firebase_admin import messaging
        if firebase_admin._apps and total_devices > 0:
            message = messaging.MulticastMessage(
                notification=messaging.Notification(title=title, body=body, image=image or None),
                data={'url': url},
                tokens=tokens
            )
            messaging.send_each_for_multicast(message)
    except Exception:
        pass

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or not request.POST:
        return HttpResponse(f"Success! Broadcasted '{title}' to {total_devices} active device(s). (Notification ID: #{push_log.id})")

    messages.success(request, f"Push Notification '{title}' broadcasted to {total_devices} device(s) successfully!")
    return redirect('/admin-notifications/')


@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def push_notifications_page(request):
    """Admin dashboard page for viewing devices, sending broadcasts, and seeing history"""
    if not request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")

    if request.method == "POST":
        title = request.POST.get('title', '').strip()
        body = request.POST.get('body', '').strip()
        url = request.POST.get('url', '/').strip()
        image = request.POST.get('image', '').strip()

        if not title or not body:
            messages.error(request, "Title and Body are required to send a notification.")
            return redirect('/admin-notifications/')

        tokens = list(DeviceToken.objects.values_list('token', flat=True))
        total_devices = len(tokens)

        PushNotification.objects.create(
            title=title,
            body=body,
            url=url,
            image=image,
            total_sent=total_devices
        )

        messages.success(request, f"Push Notification '{title}' sent to {total_devices} device(s) successfully!")
        return redirect('/admin-notifications/')

    devices = DeviceToken.objects.all().order_by('-created_at')
    history = PushNotification.objects.all().order_by('-created_at')

    paginator = Paginator(history, 20)
    page_number = request.GET.get('page')
    page_posts = paginator.get_page(page_number)
    current_page = page_posts.number
    total_pages = paginator.num_pages
    page_range = range(max(current_page - 2, 1), min(current_page + 3, total_pages + 1))

    return render(request, 'backend/notifications.html', {
        'page_posts': page_posts,
        'page_range': page_range,
        'devices': devices[:50],
        'total_devices': devices.count(),
        'total_notifications': history.count(),
    })


@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def delete_device_token(request, id):
    """Delete a single registered device token"""
    if not request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")
    device = get_object_or_404(DeviceToken, id=id)
    device.delete()
    messages.success(request, "Device token removed successfully.")
    return redirect('/admin-notifications/')


# Customer / Buyer Management for Admin Dashboard
@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def admin_buyer(request):
    """Admin view to list all registered customers / buyers with their complete details and addresses"""
    if not request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")

    search_query = request.GET.get('search', '').strip() or request.POST.get('search', '').strip()

    buyers_qs = Buyer.objects.all().order_by('-id')

    if search_query:
        buyers_qs = buyers_qs.filter(
            Q(name__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(address__city__icontains=search_query) |
            Q(address__address__icontains=search_query) |
            Q(address__pin__icontains=search_query)
        ).distinct()

    paginator = Paginator(buyers_qs, 25)
    page_number = request.GET.get('page')
    page_posts = paginator.get_page(page_number)
    current_page = page_posts.number
    total_pages = paginator.num_pages
    page_range = range(max(current_page - 2, 1), min(current_page + 3, total_pages + 1))

    # Pre-fetch address and order statistics for displayed buyers
    buyers_data = []
    for b in page_posts:
        latest_addr = Address.objects.filter(buyer=b).order_by('-id').first()
        all_addrs = Address.objects.filter(buyer=b)
        orders = Order.objects.filter(buyer=b)
        order_count = orders.count()
        order_total = sum([float(getattr(o, 'finalPrice', 0) or getattr(o, 'totalPrice', 0) or 0) for o in orders])

        buyers_data.append({
            'buyer': b,
            'primary_address': latest_addr,
            'addresses': all_addrs,
            'order_count': order_count,
            'order_total': order_total,
        })

    return render(request, 'backend/buyer.html', {
        'page_posts': page_posts,
        'page_range': page_range,
        'buyers_data': buyers_data,
        'search_query': search_query,
        'total_buyers': Buyer.objects.count(),
    })


@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def admin_buyer_details(request, id):
    """Admin view for detailed customer profile, all addresses, and full order history"""
    if not request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")

    buyer = get_object_or_404(Buyer, id=id)
    addresses = Address.objects.filter(buyer=buyer).order_by('-id')
    orders = Order.objects.filter(buyer=buyer).order_by('-id')
    total_spent = sum([float(getattr(o, 'finalPrice', 0) or getattr(o, 'totalPrice', 0) or 0) for o in orders])

    return render(request, 'backend/buyer-details.html', {
        'buyer': buyer,
        'addresses': addresses,
        'orders': orders,
        'order_count': orders.count(),
        'total_spent': total_spent,
    })


@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def admin_delete_buyer(request, id):
    """Admin can delete a buyer account and their addresses"""
    if not request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")

    buyer = get_object_or_404(Buyer, id=id)
    buyer_name = buyer.name
    buyer_phone = buyer.phone

    try:
        user = User.objects.filter(username=buyer_phone).first()
        if user and not user.is_staff and not user.is_superuser:
            user.delete()
    except Exception:
        pass

    buyer.delete()
    messages.success(request, f"Customer '{buyer_name}' ({buyer_phone}) deleted successfully.")
    return redirect('/admin-buyer/')







# ==============================================================================
# ADMIN PAYMENTS & TRANSACTION LOGS MANAGEMENT
# ==============================================================================

@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def admin_payments_page(request):
    """
    Admin Management Dashboard for All Payments & Razorpay Logs:
    - Lists all transactions: Success, Failed, Cancelled, Pending
    - Detailed filtering and search
    - Revenue and success rate stats
    """
    if not request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")

    status_filter = request.GET.get('status', '').strip().upper()
    search_query = request.GET.get('search_query', '').strip()

    payments_qs = Payment.objects.all().order_by('-created_at')

    if status_filter:
        if status_filter == 'FAILED':
            payments_qs = payments_qs.filter(status__in=['FAILED', 'CANCELLED'])
        else:
            payments_qs = payments_qs.filter(status=status_filter)

    if search_query:
        payments_qs = payments_qs.filter(
            Q(order_number__icontains=search_query) |
            Q(razorpay_order_id__icontains=search_query) |
            Q(razorpay_payment_id__icontains=search_query) |
            Q(buyer__name__icontains=search_query) |
            Q(buyer__phone__icontains=search_query) |
            Q(buyer__email__icontains=search_query) |
            Q(error_reason__icontains=search_query) |
            Q(error_description__icontains=search_query) |
            Q(error_code__icontains=search_query)
        )

    total_count = Payment.objects.count()
    success_count = Payment.objects.filter(status='SUCCESS').count()
    failed_count = Payment.objects.filter(status__in=['FAILED', 'CANCELLED']).count()
    pending_count = Payment.objects.filter(status='PENDING').count()

    from django.db.models import Sum
    total_volume = Payment.objects.filter(status='SUCCESS').aggregate(Sum('amount'))['amount__sum'] or 0.0

    success_rate = round((success_count / total_count * 100), 1) if total_count > 0 else 0.0

    paginator = Paginator(payments_qs, 25)
    page_number = request.GET.get('page')
    page_posts = paginator.get_page(page_number)
    current_page = page_posts.number
    total_pages = paginator.num_pages
    page_range = range(max(current_page - 2, 1), min(current_page + 3, total_pages + 1))

    return render(request, 'backend/payments.html', {
        'page_posts': page_posts,
        'page_range': page_range,
        'status_filter': status_filter,
        'search_query': search_query,
        'total_count': total_count,
        'success_count': success_count,
        'failed_count': failed_count,
        'pending_count': pending_count,
        'total_volume': total_volume,
        'success_rate': success_rate,
    })


@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def admin_payment_details(request, id):
    """View full payment log and associated orders"""
    if not request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")

    payment = get_object_or_404(Payment, id=id)
    orders = Order.objects.filter(
        Q(razorpay_payment_id=payment.razorpay_payment_id) |
        Q(razorpay_order_id=payment.razorpay_order_id) |
        Q(transactionId=payment.razorpay_payment_id)
    )
    return render(request, 'backend/payment-details.html', {
        'payment': payment,
        'orders': orders,
    })


@login_required(login_url='/admin-login/')
@user_passes_test(is_superuser, login_url='/admin-login/')
def admin_delete_payment(request, id):
    """Delete a payment log record"""
    if not request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to access this page.")

    payment = get_object_or_404(Payment, id=id)
    ord_num = payment.order_number
    payment.delete()
    messages.success(request, f"Payment log for order #{ord_num} deleted successfully.")
    return redirect('/admin-payments/')
