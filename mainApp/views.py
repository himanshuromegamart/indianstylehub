from django.shortcuts import render
import requests
from django.http import HttpResponse,HttpResponseForbidden
from .models import *
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.db.models import Q
import os


# Create your views here.
def home_page(request):
    supercategories=Supercategory.objects.all()[:7]
    maincategories=Maincategory.objects.all()
    categories=Category.objects.all()
    subcategories=Subcategory.objects.all()
    filteredProduct=Product.objects.all().order_by('id').reverse()[:12]
    brands=Brand.objects.all()
    slider=Slider.objects.all()
    products=Product.objects.all().order_by('id').reverse()[:6]
    blogs=Blog.objects.all().order_by('-id')[:3]
    gallery=Gallery.objects.all().order_by('-id')[:10]
    context = {
        'supercategories': supercategories,'maincategories': maincategories, 'categories': categories, 'subcategories': subcategories,
        'products': products,'slider':slider,'filteredProduct':filteredProduct,'blogs':blogs,'brands':brands,'gallery':gallery
    }
    return render(request,'front/index.html',context)




def dynamic_category_view(request, supercat=None, mcat=None, cat=None, scat=None):
    """
    Handles 4-tier category hierarchy:
    Level 1: /<supercategory>/                          e.g. /women/ or /men/ or /kids/
    Level 2: /<supercategory>/<maincategory>/           e.g. /women/footwear/
    Level 3: /<supercategory>/<maincategory>/<category>/ e.g. /women/footwear/shoes/
    Level 4: /<supercategory>/<maincategory>/<category>/<subcategory>/ e.g. /women/footwear/shoes/sports-shoes/

    FALLBACK RULE:
    If category or subcategory is unavailable or has no products,
    it automatically falls back to showing products of the parent category/maincategory/supercategory
    without error.
    """
    SLUG_ALIASES = {
        'female': 'women',
        'male': 'men',
        'kid': 'kids',
        'girls': 'kids',
        'boys': 'kids',
    }

    raw_supercat = supercat
    if supercat and supercat.lower() in SLUG_ALIASES:
        supercat = SLUG_ALIASES[supercat.lower()]

    supercategory_obj = None
    maincategory_obj = None
    category_obj = None
    subcategory_obj = None

    breadcrumbs = [{'name': 'Home', 'url': '/'}]
    current_title = "Shop"
    current_description = ""
    child_items = []

    # 1. Determine Hierarchy Level
    if supercat == 'all':
        products = Product.objects.all().order_by('-id')
        current_title = "All Products"
        breadcrumbs.append({'name': 'All Products', 'url': '/all/'})
        child_items = [{'name': s.name, 'image': s.image, 'url': f"/{s.slug}/"} for s in Supercategory.objects.filter(slug__in=['women', 'men', 'kids'])]

    elif supercat and Supercategory.objects.filter(slug__iexact=supercat).exists():
        supercategory_obj = Supercategory.objects.filter(slug__iexact=supercat).first()
        current_title = supercategory_obj.name
        breadcrumbs.append({'name': supercategory_obj.name, 'url': f"/{supercategory_obj.slug}/"})

        if mcat:
            maincategory_obj = Maincategory.objects.filter(slug__iexact=mcat).first()
            if maincategory_obj:
                current_title = f"{supercategory_obj.name} - {maincategory_obj.name}"
                current_description = maincategory_obj.description or ""
                breadcrumbs.append({'name': maincategory_obj.name, 'url': f"/{supercategory_obj.slug}/{maincategory_obj.slug}/"})

        if cat:
            if maincategory_obj:
                category_obj = Category.objects.filter(maincategory=maincategory_obj, slug__iexact=cat).first()
            if not category_obj:
                category_obj = Category.objects.filter(slug__iexact=cat).first()
            if category_obj:
                current_title = f"{category_obj.name}"
                current_description = category_obj.description or current_description
                breadcrumbs.append({'name': category_obj.name, 'url': f"/{supercategory_obj.slug}/{maincategory_obj.slug if maincategory_obj else 'all'}/{category_obj.slug}/"})

        if scat:
            if category_obj:
                subcategory_obj = Subcategory.objects.filter(category=category_obj, slug__iexact=scat).first()
            if not subcategory_obj:
                subcategory_obj = Subcategory.objects.filter(slug__iexact=scat).first()
            if subcategory_obj:
                current_title = f"{subcategory_obj.name}"
                current_description = subcategory_obj.description or current_description
                breadcrumbs.append({'name': subcategory_obj.name, 'url': f"/{supercategory_obj.slug}/{maincategory_obj.slug if maincategory_obj else 'all'}/{category_obj.slug if category_obj else 'all'}/{subcategory_obj.slug}/"})

        # Determine Products & Child Items based on hierarchy depth:
        if subcategory_obj:
            products = Product.objects.filter(subcategory=subcategory_obj)
            if not products.exists() and category_obj:
                products = Product.objects.filter(category=category_obj)
            if not products.exists() and maincategory_obj:
                products = Product.objects.filter(maincategory=maincategory_obj)
            if not products.exists():
                products = Product.objects.filter(Q(supercategory=supercategory_obj) | Q(maincategory__supercategory=supercategory_obj))
            child_items = []

        elif category_obj:
            products = Product.objects.filter(category=category_obj)
            if not products.exists() and maincategory_obj:
                products = Product.objects.filter(maincategory=maincategory_obj)
            if not products.exists():
                products = Product.objects.filter(Q(supercategory=supercategory_obj) | Q(maincategory__supercategory=supercategory_obj))
            scats = Subcategory.objects.filter(category=category_obj)
            child_items = [{
                'name': s.name,
                'image': s.image or (category_obj.image if category_obj else ''),
                'url': f"/{supercategory_obj.slug}/{maincategory_obj.slug if maincategory_obj else 'all'}/{category_obj.slug}/{s.slug}/"
            } for s in scats]

        elif maincategory_obj:
            products = Product.objects.filter(maincategory=maincategory_obj)
            if not products.exists():
                products = Product.objects.filter(Q(supercategory=supercategory_obj) | Q(maincategory__supercategory=supercategory_obj))
            cats = Category.objects.filter(maincategory=maincategory_obj)
            child_items = [{
                'name': c.name,
                'image': c.image or '',
                'url': f"/{supercategory_obj.slug}/{maincategory_obj.slug}/{c.slug}/"
            } for c in cats]

        else:
            # Supercategory only
            products = Product.objects.filter(
                Q(supercategory=supercategory_obj) | 
                Q(maincategory__supercategory=supercategory_obj) | 
                Q(offers=supercategory_obj)
            )
            mcats = Maincategory.objects.filter(supercategory=supercategory_obj)
            if not mcats.exists():
                mcats = Maincategory.objects.all()
            child_items = [{
                'name': m.name,
                'image': m.image or '',
                'url': f"/{supercategory_obj.slug}/{m.slug}/"
            } for m in mcats]

    elif supercat and Maincategory.objects.filter(slug__iexact=supercat).exists():
        # Legacy Maincategory URL
        maincategory_obj = Maincategory.objects.filter(slug__iexact=supercat).first()
        current_title = maincategory_obj.name
        current_description = maincategory_obj.description or ""
        breadcrumbs.append({'name': maincategory_obj.name, 'url': f"/{maincategory_obj.slug}/"})

        if mcat:
            category_obj = Category.objects.filter(maincategory=maincategory_obj, slug__iexact=mcat).first() or Category.objects.filter(slug__iexact=mcat).first()
            if category_obj:
                current_title = f"{maincategory_obj.name} - {category_obj.name}"
                breadcrumbs.append({'name': category_obj.name, 'url': f"/{maincategory_obj.slug}/{category_obj.slug}/"})

        if cat:
            subcategory_obj = Subcategory.objects.filter(category=category_obj, slug__iexact=cat).first() or Subcategory.objects.filter(slug__iexact=cat).first()
            if subcategory_obj:
                current_title = f"{category_obj.name if category_obj else maincategory_obj.name} - {subcategory_obj.name}"
                breadcrumbs.append({'name': subcategory_obj.name, 'url': f"/{maincategory_obj.slug}/{category_obj.slug if category_obj else 'all'}/{subcategory_obj.slug}/"})

        if subcategory_obj:
            products = Product.objects.filter(subcategory=subcategory_obj)
            if not products.exists() and category_obj:
                products = Product.objects.filter(category=category_obj)
            if not products.exists():
                products = Product.objects.filter(maincategory=maincategory_obj)
            child_items = []
        elif category_obj:
            products = Product.objects.filter(category=category_obj)
            if not products.exists():
                products = Product.objects.filter(maincategory=maincategory_obj)
            scats = Subcategory.objects.filter(category=category_obj)
            child_items = [{
                'name': s.name,
                'image': s.image or '',
                'url': f"/{maincategory_obj.slug}/{category_obj.slug}/{s.slug}/"
            } for s in scats]
        else:
            products = Product.objects.filter(maincategory=maincategory_obj)
            cats = Category.objects.filter(maincategory=maincategory_obj)
            child_items = [{
                'name': c.name,
                'image': c.image or '',
                'url': f"/{maincategory_obj.slug}/{c.slug}/"
            } for c in cats]

    else:
        # Fallback if unknown slug
        products = Product.objects.filter(name__icontains=raw_supercat or '')
        if not products.exists():
            products = Product.objects.all()
        current_title = raw_supercat.title() if raw_supercat else "Products"

    # Facet Filters
    selected_maincategory = request.GET.get('maincategory')
    selected_categories = request.GET.getlist('category[]')
    selected_brands = request.GET.getlist('brand[]')
    selected_colors = request.GET.getlist('color[]')
    selected_size = request.GET.get('size')
    selected_rating = request.GET.get('rating')
    selected_min_price = request.GET.get('min_price')
    selected_max_price = request.GET.get('max_price')

    if selected_maincategory and selected_maincategory.isdigit():
        products = products.filter(maincategory__id=int(selected_maincategory))

    selected_categories_clean = [c for c in selected_categories if c.isdigit()]
    if selected_categories_clean:
        products = products.filter(category__id__in=selected_categories_clean)

    selected_brands_clean = [b for b in selected_brands if b.isdigit()]
    if selected_brands_clean:
        products = products.filter(brand__id__in=selected_brands_clean)

    if selected_colors:
        products = products.filter(color__in=selected_colors)

    if selected_size:
        products = products.filter(size=selected_size)

    if selected_rating and selected_rating.isdigit():
        products = products.filter(reviews__gte=int(selected_rating))

    if selected_min_price and selected_max_price:
        try:
            products = products.filter(price__gte=float(selected_min_price), price__lte=float(selected_max_price))
        except ValueError:
            pass

    products = products.distinct().order_by('-id')

    # Pagination
    paginator = Paginator(products, 30)
    page_number = request.GET.get('page')
    page_posts = paginator.get_page(page_number)
    current_page = page_posts.number
    total_pages = paginator.num_pages
    page_range = range(max(current_page - 2, 1), min(current_page + 3, total_pages + 1))

    maincategories = Maincategory.objects.all()
    categories = Category.objects.filter(maincategory=maincategory_obj) if maincategory_obj else Category.objects.all()
    brands = Brand.objects.all()
    colors = Color.objects.all()
    sizes = Size.objects.all()
    subcategories = Subcategory.objects.filter(category=category_obj) if category_obj else Subcategory.objects.all()

    context = {
        'page_posts': page_posts,
        'page_range': page_range,
        'maincategories': maincategories,
        'categories': categories,
        'subcategories': subcategories,
        'brands': brands,
        'colors': colors,
        'sizes': sizes,
        'maincategory': maincategory_obj,
        'supercategory': supercategory_obj,
        'category': category_obj,
        'subcategory': subcategory_obj,
        'child_items': child_items,
        'breadcrumbs': breadcrumbs,
        'current_title': current_title,
        'ops': maincategory_obj or supercategory_obj or category_obj or subcategory_obj,
        'title': current_title,
        'description': current_description,
        'selected_maincategories': selected_maincategory,
        'selected_categories': selected_categories,
        'selected_brands': selected_brands,
        'selected_colors': selected_colors,
        'selected_size': selected_size,
        'selected_rating': selected_rating,
    }
    return render(request, 'front/products.html', context)


def category_by_maincategory(request, ops):
    return dynamic_category_view(request, supercat=ops)


def subcategory_by_category(request, mcat, cat):
    return dynamic_category_view(request, supercat=mcat, mcat=cat)



def web_filter(request):
    maincategories = Maincategory.objects.all()
    categories = Category.objects.all()
    subcategories = Subcategory.objects.all()
    brands = Brand.objects.all()
    size = Size.objects.all()
    color = Color.objects.all()
    filteredProduct=Product.objects.all().order_by('id').reverse()[:6]
    data=Product.objects.all()

    # Apply filters based on selected checkboxes
    selected_maincategories = request.GET.get('maincategory')
    selected_categories = request.GET.getlist('category[]')
    selected_subcategories = request.GET.getlist('subcategory[]')
    selected_brands = request.GET.getlist('brand[]')
    selected_colors = request.GET.getlist('color[]')
    selected_size = request.GET.get('size')
    selected_rating = request.GET.get('rating')
    selected_min_price = request.GET.get('min_price')
    selected_max_price = request.GET.get('max_price')

    # Validate and filter only numeric values
    selected_categories = [cat for cat in selected_categories if cat.isdigit()]
    selected_subcategories = [sub for sub in selected_subcategories if sub.isdigit()]
    selected_brands = [brand for brand in selected_brands if brand.isdigit()]
    

    if selected_maincategories:
        categories = Category.objects.filter(maincategory=Maincategory.objects.get(id=selected_maincategories))
        data = data.filter(maincategory__id=selected_maincategories)
    if selected_categories:
        data = data.filter(category__id__in=selected_categories)
    if selected_subcategories:
        data = data.filter(subcategory__id__in=selected_subcategories)
    if selected_brands:
        data = data.filter(brand__id__in=selected_brands)
    if selected_colors:
        data = data.filter(color__in=selected_colors)
    if selected_size:
        data = data.filter(size=selected_size)
    if selected_rating:
        data = data.filter(reviews__gte=selected_rating)
    try:
        if selected_min_price and selected_max_price:
            min_price = float(selected_min_price)
            max_price = float(selected_max_price)
            data = data.filter(price__gte=min_price, price__lte=max_price)
        elif selected_min_price:
            min_price = float(selected_min_price)
            data = data.filter(price__gte=min_price)
        elif selected_max_price:
            max_price = float(selected_max_price)
            data = data.filter(price__lte=max_price)
    except ValueError:
        # Handle invalid price values (e.g., non-numeric input)
        messages.error(request, "Invalid price range. Please enter valid numbers.")
        data = Product.objects.none()  # Return an empty queryset if invalid



    # Pagination
    paginator = Paginator(data, 30)
    page_number = request.GET.get('page')
    page_posts = paginator.get_page(page_number)
    current_page = page_posts.number
    total_pages = paginator.num_pages
    page_range = range(max(current_page - 2, 1), min(current_page + 3, total_pages + 1))

    return render(request, 'front/products.html', {
        'page_posts': page_posts,
        'page_range': page_range,
        'maincategories': maincategories,
        'categories': categories,
        'subcategories': subcategories,
        'brands': brands,
        'sizes': size,
        'colors': color,
        'selected_maincategories': selected_maincategories, 
        'selected_categories': selected_categories,
        'selected_subcategories': selected_subcategories,
        'selected_brands': selected_brands, 
        'selected_colors':selected_colors,
        'selected_size':selected_size,
        'selected_rating':selected_rating,
        'filteredProduct':filteredProduct,
    })



def category_page(request,cat):
    maincategories=Maincategory.objects.all()
    print("Maincategory is :",maincategories)
    categories=Category.objects.all()
    subcategories=Subcategory.objects.all()
    brands=Brand.objects.all()
    size=Size.objects.all()
    color=Color.objects.all()
    try:
        # Fetch products with offers
        if cat == "all":
            data = Product.objects.all().order_by('-id')  # Filter products with non-empty offers
        else:
            # Get the Supercategory object
            data = Product.objects.filter(category=Category.objects.get(slug=cat))
        paginator = Paginator(data, 100)  # Show 10 posts per page
        page_number = request.GET.get('page')
        page_posts = paginator.get_page(page_number)
        current_page = page_posts.number
        total_pages = paginator.num_pages
        page_range = range(max(current_page - 2, 1), min(current_page + 3, total_pages + 1))
    except Exception as e:
        print(f"Error occurred: {e}")  # Log the error for debugging
        data = Product.objects.none()  # Return an empty queryset
        
    return render(request, 'front/products.html', {'page_posts':page_posts,'page_range': page_range,'maincategories':maincategories,'categories':categories,'subcategories':subcategories,'brands':brands,'size':size,'color':color})


def product_by_maincategory_category_subcategiry(request, mcat, cat, scat):
    return dynamic_category_view(request, supercat=mcat, mcat=cat, cat=scat)


def men_home_page(request):
    return dynamic_category_view(request, supercat='men')


def kid_home_page(request):
    return dynamic_category_view(request, supercat='kids')

def brand_page(request):
    return render(request,'front/brands.html')

def product_page(request,cat):
    try:
       data=Product.objects.filter(cateory=Category.objects.get(slug=cat))
    except:
        data=''
    return render(request,'front/products.html',{'data':data})


from django.db.models import Min
from django.shortcuts import render, get_object_or_404

def product_detail(request, name, id):
    maincategories=Maincategory.objects.all()
    categories=Category.objects.all()
    subcategories=Subcategory.objects.all()
    brands=Brand.objects.all()
    filteredProduct=Product.objects.all().order_by('id').reverse()[:12]
    try:
        data = get_object_or_404(Product, id=id)

        # Get unique colors for the same SKU & pick the first occurrence
        unique_colors = Product.objects.filter(sku=data.sku).values('color').annotate(id=Min('id'))
        skuProductByColor = Product.objects.filter(id__in=[item['id'] for item in unique_colors])

        # Get unique sizes for the selected color & pick the first occurrence
        unique_sizes = Product.objects.filter(sku=data.sku, color=data.color).values('size').annotate(id=Min('id'))
        skuProductBySize = Product.objects.filter(id__in=[item['id'] for item in unique_sizes])

        # Get similar products
        similarProduct = Product.objects.filter(category=data.category).exclude(id=data.id)

    except:
        return render(request, 'front/error.html')

    return render(request, 'front/product-details.html', {
        'data': data,
        'skuProductByColor': skuProductByColor,
        'skuProductBySize': skuProductBySize,
        'similarProduct': similarProduct,
        'carts': request.session.get('cart', {}),
        'maincategories': maincategories, 
        'categories': categories, 
        'subcategories': subcategories,
        'filteredProduct': filteredProduct,
        'brands': brands,

    })


from django.shortcuts import get_object_or_404
from django.http import JsonResponse

def add_to_cart(request):
    if request.method == "POST":
        product_id = request.POST.get('productId')

        # Handle invalid or missing product ID
        if not product_id:
            return JsonResponse({'error': 'Product ID is required'}, status=400)

        try:
            quantity = int(request.POST.get('quantity', 1))
            if quantity < 1:
                raise ValueError("Quantity must be at least 1")
        except ValueError:
            return JsonResponse({'error': 'Invalid quantity'}, status=400)

        product = get_object_or_404(Product, id=product_id)

        # Initialize session cart if not exists
        if 'cart' not in request.session:
            request.session['cart'] = {}

        cart = request.session['cart']

        # Check if product is already in cart
        if str(product_id) in cart:
            cart[str(product_id)]['quantity'] += quantity  # Increment quantity
        else:
            cart[str(product_id)] = {
                'name': product.name,
                'price': float(product.price),
                'quantity': quantity,
                'image': getattr(product, 'image1', ''),  # Ensure safe access
                'size': str(product.size) if product.size else 'N/A',
                'color': str(product.color) if product.color else 'N/A'
            }
            print("Cart Data is :",cart)

        # Save updated cart back to session
        request.session['cart'] = cart
        request.session.modified = True

        return JsonResponse({'message': 'Product added to cart', 'cart': cart})

    return JsonResponse({'error': 'Invalid request'}, status=400)

from django.http import JsonResponse

def get_cart_data(request):
    cart = request.session.get('cart', {})  # Get cart data, default to empty dict
    print("Cart is called...",cart)
    return JsonResponse({'cart': cart})  # Ensure it's a JsonResponse


from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import Product

def update_cart(request):
    if request.method == "POST":
        product_id = request.POST.get('id')
        change = int(request.POST.get('change', 0))
        
        cart = request.session.get('cart', {})
        if str(product_id) in cart:
            cart[str(product_id)]['quantity'] += change
            if cart[str(product_id)]['quantity'] <= 0:
                del cart[str(product_id)]

        request.session['cart'] = cart
        request.session.modified = True
        return JsonResponse({'message': 'Cart updated'})

    return JsonResponse({'error': 'Invalid request'}, status=400)

def remove_from_cart(request):
    if request.method == "POST":
        product_id = request.POST.get('id')

        cart = request.session.get('cart', {})
        if str(product_id) in cart:
            del cart[str(product_id)]

        request.session['cart'] = cart
        request.session.modified = True
        return JsonResponse({'message': 'Product removed'})

    return JsonResponse({'error': 'Invalid request'}, status=400)

from django.template.loader import render_to_string



def cart_page(request):
    cart = request.session.get('cart', {})  # Get cart data, default to empty dict
    print("Cart is called...",cart)
    return render(request,'front/cart.html',{'cart':cart})

def wishlist_page(request):
    return render(request,'front/wishlist.html')

def compare_page(request):
    return render(request,'front/compare.html')

def checkout_page(request):
    return render(request,'front/checkout.html')

def blog_page(request):
    maincategories = Maincategory.objects.all()
    categories = Category.objects.all()
    subcategories = Subcategory.objects.all()
    brands = Brand.objects.all()
    size = Size.objects.all()
    color = Color.objects.all()
    filteredProduct=Product.objects.all().order_by('id').reverse()[:12]


    blogs=Blog.objects.all()
    paginator = Paginator(blogs, 100)
    page_number = request.GET.get('page')
    page_posts = paginator.get_page(page_number)
    context = {
        'page_posts': page_posts,
        'page_range': range(max(page_posts.number - 2, 1), min(page_posts.number + 3, paginator.num_pages + 1)),
        'total_pages': paginator.num_pages,
        'maincategories': maincategories,
        'categories': categories,
        'subcategories': subcategories,
        'brands': brands,
        'size': size,
        'color': color,
        'filteredProduct': filteredProduct,
    }

    return render(request,'front/blog.html',context)


def blog_details_page(request,ops):
    maincategories = Maincategory.objects.all()
    categories = Category.objects.all()
    subcategories = Subcategory.objects.all()
    brands = Brand.objects.all()
    size = Size.objects.all()
    color = Color.objects.all()
    filteredProduct=Product.objects.all().order_by('id').reverse()[:12]

    try:
        data=Blog.objects.get(slug=ops)
        blogs=Blog.objects.all().exclude(id=data.id).order_by('-id')[:10]
    except:
        return render(request,'front/error.html')
    return render(request,'front/blog-details.html',{
        'data':data,
        'blogs':blogs,
        'maincategories': maincategories,
        'categories': categories,
        'subcategories': subcategories,
        'brands': brands,
        'size': size,
        'color': color,
        'filteredProduct': filteredProduct
        })

def about_us(request):
    maincategories = Maincategory.objects.all()
    categories = Category.objects.all()
    subcategories = Subcategory.objects.all()
    brands = Brand.objects.all()
    size = Size.objects.all()
    color = Color.objects.all()
    filteredProduct=Product.objects.all().order_by('id').reverse()[:12]
    return render(request,'front/about.html',{
        'maincategories': maincategories,
        'categories': categories,
        'subcategories': subcategories,
        'brands': brands,
        'size': size,
        'color': color,
        'filteredProduct': filteredProduct,})

def contact_page(request):
    maincategories = Maincategory.objects.all()
    categories = Category.objects.all()
    subcategories = Subcategory.objects.all()
    brands = Brand.objects.all()
    size = Size.objects.all()
    color = Color.objects.all()
    filteredProduct=Product.objects.all().order_by('id').reverse()[:12]
    msg=''
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        message = request.POST.get('message')
        contact=Contact(name=name, email=email, phone=phone, message=message)
        contact.save()
        msg='Your message has been sent successfully. We will get back to you soon.'

    return render(request,'front/contact.html',{'maincategories': maincategories,
        'categories': categories,
        'subcategories': subcategories,
        'brands': brands,
        'size': size,
        'color': color,
        'filteredProduct': filteredProduct,
        'msg':msg})



def faq(request):
    maincategories = Maincategory.objects.all()
    categories = Category.objects.all()
    subcategories = Subcategory.objects.all()
    brands = Brand.objects.all()
    size = Size.objects.all()
    color = Color.objects.all()
    filteredProduct=Product.objects.all().order_by('id').reverse()[:12]
    return render(request,'front/faq.html',{'maincategories': maincategories,
        'categories': categories,
        'subcategories': subcategories,
        'brands': brands,
        'size': size,
        'color': color,
        'filteredProduct': filteredProduct,})


#User dashboard

def login_page(request):
    maincategories = Maincategory.objects.all()
    categories = Category.objects.all()
    subcategories = Subcategory.objects.all()
    brands = Brand.objects.all()
    size = Size.objects.all()
    color = Color.objects.all()
    filteredProduct=Product.objects.all().order_by('id').reverse()[:12]
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        
        # Authenticate user
        user = authenticate(username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Redirect based on user type or 'next' parameter
            next_url = request.GET.get("next")
            if next_url:
                return redirect(next_url)
            elif user.is_superuser:
                return redirect("/admin-dashboard")  # Use reverse for named URL
            else:
                return redirect("/my-account") # Use reverse for named URL
        else:
            messages.error(request, "Invalid username or password!")

    return render(request, "front/login.html",{'maincategories': maincategories,
        'categories': categories,
        'subcategories': subcategories,
        'brands': brands,
        'size': size,
        'color': color,
        'filteredProduct': filteredProduct,})



def logout_page(request):
    logout(request)
    return redirect("/login")

def register(request):
    maincategories = Maincategory.objects.all()
    categories = Category.objects.all()
    subcategories = Subcategory.objects.all()
    brands = Brand.objects.all()
    size = Size.objects.all()
    color = Color.objects.all()
    filteredProduct=Product.objects.all().order_by('id').reverse()[:12]
    if request.method == "POST":
        # Get the form data
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Check if the user already exists
        if User.objects.filter(username=phone).exists():
            messages.error(request, "Phone number already exists.")
            return render(request, 'front/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return render(request, 'front/register.html')
        
        # Hash the password
        hashed_password = make_password(password)
        
        # Create a new buyer object
        buyer = Buyer(name=name, phone=phone, email=email, password=hashed_password)
        buyer.save()

        # Split the name into first and last names
        first_name, last_name = name.split(" ", 1) if " " in name else (name, "")
        
        # Create a new user object
        user = User(username=phone, email=email, first_name=first_name, last_name=last_name, password=hashed_password)
        user.save()

        # Authenticate and log the user in
        user = authenticate(username=phone, password=password)
        
        if user is not None:
            if user.is_superuser:
                login(request, user)
                return redirect("/admin-dashboard")
            else:
               return redirect('/my-account')
        else:
            messages.error(request, "Invalid Username or Password!")

          # Redirect to a page after successful login (e.g., home page)
    
    return render(request, 'front/register.html',{'maincategories': maincategories,
        'categories': categories,
        'subcategories': subcategories,
        'brands': brands,
        'size': size,
        'color': color,
        'filteredProduct': filteredProduct,})



@login_required(login_url="/login")
def my_account(request):
    print("User: ",request.user.username)
    if not Buyer.objects.filter(phone=request.user.username):
        return HttpResponseForbidden("You don't have permission to access this page.")
    
    buyer=Buyer.objects.get(phone=request.user.username)
    return render(request,'front/my-account.html',{'buyer':buyer})


def my_account_address(request):
    return render(request,'front/my-account-address.html')

def my_account_edit(request):
    return render(request,'front/my-account-edit.html')

@login_required(login_url="/login")
def my_account_order(request):
    return render(request,'front/my-account-orders.html')

def my_account_order_details(request):
    return render(request,'front/my-account-orders-details.html')

def order_tracking(request):
    return render(request,'front/order-tracking.html')

def payment_confirmation(request):
    return render(request,'front/payment-confirmation.html')

def payment_failure(request):
    return render(request,'front/payment-failure.html')


def search_product(request):
    maincategories = Maincategory.objects.all()
    categories = Category.objects.all()
    subcategories = Subcategory.objects.all()
    brands = Brand.objects.all()
    size = Size.objects.all()
    color = Color.objects.all()
    filteredProduct=Product.objects.all().order_by('id').reverse()[:12]

    query = request.GET.get('query', '').strip()  # Get the query from GET request

    # Filter products based on the search query
    if query:
        data = Product.objects.filter(
            Q(name__icontains=query) |  # Search by name
            Q(description__icontains=query) |  # Search by description
            Q(category__name__icontains=query) |  # Search by category name
            Q(subcategory__name__icontains=query)  # Search by subcategory name
        ).distinct()  # Avoid duplicate results if multiple fields match
    else:
        data = Product.objects.none()  # If no query, return empty results

    # Pagination
    paginator = Paginator(data, 100)
    page_number = request.GET.get('page')
    page_posts = paginator.get_page(page_number)
    current_page = page_posts.number
    total_pages = paginator.num_pages
    page_range = range(max(current_page - 2, 1), min(current_page + 3, total_pages + 1))

    return render(request, 'front/products.html', {
        'page_posts': page_posts,
        'page_range': page_range,
        'maincategories': maincategories,
        'categories': categories,
        'subcategories': subcategories,
        'brands': brands,
        'size': size,
        'color': color,
        'query': query,  # Pass the query to the template
        'filteredProduct': filteredProduct,
    })


from django.http import HttpResponse
from django.template.loader import render_to_string

def sitemap_page(request):
    products = Product.objects.all().order_by('-id')
    xml_content = render_to_string('front/sitemap.xml', {'products': products})
    return HttpResponse(xml_content, content_type='application/xml')


def robots_txt(request):
    return render(request, 'front/robots.txt')



from django.core.validators import validate_email
from django.core.exceptions import ValidationError

def add_enquiry(request):
    if request.method == "POST":
        productId = request.POST.get('productId')
        print("Product Id :", productId)
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        address = request.POST.get('address', '').strip()
        pincode = request.POST.get('pincode', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        try:
            product = Product.objects.get(id=productId)
        except Product.DoesNotExist:
            return HttpResponse("Invalid product.")
        print(f"""
            Product:{product}
            Name,{name}
            Phone,{phone}
            Email, {email}
            PinCode: {pincode}
            Address, {address}
            city, {city}
            state, {state}
            
        """)

        # Basic validation
        if not all([productId, name, phone, email, address, pincode, city, state]):
            return HttpResponse("All fields are required.")

        if not phone.isdigit() or len(phone) != 10:
            return HttpResponse("Enter a valid 10-digit phone number.")

        if not pincode.isdigit() or len(pincode) != 6:
            return HttpResponse("Enter a valid 6-digit pincode.")

        try:
            validate_email(email)
        except ValidationError:
            return HttpResponse("Invalid email address.")

        try:
            Enquiry.objects.create(
                product=product,
                name=name,
                phone=phone,
                email=email,
                address=address,
                pincode=pincode,  # fixed field name
                city=city,
                state=state
            )
            return render(request, 'front/confirmation.html')
        except Exception as e:
            return HttpResponse("Please try after sometime...")

    return HttpResponse("Invalid request method.")
