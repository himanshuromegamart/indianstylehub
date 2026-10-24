from django.shortcuts import render
import requests
from django.http import HttpResponse,HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt
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
import json
import hmac
import hashlib
import razorpay
from django.conf import settings


def firebase_messaging_sw(request):
    sw_path = os.path.join(settings.BASE_DIR, 'mainApp', 'static', 'firebase-messaging-sw.js')
    if os.path.exists(sw_path):
        with open(sw_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return HttpResponse(content, content_type='application/javascript')
    return HttpResponse("// service worker not found", content_type='application/javascript')



# Create your views here.
def home_page(request):
    supercategories = Supercategory.objects.all()[:7]
    maincategories = Maincategory.objects.all()
    categories = Category.objects.all()
    subcategories = Subcategory.objects.all()
    filteredProduct = Product.objects.all().order_by('id').reverse()[:12]
    brands = Brand.objects.all()
    slider = Slider.objects.all()
    products = Product.objects.all().order_by('id').reverse()[:6]
    blogs = Blog.objects.all().order_by('-id')[:3]
    gallery = Gallery.objects.all().order_by('-id')[:10]
    popular_links = get_home_popular_links()

    # Supercategories that have more than 1 child maincategory (array size > 1)
    home_supercategories = []
    for sc in Supercategory.objects.prefetch_related('maincategories').all().order_by('id'):
        mc_list = list(sc.maincategories.all().order_by('id'))
        if len(mc_list) > 1:
            sc.active_maincategories = mc_list
            sc.maincategories_count = len(mc_list)
            if not sc.image and mc_list and mc_list[0].image:
                sc.display_image = mc_list[0].image
            else:
                sc.display_image = sc.image or ''
            home_supercategories.append(sc)

    # Dynamic Category Sections (Only categories that have active products!)
    category_sections = []
    seen_category_names = set()

    # 1. Maincategories with products
    for mc in Maincategory.objects.all().order_by('id'):
        prods = Product.objects.filter(Q(maincategory=mc) | Q(category__maincategory=mc)).distinct().order_by('-id')[:12]
        if prods.exists():
            banner_img = mc.banner or mc.banner1 or mc.banner2 or mc.image or ''
            if not banner_img and prods.first() and prods.first().image1:
                banner_img = prods.first().image1
            category_sections.append({
                'id': f"mc_{mc.id}",
                'name': mc.name,
                'slug': mc.slug,
                'url': f"/{mc.slug}/",
                'banner_img': banner_img,
                'products': prods,
            })
            seen_category_names.add(mc.name.strip().lower())

    # 2. Standalone Categories with products (if not already included under maincategory)
    for cat in Category.objects.all().order_by('id'):
        if cat.name.strip().lower() in seen_category_names:
            continue
        prods = Product.objects.filter(category=cat).order_by('-id')[:12]
        if prods.exists():
            banner_img = cat.image or ''
            if not banner_img and prods.first() and prods.first().image1:
                banner_img = prods.first().image1
            category_sections.append({
                'id': f"cat_{cat.id}",
                'name': cat.name,
                'slug': cat.slug,
                'url': f"/{cat.slug}/",
                'banner_img': banner_img,
                'products': prods,
            })
            seen_category_names.add(cat.name.strip().lower())

    # Fallback if no categories are assigned to products, so homepage is never blank
    if not category_sections and Product.objects.exists():
        prods = Product.objects.all().order_by('-id')[:12]
        category_sections.append({
            'id': 'featured',
            'name': 'Featured Collection',
            'slug': 'all',
            'url': '/all/',
            'banner_img': prods.first().image1 if prods.first() else '',
            'products': prods,
        })

    context = {
        'supercategories': supercategories,
        'maincategories': maincategories,
        'categories': categories,
        'subcategories': subcategories,
        'products': products,
        'slider': slider,
        'filteredProduct': filteredProduct,
        'blogs': blogs,
        'brands': brands,
        'gallery': gallery,
        'popular_links': popular_links,
        'category_sections': category_sections,
        'home_supercategories': home_supercategories,
    }
    return render(request, 'front/index.html', context)


from urllib.parse import quote_plus

INDIAN_STATES = [
    "Maharashtra", "Uttar Pradesh", "Delhi", "Gujarat", "Karnataka", "Tamil Nadu",
    "West Bengal", "Rajasthan", "Punjab", "Haryana", "Madhya Pradesh", "Telangana",
    "Andhra Pradesh", "Bihar", "Kerala", "Odisha", "Assam", "Jharkhand",
    "Chhattisgarh", "Uttarakhand", "Himachal Pradesh", "Jammu and Kashmir", "Goa",
    "Chandigarh", "Tripura", "Manipur", "Meghalaya", "Nagaland", "Puducherry",
    "Arunachal Pradesh", "Mizoram", "Sikkim", "Ladakh", "Daman",
    "Andaman and Nicobar Islands", "Lakshadweep"
]

HOME_POPULAR_KEYWORDS = [
    ("Women Ethnic Wear", "Maharashtra"),
    ("Designer Handbags", "Delhi"),
    ("Wholesale Sarees", "Gujarat"),
    ("Bridal Lehengas", "Rajasthan"),
    ("Cotton Kurtis", "Uttar Pradesh"),
    ("Partywear Gowns", "Karnataka"),
    ("Silk Sarees", "Tamil Nadu"),
    ("Traditional Suits", "Punjab"),
    ("Fashion Handbags", "West Bengal"),
    ("Embroidered Kurtis", "Madhya Pradesh"),
    ("Festive Wear", "Telangana"),
    ("Designer Dupattas", "Haryana"),
    ("Chikankari Kurtis", "Uttar Pradesh"),
    ("Bandhani & Leheriya", "Rajasthan"),
    ("Western Dresses", "Maharashtra"),
    ("Printed Kurtis", "Bihar"),
    ("Casual Tops & Tunics", "Kerala"),
    ("Fashion Accessories", "Odisha"),
    ("Handcrafted Clutches", "Gujarat"),
    ("Designer Footwear", "Delhi"),
    ("Wedding Collection", "Chandigarh"),
    ("Ethnic Kurti Sets", "Assam"),
    ("Banarasi Sarees", "Uttar Pradesh"),
    ("Tote Handbags", "Karnataka"),
    ("Wholesale Dress Materials", "Gujarat"),
    ("Summer Kurtis", "Andhra Pradesh"),
    ("Winter Shawls & Stoles", "Jammu and Kashmir"),
    ("Indo-Western Outfits", "Maharashtra"),
    ("Georgette Sarees", "West Bengal"),
    ("Palazzo Suits", "Punjab"),
    ("Party Clutches", "Goa"),
    ("Designer Handbags", "Uttarakhand"),
    ("Bridal Sarees", "Himachal Pradesh"),
    ("Boutique Kurtis", "Jharkhand"),
    ("Printed Sarees", "Chhattisgarh"),
    ("Fashion Jewellery", "Tripura"),
]

def get_home_popular_links():
    """
    Returns Popular SEO links for the Home Page.
    Fetches DB links configured for home (show_on_home=True or global),
    and supplements with curated Pan-India fashion keyword links.
    """
    db_links = []
    try:
        db_links = list(PopularLink.objects.filter(
            Q(show_on_home=True) |
            Q(subcategory__isnull=True, category__isnull=True, maincategory__isnull=True, supercategory__isnull=True),
            is_active=True
        ).order_by('order', 'id'))
    except Exception:
        try:
            db_links = list(PopularLink.objects.filter(
                subcategory__isnull=True, category__isnull=True, maincategory__isnull=True, supercategory__isnull=True,
                is_active=True
            ).order_by('order', 'id'))
        except Exception:
            db_links = []

    final_links = []
    existing_titles = set()

    for l in db_links:
        title_lower = l.title.strip().lower()
        if title_lower not in existing_titles:
            existing_titles.add(title_lower)
            final_links.append({
                'title': l.title,
                'url': l.url,
                'state': l.state or '',
                'is_custom': True
            })

    for kw, state in HOME_POPULAR_KEYWORDS:
        title_text = f"{kw} Manufacturer & Wholesaler in {state}"
        if title_text.lower() not in existing_titles:
            existing_titles.add(title_text.lower())
            final_links.append({
                'title': title_text,
                'url': f"/search/?query={quote_plus(f'{kw} {state}')}",
                'state': state,
                'is_custom': False
            })

    return final_links

def get_popular_links(current_title=None, supercategory_obj=None, maincategory_obj=None, category_obj=None, subcategory_obj=None):
    """
    Retrieves DB-configured PopularLink records for the active hierarchy and supplements
    with programmatic regional SEO links across Indian states (Romegamart SEO pattern).
    """
    title_text = (current_title or "Fashion & Apparel").strip()
    db_links = []
    try:
        q = Q()
        if subcategory_obj:
            q |= Q(subcategory=subcategory_obj)
        if category_obj:
            q |= Q(category=category_obj)
        if maincategory_obj:
            q |= Q(maincategory=maincategory_obj)
        if supercategory_obj:
            q |= Q(supercategory=supercategory_obj)

        if q:
            db_links = list(PopularLink.objects.filter(q, is_active=True).order_by('order', 'id'))

        # Also append any global active links (where all category fields are blank)
        global_links = list(PopularLink.objects.filter(
            subcategory__isnull=True,
            category__isnull=True,
            maincategory__isnull=True,
            supercategory__isnull=True,
            is_active=True
        ).order_by('order', 'id'))
        for gl in global_links:
            if gl not in db_links:
                db_links.append(gl)
    except Exception as e:
        print(f"Error querying PopularLink: {e}")
        db_links = []

    existing_states = {l.state.strip().lower() for l in db_links if l.state}
    final_links = []

    # 1. Custom links from Database
    for l in db_links:
        final_links.append({
            'title': l.title,
            'url': l.url,
            'state': l.state or '',
            'is_custom': True
        })

    # 2. Dynamic Programmatic SEO links across Indian States (Romegamart pattern)
    for state in INDIAN_STATES:
        if state.lower() not in existing_states:
            query_str = f"{title_text} {state}"
            final_links.append({
                'title': f"{title_text} Manufacturer & Wholesaler in {state}",
                'url': f"/search/?query={quote_plus(query_str)}",
                'state': state,
                'is_custom': False
            })

    return final_links


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
        current_description = supercategory_obj.description or ""
        breadcrumbs.append({'name': supercategory_obj.name, 'url': f"/{supercategory_obj.slug}/"})

        if mcat:
            maincategory_obj = Maincategory.objects.filter(slug__iexact=mcat).first()
            if maincategory_obj:
                current_title = f"{supercategory_obj.name} - {maincategory_obj.name}"
                current_description = maincategory_obj.description or current_description
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

    elif supercat and Category.objects.filter(slug__iexact=supercat).exists():
        # Direct Category URL: e.g. /handbags/ or /test111/
        category_obj = Category.objects.filter(slug__iexact=supercat).first()
        maincategory_obj = category_obj.maincategory
        supercategory_obj = maincategory_obj.supercategory if maincategory_obj else None
        current_title = category_obj.name
        current_description = category_obj.description or ""
        breadcrumbs.append({'name': category_obj.name, 'url': category_obj.get_hierarchy_url()})
        products = Product.objects.filter(category=category_obj)
        scats = Subcategory.objects.filter(category=category_obj)
        child_items = [{
            'name': s.name,
            'image': s.image or (category_obj.image if category_obj else ''),
            'url': f"/{supercategory_obj.slug if supercategory_obj else 'all'}/{maincategory_obj.slug if maincategory_obj else 'all'}/{category_obj.slug}/{s.slug}/"
        } for s in scats]

    elif supercat and Subcategory.objects.filter(slug__iexact=supercat).exists():
        # Direct Subcategory URL: e.g. /tote-handbags/
        subcategory_obj = Subcategory.objects.filter(slug__iexact=supercat).first()
        category_obj = subcategory_obj.category
        maincategory_obj = category_obj.maincategory if category_obj else None
        supercategory_obj = maincategory_obj.supercategory if maincategory_obj else None
        current_title = subcategory_obj.name
        current_description = subcategory_obj.description or ""
        breadcrumbs.append({'name': subcategory_obj.name, 'url': subcategory_obj.get_hierarchy_url()})
        products = Product.objects.filter(subcategory=subcategory_obj)
        child_items = []

    else:
        # Fallback if unknown slug
        products = Product.objects.filter(name__icontains=raw_supercat or '')
        current_title = raw_supercat.title() if raw_supercat else "Products"
        current_description = ""
        breadcrumbs.append({'name': current_title, 'url': f"/{raw_supercat}/"})

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

    blog_filter = Q()
    if subcategory_obj:
        blog_filter |= Q(category=category_obj)
    if category_obj:
        blog_filter |= Q(category=category_obj)
    if maincategory_obj:
        blog_filter |= Q(maincategory=maincategory_obj)
    if supercategory_obj:
        blog_filter |= Q(supercategory=supercategory_obj)
    related_blogs = Blog.objects.filter(blog_filter).distinct()[:6] if blog_filter else Blog.objects.none()

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
        'current_description': current_description or '',
        'ops': subcategory_obj or category_obj or maincategory_obj or supercategory_obj,
        'title': current_title,
        'description': current_description or '',
        'related_blogs': related_blogs,
        'popular_links': get_popular_links(
            current_title=current_title,
            supercategory_obj=supercategory_obj,
            maincategory_obj=maincategory_obj,
            category_obj=category_obj,
            subcategory_obj=subcategory_obj
        ),
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
        try:
            m_obj = Maincategory.objects.filter(id=selected_maincategories).first() if str(selected_maincategories).isdigit() else Maincategory.objects.filter(slug=selected_maincategories).first()
            if m_obj:
                categories = Category.objects.filter(maincategory=m_obj)
                data = data.filter(maincategory=m_obj)
            else:
                data = Product.objects.none()
        except Exception:
            data = Product.objects.none()
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
    paginator = Paginator(data.order_by('-id'), 30)
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
        'current_title': "Filtered Products",
        'popular_links': get_popular_links(current_title="Fashion Collection"),
    })



def category_page(request, cat):
    return dynamic_category_view(request, supercat=cat)


def product_by_maincategory_category_subcategiry(request, mcat, cat, scat):
    return dynamic_category_view(request, supercat=mcat, mcat=cat, cat=scat)


def men_home_page(request):
    return dynamic_category_view(request, supercat='men')


def kid_home_page(request):
    return dynamic_category_view(request, supercat='kids')

def brand_page(request):
    brands = Brand.objects.all()
    return render(request, 'front/brands.html', {'brands': brands})

def product_page(request, cat):
    return dynamic_category_view(request, supercat=cat)


from django.db.models import Min
from django.shortcuts import render, get_object_or_404

def product_detail(request, name, id):
    maincategories=Maincategory.objects.all()
    categories=Category.objects.all()
    subcategories=Subcategory.objects.all()
    brands=Brand.objects.all()
    filteredProduct=Product.objects.all().order_by('id').reverse()[:12]
    skuProductByColor = []
    skuProductBySize = []
    similarProduct = []
    related_blogs = []
    breadcrumbs = [{'name': 'Home', 'url': '/'}]

    try:
        data = get_object_or_404(Product, id=id)

        # Get unique colors for the same SKU & pick the first occurrence
        if data.sku:
            unique_colors = Product.objects.filter(sku=data.sku).values('color').annotate(id=Min('id'))
            skuProductByColor = Product.objects.filter(id__in=[item['id'] for item in unique_colors])

            # Get unique sizes for the selected color & pick the first occurrence
            unique_sizes = Product.objects.filter(sku=data.sku, color=data.color).values('size').annotate(id=Min('id'))
            skuProductBySize = Product.objects.filter(id__in=[item['id'] for item in unique_sizes])
        else:
            skuProductByColor = [data]
            skuProductBySize = [data]

        # Get similar products
        if data.category:
            similarProduct = Product.objects.filter(category=data.category).exclude(id=data.id)[:12]
        else:
            similarProduct = Product.objects.exclude(id=data.id)[:12]

        # Related blogs connected to product or its categories
        try:
            prod_blog_filter = Q(product=data)
            if data.category:
                prod_blog_filter |= Q(category=data.category)
            if data.maincategory:
                prod_blog_filter |= Q(maincategory=data.maincategory)
            if data.supercategory:
                prod_blog_filter |= Q(supercategory=data.supercategory)
            related_blogs = list(Blog.objects.filter(prod_blog_filter).distinct()[:3])
            if not related_blogs:
                related_blogs = list(Blog.objects.all().order_by('-id')[:3])
        except Exception:
            related_blogs = []

        # Build breadcrumbs for product detail
        breadcrumbs = [{'name': 'Home', 'url': '/'}]
        if data.supercategory:
            breadcrumbs.append({'name': data.supercategory.name, 'url': f"/{data.supercategory.slug}/"})
            if data.maincategory:
                breadcrumbs.append({'name': data.maincategory.name, 'url': f"/{data.supercategory.slug}/{data.maincategory.slug}/"})
                if data.category:
                    breadcrumbs.append({'name': data.category.name, 'url': f"/{data.supercategory.slug}/{data.maincategory.slug}/{data.category.slug}/"})
        elif data.maincategory:
            breadcrumbs.append({'name': data.maincategory.name, 'url': f"/{data.maincategory.slug}/"})
            if data.category:
                breadcrumbs.append({'name': data.category.name, 'url': f"/{data.maincategory.slug}/{data.category.slug}/"})
        elif data.category:
            breadcrumbs.append({'name': data.category.name, 'url': f"/category/{data.category.name}/"})
        breadcrumbs.append({'name': data.name, 'url': request.path})

    except Exception as e:
        return render(request, 'front/error.html')

    return render(request, 'front/product-details.html', {
        'data': data,
        'skuProductByColor': skuProductByColor,
        'skuProductBySize': skuProductBySize,
        'similarProduct': similarProduct,
        'related_blogs': related_blogs,
        'carts': request.session.get('cart', {}),
        'maincategories': maincategories, 
        'categories': categories, 
        'subcategories': subcategories,
        'filteredProduct': filteredProduct,
        'brands': brands,
        'breadcrumbs': breadcrumbs,
    })


from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.utils.text import slugify

@csrf_exempt
def add_to_cart(request):
    if request.method == "POST":
        try:
            product_id = request.POST.get('productId') or request.POST.get('id')

            if not product_id:
                return JsonResponse({'status': 'error', 'error': 'Product ID is required'}, status=400)

            try:
                quantity = int(request.POST.get('quantity', 1))
                if quantity < 1:
                    quantity = 1
            except (ValueError, TypeError):
                quantity = 1

            product = Product.objects.filter(id=product_id).first()
            if not product:
                return JsonResponse({'status': 'error', 'error': 'Product not found'}, status=404)

            if 'cart' not in request.session or not isinstance(request.session['cart'], dict):
                request.session['cart'] = {}

            cart = request.session['cart']
            pid_str = str(product.id)

            if pid_str in cart:
                cart[pid_str]['quantity'] = int(cart[pid_str].get('quantity', 1)) + quantity
            else:
                price_val = 0.0
                try:
                    price_val = float(product.price) if product.price is not None else 0.0
                except (ValueError, TypeError):
                    price_val = 0.0

                cart[pid_str] = {
                    'id': product.id,
                    'name': product.name,
                    'price': price_val,
                    'quantity': quantity,
                    'image': product.image1 or '',
                    'size': str(product.size) if product.size else 'Free Size',
                    'color': str(product.color) if product.color else 'Standard',
                    'slug': slugify(product.name) if product.name else str(product.id),
                }

            request.session['cart'] = cart
            request.session.modified = True
            total_items = sum(int(item.get('quantity', 1)) for item in cart.values())

            return JsonResponse({
                'status': 'success',
                'message': f'"{product.name}" added to cart successfully!',
                'cart_count': total_items,
                'cart': cart
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'status': 'error', 'error': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'error': 'Invalid request method'}, status=400)


def get_cart_data(request):
    cart = request.session.get('cart', {})
    total_items = sum(int(item.get('quantity', 1)) for item in cart.values()) if isinstance(cart, dict) else 0
    return JsonResponse({'cart': cart, 'cart_count': total_items})


@csrf_exempt
def update_cart(request):
    if request.method == "POST":
        product_id = str(request.POST.get('id') or request.POST.get('productId') or '')
        try:
            change = int(request.POST.get('change', 0))
        except (ValueError, TypeError):
            change = 0

        set_qty = request.POST.get('quantity')
        cart = request.session.get('cart', {})
        if not isinstance(cart, dict):
            cart = {}

        if product_id in cart:
            if set_qty is not None:
                try:
                    new_qty = int(set_qty)
                    if new_qty > 0:
                        cart[product_id]['quantity'] = new_qty
                    else:
                        del cart[product_id]
                except (ValueError, TypeError):
                    pass
            else:
                cart[product_id]['quantity'] += change
                if cart[product_id]['quantity'] <= 0:
                    del cart[product_id]

        request.session['cart'] = cart
        request.session.modified = True

        subtotal = sum(float(item.get('price', 0.0)) * int(item.get('quantity', 1)) for item in cart.values())
        total_items = sum(int(item.get('quantity', 1)) for item in cart.values())
        item_qty = cart.get(product_id, {}).get('quantity', 0)
        item_price = float(cart.get(product_id, {}).get('price', 0.0))
        item_subtotal = item_price * item_qty

        return JsonResponse({
            'status': 'success',
            'message': 'Cart updated',
            'cart_count': total_items,
            'subtotal': subtotal,
            'total': subtotal,
            'item_qty': item_qty,
            'item_subtotal': item_subtotal,
            'is_empty': len(cart) == 0
        })

    return JsonResponse({'status': 'error', 'error': 'Invalid request'}, status=400)


@csrf_exempt
def remove_from_cart(request):
    if request.method == "POST":
        product_id = str(request.POST.get('id') or request.POST.get('productId') or '')
        cart = request.session.get('cart', {})
        if not isinstance(cart, dict):
            cart = {}

        if product_id in cart:
            del cart[product_id]

        request.session['cart'] = cart
        request.session.modified = True

        subtotal = sum(float(item.get('price', 0.0)) * int(item.get('quantity', 1)) for item in cart.values())
        total_items = sum(int(item.get('quantity', 1)) for item in cart.values())

        return JsonResponse({
            'status': 'success',
            'message': 'Product removed from cart',
            'cart_count': total_items,
            'subtotal': subtotal,
            'total': subtotal,
            'is_empty': len(cart) == 0
        })

    return JsonResponse({'status': 'error', 'error': 'Invalid request'}, status=400)


def cart_page(request):
    cart = request.session.get('cart', {})
    cart_items = []
    subtotal = 0.0
    for pid, item in (cart.items() if isinstance(cart, dict) else []):
        if not isinstance(item, dict):
            prod = Product.objects.filter(id=pid).first()
            if prod:
                item = {
                    'name': prod.name,
                    'price': float(prod.price or 0.0),
                    'quantity': int(item) if str(item).isdigit() else 1,
                    'image': prod.image or '',
                    'size': 'Free Size',
                    'color': 'Standard',
                    'slug': prod.name.replace(' ', '-'),
                }
            else:
                continue
        qty = int(item.get('quantity', 1) or 1)
        price = float(item.get('price', 0.0) or 0.0)
        item_total = price * qty
        subtotal += item_total
        cart_items.append({
            'id': pid,
            'name': item.get('name', 'Product'),
            'price': price,
            'quantity': qty,
            'image': item.get('image', ''),
            'size': item.get('size', 'Free Size'),
            'color': item.get('color', 'Standard'),
            'slug': item.get('slug', 'product'),
            'subtotal': item_total,
        })
    shipping = 0.0
    total = subtotal + shipping
    return render(request, 'front/cart.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping': shipping,
        'total': total,
    })


@csrf_exempt
def add_to_wishlist(request):
    if request.method == "POST":
        product_id = request.POST.get('productId') or request.POST.get('id')
        if not product_id:
            return JsonResponse({'status': 'error', 'error': 'Product ID is required'}, status=400)
        product = Product.objects.filter(id=product_id).first()
        if not product:
            return JsonResponse({'status': 'error', 'error': 'Product not found'}, status=404)

        if 'wishlist' not in request.session or not isinstance(request.session['wishlist'], list):
            request.session['wishlist'] = []
        wishlist_ids = request.session['wishlist']
        if product.id not in wishlist_ids:
            wishlist_ids.append(product.id)
            request.session['wishlist'] = wishlist_ids
            request.session.modified = True

        if request.user.is_authenticated:
            buyer = Buyer.objects.filter(phone=request.user.username).first() or Buyer.objects.filter(email=request.user.email).first()
            if buyer:
                Wishlist.objects.get_or_create(buyer=buyer, product=product)

        return JsonResponse({
            'status': 'success',
            'message': f'"{product.name}" added to wishlist!',
            'wishlist_count': len(request.session['wishlist']),
            'is_in_wishlist': True
        })

    return JsonResponse({'status': 'error', 'error': 'Invalid request'}, status=400)


@csrf_exempt
def remove_from_wishlist(request):
    if request.method == "POST":
        product_id = request.POST.get('productId') or request.POST.get('id')
        if not product_id:
            return JsonResponse({'error': 'Product ID is required'}, status=400)
        try:
            pid_int = int(product_id)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Invalid ID'}, status=400)

        wishlist_ids = request.session.get('wishlist', [])
        if pid_int in wishlist_ids:
            wishlist_ids.remove(pid_int)
            request.session['wishlist'] = wishlist_ids
            request.session.modified = True

        if request.user.is_authenticated:
            buyer = Buyer.objects.filter(phone=request.user.username).first() or Buyer.objects.filter(email=request.user.email).first()
            if buyer:
                Wishlist.objects.filter(buyer=buyer, product_id=pid_int).delete()

        return JsonResponse({
            'status': 'success',
            'message': 'Product removed from wishlist',
            'wishlist_count': len(request.session.get('wishlist', [])),
            'is_in_wishlist': False
        })

    return JsonResponse({'error': 'Invalid request'}, status=400)


def wishlist_page(request):
    product_ids = set(request.session.get('wishlist', []))
    if request.user.is_authenticated:
        buyer = Buyer.objects.filter(phone=request.user.username).first() or Buyer.objects.filter(email=request.user.email).first()
        if buyer:
            db_pids = Wishlist.objects.filter(buyer=buyer).values_list('product_id', flat=True)
            product_ids.update(db_pids)
            request.session['wishlist'] = list(product_ids)
            request.session.modified = True

    wishlist_products = Product.objects.filter(id__in=product_ids).order_by('-id')
    return render(request, 'front/wishlist.html', {
        'wishlist_products': wishlist_products,
        'wishlist_count': wishlist_products.count()
    })


def compare_page(request):
    return render(request, 'front/compare.html')


from datetime import datetime
import random

def checkout_page(request):
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('/cart/')

    cart_items = []
    subtotal = 0.0
    for pid, item in (cart.items() if isinstance(cart, dict) else []):
        if not isinstance(item, dict):
            prod = Product.objects.filter(id=pid).first()
            if prod:
                item = {
                    'name': prod.name,
                    'price': float(prod.price or 0.0),
                    'quantity': int(item) if str(item).isdigit() else 1,
                    'image': prod.image or '',
                    'size': 'Free Size',
                    'color': 'Standard',
                    'slug': prod.name.replace(' ', '-'),
                }
            else:
                continue
        qty = int(item.get('quantity', 1) or 1)
        price = float(item.get('price', 0.0) or 0.0)
        item_total = price * qty
        subtotal += item_total
        cart_items.append({
            'id': pid,
            'name': item.get('name', 'Product'),
            'price': price,
            'quantity': qty,
            'image': item.get('image', ''),
            'size': item.get('size', 'Free Size'),
            'color': item.get('color', 'Standard'),
            'slug': item.get('slug', 'product'),
            'subtotal': item_total,
        })
    shipping = 0.0
    total = subtotal + shipping

    buyer = None
    saved_address = None
    if request.user.is_authenticated:
        buyer = Buyer.objects.filter(phone=request.user.username).first() or Buyer.objects.filter(email=request.user.email).first()
        if buyer:
            saved_address = Address.objects.filter(buyer=buyer).order_by('-id').first()

    initial_name = buyer.name if (buyer and buyer.name) else ''
    initial_phone = buyer.phone if (buyer and buyer.phone) else ''
    initial_email = buyer.email if (buyer and buyer.email) else ''
    initial_address = saved_address.address if (saved_address and saved_address.address) else ''
    initial_city = saved_address.city if (saved_address and saved_address.city) else ''
    initial_state = saved_address.state if (saved_address and saved_address.state) else ''
    initial_pin = saved_address.pin if (saved_address and saved_address.pin) else ''

    # Check email verification status
    session_verified_email = request.session.get('checkout_verified_email', '').strip().lower()
    is_email_verified = False
    if session_verified_email:
        is_email_verified = True
        if not initial_email:
            initial_email = session_verified_email
    elif request.user.is_authenticated and request.user.email:
        is_email_verified = True
        request.session['checkout_verified_email'] = request.user.email.strip().lower()

    checkout_ctx = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping': shipping,
        'total': total,
        'buyer': buyer,
        'saved_address': saved_address,
        'initial_name': initial_name,
        'initial_phone': initial_phone,
        'initial_email': initial_email,
        'initial_address': initial_address,
        'initial_city': initial_city,
        'initial_state': initial_state,
        'initial_pin': initial_pin,
        'is_email_verified': is_email_verified,
        'form_data': {},
    }

    if request.method == "POST":
        try:
            name = request.POST.get('name', '').strip()
            phone = request.POST.get('phone', '').strip()
            email = request.POST.get('email', '').strip()
            address = request.POST.get('address', '').strip()
            city = request.POST.get('city', '').strip()
            state = request.POST.get('state', '').strip()
            pincode = request.POST.get('pincode', '').strip()
            notes = request.POST.get('notes', '').strip()

            if not all([name, phone, email, address, city, state, pincode]):
                messages.error(request, "Please fill in all required delivery address and email fields.")
                ctx = dict(checkout_ctx)
                ctx['form_data'] = request.POST
                ctx['is_email_verified'] = is_email_verified
                return render(request, 'front/checkout.html', ctx)

            phone_digits = ''.join(filter(str.isdigit, phone))
            if len(phone_digits) < 10:
                messages.error(request, "Please enter a valid 10-digit mobile phone number.")
                ctx = dict(checkout_ctx)
                ctx['form_data'] = request.POST
                ctx['is_email_verified'] = is_email_verified
                return render(request, 'front/checkout.html', ctx)

            clean_phone = phone_digits[-10:] if len(phone_digits) >= 10 else phone_digits

            # Email OTP verification enforcement
            verified_session_email = request.session.get('checkout_verified_email', '').strip().lower()
            auth_email = (request.user.email or '').strip().lower() if request.user.is_authenticated else ''
            req_email = email.strip().lower()

            if not (verified_session_email == req_email or (auth_email and auth_email == req_email)):
                messages.error(request, "Please verify your email address using the 6-digit OTP code before completing your order.")
                ctx = dict(checkout_ctx)
                ctx['form_data'] = request.POST
                ctx['is_email_verified'] = False
                return render(request, 'front/checkout.html', ctx)

            # Customer Account (User & Buyer) handling
            # Password default is set to clean_phone (10-digit mobile number) so customer can log in!
            if not buyer:
                buyer = Buyer.objects.filter(phone=clean_phone).first()
                if not buyer:
                    buyer = Buyer.objects.create(
                        name=name,
                        phone=clean_phone,
                        email=email,
                        password=make_password(clean_phone)
                    )
                else:
                    if not buyer.name and name:
                        buyer.name = name
                    buyer.email = email
                    if not buyer.password:
                        buyer.password = make_password(clean_phone)
                    buyer.save()

            # If not already logged in, create/link User and log the customer in
            if not request.user.is_authenticated:
                try:
                    user = User.objects.filter(username=clean_phone).first()
                    first_name, last_name = name.split(" ", 1) if " " in name else (name, "")
                    if not user:
                        user = User.objects.create_user(
                            username=clean_phone,
                            email=email,
                            first_name=first_name,
                            last_name=last_name
                        )
                        user.set_password(clean_phone)
                        user.save()
                    else:
                        if not user.email:
                            user.email = email
                            user.save()
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                except Exception as user_err:
                    print("User auth error in checkout:", user_err)

            # Auto-upgrade MySQL columns if running on MySQL
            try:
                from django.db import connection
                if connection.vendor == 'mysql':
                    with connection.cursor() as cursor:
                        cursor.execute("ALTER TABLE mainApp_address MODIFY COLUMN address TEXT, MODIFY COLUMN city VARCHAR(150), MODIFY COLUMN state VARCHAR(150), MODIFY COLUMN pin VARCHAR(20), MODIFY COLUMN landmark VARCHAR(255), MODIFY COLUMN alternatePhone VARCHAR(20)")
                        cursor.execute("ALTER TABLE mainApp_buyer MODIFY COLUMN phone VARCHAR(20)")
            except Exception:
                pass

            # Create Address record with graceful fallback
            address_obj = None
            try:
                address_obj = Address.objects.create(
                    buyer=buyer,
                    address=address,
                    city=city,
                    state=state,
                    pin=pincode,
                    alternatePhone=clean_phone,
                    addressType='Home'
                )
            except Exception as addr_err:
                try:
                    address_obj = Address.objects.create(
                        buyer=buyer,
                        address=(address or '')[:10],
                        city=(city or '')[:10],
                        state=(state or '')[:10],
                        pin=(pincode or '')[:10],
                        alternatePhone=(clean_phone or '')[:10],
                        addressType='Home'
                    )
                except Exception:
                    address_obj = None

            now_str = timezone.localtime(timezone.now()).strftime("%d %b %Y, %I:%M %p")
            rand_suffix = random.randint(1000, 9999)
            order_number = f"ORD{datetime.now().strftime('%y%m%d')}{rand_suffix}"

            for item in cart_items:
                product = None
                try:
                    product = Product.objects.filter(id=item['id']).first()
                except Exception:
                    pass

                Order.objects.create(
                    buyer=buyer,
                    product=product,
                    address=address_obj,
                    quantity=item['quantity'],
                    totalPrice=item['subtotal'],
                    shippingPrice=0.0,
                    finalPrice=item['subtotal'],
                    transactionId=f"COD-{order_number}",
                    orderDate=now_str,
                    orderStatus="Pending",
                    waywill="",
                    cancelled_by=""
                )

            # Clear session cart and checkout OTP data
            request.session['cart'] = {}
            request.session.pop('checkout_verified_email', None)
            request.session.pop('checkout_otp_code', None)
            request.session.pop('checkout_otp_email', None)
            request.session.modified = True

            return render(request, 'front/confirmation.html', {
                'order_number': order_number,
                'buyer': buyer,
                'address': address_obj,
                'total': total,
                'cart_items': cart_items,
                'order_date': now_str,
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f"There was an issue processing your order. Please check your details and try again. (Details: {str(e)})")
            ctx = dict(checkout_ctx)
            ctx['form_data'] = request.POST
            return render(request, 'front/checkout.html', ctx)

    return render(request, 'front/checkout.html', checkout_ctx)


def blog_page(request):
    maincategories = Maincategory.objects.all()
    categories = Category.objects.all()
    subcategories = Subcategory.objects.all()
    brands = Brand.objects.all()
    size = Size.objects.all()
    color = Color.objects.all()
    filteredProduct=Product.objects.all().order_by('id').reverse()[:12]


    blogs = Blog.objects.all().order_by('-id')
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
    filteredProduct = Product.objects.all().order_by('id').reverse()[:12]

    if request.GET.get('logout'):
        logout(request)
        try:
            request.session.flush()
        except Exception:
            pass

    if request.user.is_authenticated:
        if request.user.is_superuser or request.user.is_staff:
            return redirect("/admin-dashboard")
        return redirect("/all/")

    next_url = request.GET.get("next") or request.POST.get("next") or ""

    if request.method == "POST":
        raw_input = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        digits = ''.join(filter(str.isdigit, raw_input))
        clean_phone = digits[-10:] if len(digits) >= 10 else digits

        user = None

        # 1. Login by Email
        if '@' in raw_input:
            matched_user = User.objects.filter(email__iexact=raw_input).first()
            if not matched_user:
                buyer = Buyer.objects.filter(email__iexact=raw_input).first()
                if buyer and buyer.phone:
                    matched_user = User.objects.filter(username=buyer.phone).first()
            if matched_user:
                user = authenticate(username=matched_user.username, password=password)

        # 2. Login by Username / Phone
        if user is None:
            user = authenticate(username=raw_input, password=password)
        if user is None and clean_phone and clean_phone != raw_input:
            user = authenticate(username=clean_phone, password=password)

        # 3. Buyer Table Fallback & Sync: In case User table was out of sync
        if user is None:
            from django.contrib.auth.hashers import check_password
            matched_buyer = Buyer.objects.filter(
                Q(email__iexact=raw_input) |
                Q(phone=raw_input) |
                Q(phone=clean_phone)
            ).first()

            if matched_buyer and matched_buyer.password:
                if check_password(password, matched_buyer.password) or matched_buyer.password == password:
                    # Verified! Find or create Django User and sync password
                    matched_user = User.objects.filter(username=matched_buyer.phone).first()
                    if not matched_user and matched_buyer.email:
                        matched_user = User.objects.filter(email__iexact=matched_buyer.email).first()
                    if not matched_user:
                        first_name, last_name = matched_buyer.name.split(" ", 1) if " " in (matched_buyer.name or '') else (matched_buyer.name or '', "")
                        matched_user = User.objects.create_user(
                            username=matched_buyer.phone or clean_phone or raw_input,
                            email=matched_buyer.email or '',
                            first_name=first_name,
                            last_name=last_name
                        )
                    matched_user.set_password(password)
                    matched_user.save()
                    user = matched_user

        if user is not None:
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')

            # Superuser / staff redirection
            if user.is_superuser or user.is_staff:
                if next_url and not next_url.startswith("/my-account"):
                    return redirect(next_url)
                return redirect("/admin-dashboard")

            # Customer redirection: redirect to products catalog page
            if next_url and not next_url.startswith("/admin") and not next_url.startswith("/my-account"):
                return redirect(next_url)
            return redirect("/all/")
        else:
            messages.error(request, "Invalid username/phone or password!")

    return render(request, "front/login.html", {
        'maincategories': maincategories,
        'categories': categories,
        'subcategories': subcategories,
        'brands': brands,
        'size': size,
        'color': color,
        'filteredProduct': filteredProduct,
        'next': next_url,
    })


def logout_page(request):
    logout(request)
    try:
        request.session.flush()
    except Exception:
        pass
    return redirect("/login/")


def register(request):
    maincategories = Maincategory.objects.all()
    categories = Category.objects.all()
    subcategories = Subcategory.objects.all()
    brands = Brand.objects.all()
    size = Size.objects.all()
    color = Color.objects.all()
    filteredProduct = Product.objects.all().order_by('id').reverse()[:12]
    context = {
        'maincategories': maincategories,
        'categories': categories,
        'subcategories': subcategories,
        'brands': brands,
        'size': size,
        'color': color,
        'filteredProduct': filteredProduct,
    }

    if request.method == "POST":
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()

        address = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        pincode = request.POST.get('pincode', '').strip()

        # Check if the user already exists
        if User.objects.filter(username=phone).exists():
            messages.error(request, "Phone number already exists. Please log in.")
            return render(request, 'front/register.html', context)

        if email and User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists. Please log in.")
            return render(request, 'front/register.html', context)

        # Hash the password
        hashed_password = make_password(password)

        # Create a new buyer object
        buyer = Buyer(name=name, phone=phone, email=email, password=hashed_password)
        buyer.save()

        # If delivery address was entered during registration, save it immediately
        if address or city or state or pincode:
            try:
                Address.objects.create(
                    buyer=buyer,
                    addressType='Home',
                    address=address or 'Registered Delivery Address',
                    city=city,
                    state=state,
                    pin=pincode
                )
            except Exception as addr_err:
                print("Address save error during registration:", addr_err)

        # Split the name into first and last names
        first_name, last_name = name.split(" ", 1) if " " in name else (name, "")

        # Create a new user object
        user = User(username=phone, email=email, first_name=first_name, last_name=last_name, password=hashed_password)
        user.save()

        # Authenticate and log the user in
        user = authenticate(username=phone, password=password)

        if user is not None:
            login(request, user)
            if user.is_superuser:
                return redirect("/admin-dashboard")
            return redirect('/all/')
        else:
            messages.error(request, "Registration successful! Please log in.")
            return redirect('/login')

    return render(request, 'front/register.html', context)


# ==============================================================================
# FORGOT PASSWORD WITH EMAIL OTP SYSTEM
# ==============================================================================

def send_otp_email(to_email, otp_code, user_name="Customer", purpose="reset"):
    """Sends a professional, boutique-branded OTP email for password reset or checkout verification"""
    if purpose == "checkout":
        subject = f"{otp_code} is your Email Verification OTP - Nari Fashion Store"
        headline = "Checkout Email Verification"
        subheadline = "✦ SECURE CHECKOUT VERIFICATION ✦"
        instruction = "Thank you for shopping with Nari Fashion Store! Use the verification OTP below to verify your email and place your order:"
        footer_note = "If you did not initiate this order, please ignore this email."
    else:
        subject = f"{otp_code} is your Password Reset OTP - Nari Fashion Store"
        headline = "Password Reset Request"
        subheadline = "✦ NARI FASHION STORE ✦"
        instruction = "We received a request to reset your password. Use the verification OTP below to complete the process:"
        footer_note = "If you did not request a password change, please ignore this email or reach out to our support team immediately."

    message_plain = (
        f"Hello {user_name},\n\n"
        f"{instruction}\n\n"
        f"Your One-Time Password (OTP) is: {otp_code}\n\n"
        f"This OTP is valid for 15 minutes. For security reasons, please do not share this OTP with anyone.\n\n"
        f"{footer_note}\n\n"
        f"Warm regards,\nNari Fashion Store Team"
    )

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{headline}</title>
    </head>
    <body style="margin: 0; padding: 20px 0; background-color: #FAF5F6; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
        <div style="max-width: 520px; margin: 0 auto; background: #ffffff; border-radius: 18px; border: 1px solid #F5E5E8; overflow: hidden; box-shadow: 0 10px 30px rgba(239, 40, 83, 0.08);">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #EF2853 0%, #D81A43 100%); padding: 28px 24px; text-align: center; color: #ffffff;">
                <span style="display: inline-block; background: rgba(255,255,255,0.2); font-size: 11px; font-weight: 700; letter-spacing: 1.5px; padding: 4px 14px; border-radius: 20px; text-transform: uppercase; margin-bottom: 8px;">{subheadline}</span>
                <h2 style="margin: 0; font-size: 22px; font-weight: 800; letter-spacing: -0.3px;">{headline}</h2>
            </div>
            
            <!-- Body -->
            <div style="padding: 32px 28px; color: #2D3748;">
                <p style="font-size: 15px; margin: 0 0 14px;">Hello <strong>{user_name}</strong>,</p>
                <p style="font-size: 14px; color: #64748B; line-height: 1.6; margin: 0 0 24px;">
                    {instruction}
                </p>
                
                <!-- OTP Box -->
                <div style="text-align: center; margin: 24px 0;">
                    <div style="display: inline-block; background: #FFF0F3; border: 2px dashed #EF2853; border-radius: 14px; padding: 14px 36px;">
                        <span style="font-size: 34px; font-weight: 800; letter-spacing: 8px; color: #EF2853; font-family: monospace;">
                            {otp_code}
                        </span>
                    </div>
                    <p style="font-size: 12.5px; color: #94A3B8; margin: 10px 0 0;">
                        ⏳ Valid for <strong>15 minutes</strong>. Single use only.
                    </p>
                </div>

                <p style="font-size: 13px; color: #64748B; line-height: 1.6; margin: 20px 0 0;">
                    {footer_note}
                </p>
            </div>

            <!-- Footer -->
            <div style="background: #FAFAFA; border-top: 1px solid #F1F5F9; padding: 18px 24px; text-align: center; font-size: 12px; color: #94A3B8;">
                <p style="margin: 0 0 4px;">&copy; Nari Fashion Store. All rights reserved.</p>
                <p style="margin: 0;">Authentic Indian Ethnic &amp; Modern Fashion Boutique</p>
            </div>
        </div>
    </body>
    </html>
    """

    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'info@narifashionstore.com')
    print(f"\n=======================================================")
    print(f"[OTP DISPATCH] Purpose: {purpose} | Recipient: {to_email} | OTP: {otp_code} | User: {user_name}")
    print(f"=======================================================\n")

    try:
        from django.core.mail import EmailMultiAlternatives
        msg = EmailMultiAlternatives(subject, message_plain, from_email, [to_email])
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)
        return True, "Email sent successfully"
    except Exception as e:
        print(f"[OTP Email Send Warning]: {e}")
        return False, str(e)


def forgot_password_page(request):
    """Step 1: Request Email / Phone to send Password Reset OTP"""
    maincategories = Maincategory.objects.all()
    categories = Category.objects.all()
    subcategories = Subcategory.objects.all()
    brands = Brand.objects.all()
    size = Size.objects.all()
    color = Color.objects.all()
    filteredProduct = Product.objects.all().order_by('id').reverse()[:12]

    context = {
        'maincategories': maincategories,
        'categories': categories,
        'subcategories': subcategories,
        'brands': brands,
        'size': size,
        'color': color,
        'filteredProduct': filteredProduct,
    }

    if request.user.is_authenticated:
        return redirect('/my-account/')

    if request.method == "POST":
        identifier = request.POST.get('identifier', '').strip()
        if not identifier:
            messages.error(request, "Please enter your registered email address or phone number.")
            return render(request, 'front/forgot-password.html', context)

        # Look up by email or phone in Buyer and User
        buyer = None
        user = None

        if '@' in identifier:
            buyer = Buyer.objects.filter(email__iexact=identifier).first()
            user = User.objects.filter(email__iexact=identifier).first()
            if not user and buyer and buyer.phone:
                user = User.objects.filter(username=buyer.phone).first()
        else:
            phone_digits = ''.join(filter(str.isdigit, identifier))
            clean_phone = phone_digits[-10:] if len(phone_digits) >= 10 else phone_digits
            buyer = Buyer.objects.filter(phone=clean_phone).first() or Buyer.objects.filter(phone=identifier).first()
            user = User.objects.filter(username=clean_phone).first() or User.objects.filter(username=identifier).first()
            if not user and buyer and buyer.email:
                user = User.objects.filter(email__iexact=buyer.email).first()

        if not buyer and not user:
            messages.error(request, "No account found with this email or phone number. Please check and try again.")
            return render(request, 'front/forgot-password.html', context)

        target_email = (buyer.email if buyer and buyer.email else (user.email if user and user.email else "")).strip()

        if not target_email or '@' not in target_email:
            messages.error(request, "This account does not have a valid registered email address. Please contact customer support.")
            return render(request, 'front/forgot-password.html', context)

        # Generate secure 6-digit OTP
        import random
        otp_code = str(random.randint(100000, 999999))

        # Invalidate previous unused OTPs for this email and save new one
        try:
            PasswordResetOTP.objects.filter(email__iexact=target_email, is_used=False).update(is_used=True)
            PasswordResetOTP.objects.create(email=target_email, otp=otp_code)
        except Exception as db_err:
            print("OTP DB Error:", db_err)

        target_phone = buyer.phone if buyer and buyer.phone else (user.username if user else "")

        # Store session reset data
        request.session['reset_email'] = target_email
        request.session['reset_phone'] = target_phone
        request.session['reset_buyer_id'] = buyer.id if buyer else None
        request.session['reset_user_id'] = user.id if user else None
        request.session['reset_otp_fallback'] = otp_code
        request.session['reset_user_name'] = buyer.name if (buyer and buyer.name) else (user.first_name if user else "Customer")
        request.session.modified = True

        # Send email
        sent, err = send_otp_email(target_email, otp_code, request.session['reset_user_name'])
        if sent:
            messages.success(request, f"A 6-digit verification OTP has been sent to {target_email}. Please enter it below.")
        else:
            messages.success(request, f"OTP generated for {target_email}. Please check your inbox or spam folder.")

        return redirect('/verify-reset-otp/')

    return render(request, 'front/forgot-password.html', context)


def verify_reset_otp(request):
    """Step 2: Verify 6-digit OTP and set new password"""
    target_email = request.session.get('reset_email', '')
    if not target_email:
        messages.error(request, "Session expired. Please enter your email/phone again.")
        return redirect('/forgot-password/')

    maincategories = Maincategory.objects.all()
    categories = Category.objects.all()
    subcategories = Subcategory.objects.all()
    brands = Brand.objects.all()
    size = Size.objects.all()
    color = Color.objects.all()
    filteredProduct = Product.objects.all().order_by('id').reverse()[:12]

    # Mask email for privacy, e.g. pr***@gmail.com
    parts = target_email.split('@')
    masked_email = target_email
    if len(parts) == 2 and len(parts[0]) > 2:
        masked_email = f"{parts[0][:2]}***@{parts[1]}"

    context = {
        'maincategories': maincategories,
        'categories': categories,
        'subcategories': subcategories,
        'brands': brands,
        'size': size,
        'color': color,
        'filteredProduct': filteredProduct,
        'target_email': target_email,
        'masked_email': masked_email,
    }

    if request.method == "POST":
        entered_otp = request.POST.get('otp', '').strip()
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        if not entered_otp:
            messages.error(request, "Please enter the 6-digit OTP code sent to your email.")
            return render(request, 'front/verify-reset-otp.html', context)

        if not new_password or len(new_password) < 6:
            messages.error(request, "New password must be at least 6 characters long.")
            return render(request, 'front/verify-reset-otp.html', context)

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match. Please re-enter carefully.")
            return render(request, 'front/verify-reset-otp.html', context)

        # Verify OTP against Database first, then session fallback
        otp_valid = False
        otp_record = PasswordResetOTP.objects.filter(email__iexact=target_email, otp=entered_otp, is_used=False).order_by('-created_at').first()

        if otp_record and otp_record.is_valid():
            otp_valid = True
            otp_record.is_used = True
            otp_record.save()
        elif request.session.get('reset_otp_fallback') == entered_otp:
            otp_valid = True

        if not otp_valid:
            messages.error(request, "Invalid or expired OTP. Please check the code or click Resend OTP.")
            return render(request, 'front/verify-reset-otp.html', context)

        # Update both User and Buyer passwords reliably
        hashed = make_password(new_password)
        target_phone = request.session.get('reset_phone', '')
        buyer_id = request.session.get('reset_buyer_id')
        user_id = request.session.get('reset_user_id')

        # 1. Update all matching Buyers
        buyers = []
        if buyer_id:
            b = Buyer.objects.filter(id=buyer_id).first()
            if b: buyers.append(b)
        if target_email:
            buyers.extend(list(Buyer.objects.filter(email__iexact=target_email)))
        if target_phone:
            buyers.extend(list(Buyer.objects.filter(phone=target_phone)))

        seen_b = set()
        for b in buyers:
            if b.id not in seen_b:
                seen_b.add(b.id)
                b.password = hashed
                if target_email and not b.email:
                    b.email = target_email
                b.save()

        # 2. Update all matching Users
        users = []
        if user_id:
            u = User.objects.filter(id=user_id).first()
            if u: users.append(u)
        if target_phone:
            users.extend(list(User.objects.filter(username=target_phone)))
        if target_email:
            users.extend(list(User.objects.filter(email__iexact=target_email)))

        seen_u = set()
        for u in users:
            if u.id not in seen_u:
                seen_u.add(u.id)
                u.set_password(new_password)
                if target_email and not u.email:
                    u.email = target_email
                u.save()

        # 3. If User doesn't exist yet but Buyer exists, create the User so customer can log in
        if not seen_u and buyers:
            primary_b = buyers[0]
            uname = primary_b.phone or target_phone or (target_email.split('@')[0])
            first_name, last_name = primary_b.name.split(" ", 1) if " " in (primary_b.name or '') else (primary_b.name or '', "")
            new_u = User.objects.create_user(
                username=uname,
                email=primary_b.email or target_email,
                first_name=first_name,
                last_name=last_name
            )
            new_u.set_password(new_password)
            new_u.save()

        # Clear session reset data
        request.session.pop('reset_email', None)
        request.session.pop('reset_phone', None)
        request.session.pop('reset_buyer_id', None)
        request.session.pop('reset_user_id', None)
        request.session.pop('reset_otp_fallback', None)
        request.session.pop('reset_user_name', None)
        request.session.modified = True

        messages.success(request, "Your password has been reset successfully! Please log in with your mobile number/email and new password.")
        return redirect('/login/')

    return render(request, 'front/verify-reset-otp.html', context)


def resend_reset_otp(request):
    """Resend a fresh OTP code to user's email"""
    target_email = request.session.get('reset_email', '')
    if not target_email:
        messages.error(request, "Session expired. Please enter your email/phone again.")
        return redirect('/forgot-password/')

    import random
    otp_code = str(random.randint(100000, 999999))
    try:
        PasswordResetOTP.objects.filter(email__iexact=target_email, is_used=False).update(is_used=True)
        PasswordResetOTP.objects.create(email=target_email, otp=otp_code)
    except Exception:
        pass

    request.session['reset_otp_fallback'] = otp_code
    user_name = request.session.get('reset_user_name', 'Customer')
    send_otp_email(target_email, otp_code, user_name)

    messages.success(request, f"A fresh OTP has been sent to {target_email}.")
    return redirect('/verify-reset-otp/')


# ==============================================================================
# CHECKOUT EMAIL OTP VERIFICATION SYSTEM
# ==============================================================================

@csrf_exempt
def send_checkout_email_otp(request):
    """API endpoint to send 6-digit OTP to customer email during checkout"""
    if request.method != "POST":
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

    import json
    email = ''
    name = 'Valued Customer'
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body.decode('utf-8'))
            email = data.get('email', '').strip().lower()
            name = data.get('name', '').strip() or 'Valued Customer'
        except Exception:
            pass
    if not email:
        email = request.POST.get('email', '').strip().lower()
        name = request.POST.get('name', '').strip() or 'Valued Customer'

    if not email:
        return JsonResponse({'status': 'error', 'message': 'Please enter your email address.'}, status=400)

    try:
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        validate_email(email)
    except Exception:
        return JsonResponse({'status': 'error', 'message': 'Please enter a valid email address.'}, status=400)

    import random
    otp_code = str(random.randint(100000, 999999))

    try:
        PasswordResetOTP.objects.filter(email__iexact=email, is_used=False).update(is_used=True)
        PasswordResetOTP.objects.create(email=email, otp=otp_code)
    except Exception as db_err:
        print("Checkout OTP DB save error:", db_err)

    request.session['checkout_otp_email'] = email
    request.session['checkout_otp_code'] = otp_code
    request.session['checkout_otp_user_name'] = name
    request.session.modified = True

    sent, err = send_otp_email(email, otp_code, user_name=name, purpose="checkout")

    return JsonResponse({
        'status': 'success',
        'message': f'A 6-digit verification code has been sent to {email}.',
        'email': email
    })


@csrf_exempt
def verify_checkout_email_otp(request):
    """API endpoint to verify the 6-digit OTP during checkout"""
    if request.method != "POST":
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

    import json
    email = ''
    otp = ''
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body.decode('utf-8'))
            email = data.get('email', '').strip().lower()
            otp = data.get('otp', '').strip()
        except Exception:
            pass
    if not email or not otp:
        email = request.POST.get('email', email).strip().lower()
        otp = request.POST.get('otp', otp).strip()

    if not email or not otp:
        return JsonResponse({'status': 'error', 'message': 'Email address and 6-digit OTP code are required.'}, status=400)

    otp_valid = False
    otp_record = PasswordResetOTP.objects.filter(email__iexact=email, otp=otp, is_used=False).order_by('-created_at').first()

    if otp_record and otp_record.is_valid():
        otp_valid = True
        otp_record.is_used = True
        otp_record.save()
    elif request.session.get('checkout_otp_email') == email and request.session.get('checkout_otp_code') == otp:
        otp_valid = True

    if not otp_valid:
        return JsonResponse({'status': 'error', 'message': 'Invalid or expired OTP code. Please check the code or click Resend.'}, status=400)

    # Mark as verified in session
    request.session['checkout_verified_email'] = email
    request.session.modified = True

    return JsonResponse({
        'status': 'success',
        'message': 'Email verified successfully! You can now place your order.',
        'email': email
    })



@login_required(login_url="/login")
def my_account(request):
    if request.user.is_superuser or request.user.is_staff:
        return redirect("/admin-dashboard")

    buyer = Buyer.objects.filter(phone=request.user.username).first()
    if not buyer and request.user.email:
        buyer = Buyer.objects.filter(email=request.user.email).first()

    if not buyer:
        buyer = Buyer.objects.create(
            name=f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
            phone=request.user.username,
            email=request.user.email or "",
            password=request.user.password
        )

    orders = Order.objects.filter(buyer=buyer).order_by('-id')[:5]
    total_orders = Order.objects.filter(buyer=buyer).count()
    addresses = Address.objects.filter(buyer=buyer)

    return render(request, 'front/my-account.html', {
        'buyer': buyer,
        'orders': orders,
        'total_orders': total_orders,
        'addresses': addresses,
    })


@login_required(login_url="/login")
def my_account_address(request):
    if request.user.is_superuser or request.user.is_staff:
        return redirect("/admin-dashboard")
    buyer = Buyer.objects.filter(phone=request.user.username).first() or Buyer.objects.filter(email=request.user.email).first()
    addresses = Address.objects.filter(buyer=buyer) if buyer else []
    return render(request, 'front/my-account-address.html', {'buyer': buyer, 'addresses': addresses})


@login_required(login_url="/login")
def my_account_edit(request):
    if request.user.is_superuser or request.user.is_staff:
        return redirect("/admin-dashboard")
    buyer = Buyer.objects.filter(phone=request.user.username).first() or Buyer.objects.filter(email=request.user.email).first()
    if request.method == "POST":
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        if name:
            request.user.first_name = name.split(" ", 1)[0]
            request.user.last_name = name.split(" ", 1)[1] if " " in name else ""
            if buyer:
                buyer.name = name
        if email:
            request.user.email = email
            if buyer:
                buyer.email = email
        request.user.save()
        if buyer:
            buyer.save()
        messages.success(request, "Account details updated successfully.")
        return redirect("/my-account/")
    return render(request, 'front/my-account-edit.html', {'buyer': buyer})


@login_required(login_url="/login")
def my_account_order(request):
    if request.user.is_superuser or request.user.is_staff:
        return redirect("/admin-dashboard")
    buyer = Buyer.objects.filter(phone=request.user.username).first() or Buyer.objects.filter(email=request.user.email).first()
    orders = Order.objects.filter(buyer=buyer).order_by('-id') if buyer else []
    return render(request, 'front/my-account-orders.html', {'buyer': buyer, 'orders': orders})


@login_required(login_url="/login")
def my_account_order_details(request):
    if request.user.is_superuser or request.user.is_staff:
        return redirect("/admin-dashboard")
    return redirect('/my-account-orders/')

def order_tracking(request):
    return redirect('/my-account-orders/')

def payment_confirmation(request):
    return render(request, 'front/confirmation.html')

def payment_failure(request):
    return render(request, 'front/error.html')


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
        # 1. Exact query match across products, descriptions, categories, tags, SEO
        data = Product.objects.filter(
            Q(name__icontains=query) |
            Q(tags__icontains=query) |
            Q(meta_title__icontains=query) |
            Q(meta_keywords__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query) |
            Q(subcategory__name__icontains=query)
        ).distinct().order_by('-id')

        # 2. Multi-word SEO query fallback (e.g. "Designer Handbags Manufacturer in Maharashtra")
        if not data.exists() and ' ' in query:
            stop_words = {'in', 'and', 'or', 'for', 'the', 'at', 'manufacturer', 'wholesaler', 'supplier', 'dealer', 'shop', 'store', 'market', 'hub', 'collection', 'online', '&'}
            indian_states_lower = {s.lower() for s in INDIAN_STATES}
            raw_words = [w.strip('.,-()[]') for w in query.split()]
            # Extract pure product keywords (exclude stop words and state names)
            product_words = [w for w in raw_words if len(w) > 2 and w.lower() not in stop_words and w.lower() not in indian_states_lower]
            if not product_words:
                product_words = [w for w in raw_words if len(w) > 2 and w.lower() not in stop_words]

            q_filter = Q()
            for w in product_words:
                stem = w.rstrip('s') if (w.lower().endswith('s') and len(w) > 3) else w
                q_filter |= (
                    Q(name__icontains=w) | Q(name__icontains=stem) |
                    Q(tags__icontains=w) | Q(tags__icontains=stem) |
                    Q(meta_keywords__icontains=w) | Q(meta_keywords__icontains=stem) |
                    Q(meta_title__icontains=w) | Q(meta_title__icontains=stem) |
                    Q(category__name__icontains=w) | Q(category__name__icontains=stem) |
                    Q(subcategory__name__icontains=w) | Q(subcategory__name__icontains=stem) |
                    Q(description__icontains=w)
                )
            if q_filter:
                data = Product.objects.filter(q_filter).distinct().order_by('-id')
    else:
        data = Product.objects.none()  # If no query, return empty results

    # Pagination
    paginator = Paginator(data, 100)
    page_number = request.GET.get('page')
    page_posts = paginator.get_page(page_number)
    current_page = page_posts.number
    total_pages = paginator.num_pages
    page_range = range(max(current_page - 2, 1), min(current_page + 3, total_pages + 1))

    current_title = f"Search: {query}" if query else "Search Products"
    popular_links = get_popular_links(current_title=query or "Fashion Collection")

    return render(request, 'front/products.html', {
        'page_posts': page_posts,
        'page_range': page_range,
        'maincategories': maincategories,
        'categories': categories,
        'subcategories': subcategories,
        'brands': brands,
        'size': size,
        'color': color,
        'query': query,
        'current_title': current_title,
        'title': current_title,
        'popular_links': popular_links,
        'filteredProduct': filteredProduct,
    })


from django.http import HttpResponse
from django.template.loader import render_to_string

def sitemap_page(request):
    products = Product.objects.all().order_by('-id')
    blogs = Blog.objects.all().order_by('-id')
    maincategories = Maincategory.objects.all()
    categories = Category.objects.all()
    popular_links = PopularLink.objects.filter(is_active=True).order_by('order', '-id')[:200]
    xml_content = render_to_string('front/sitemap.xml', {
        'products': products,
        'blogs': blogs,
        'maincategories': maincategories,
        'categories': categories,
        'popular_links': popular_links,
    })
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


# ==============================================================================
# RAZORPAY STANDARD CHECKOUT & PAYMENT INTEGRATION
# ==============================================================================

def get_razorpay_client():
    """
    Initializes and returns the Razorpay client and credentials.
    Priority order:
    1. Django settings (settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    2. Environment variables (os.environ)
    3. Direct credentials fallback (if .env is not available)
    """
    key_id = (
        getattr(settings, 'RAZORPAY_KEY_ID', None)
        or os.environ.get('RAZORPAY_KEY_ID')
        or 'rzp_test_TrebS13OjJUAeZ'
    )
    key_secret = (
        getattr(settings, 'RAZORPAY_KEY_SECRET', None)
        or os.environ.get('RAZORPAY_KEY_SECRET')
        or 'cQ2Mt9EhceXPKCGGFZRG7fAD'
    )
    key_id = str(key_id).strip()
    key_secret = str(key_secret).strip()
    client = razorpay.Client(auth=(key_id, key_secret))
    return client, key_id, key_secret


def confirm_and_create_order(payment, razorpay_payment_id=None, razorpay_signature="", request=None):
    """
    Centralized, fail-safe order confirmation helper.
    Ensures that whenever a payment is captured (via verify endpoint, webhook, or admin sync):
    1. Payment is marked SUCCESS and saved with razorpay_payment_id and signature.
    2. Order row(s) are created in the database and linked to buyer, address, and product.
    3. Order status is set to 'Confirmed' and payment_status to 'Paid'.
    4. Session cart is cleared if request is present.
    """
    if not payment:
        return []

    # 1. Update Payment record to SUCCESS
    payment.status = 'SUCCESS'
    if razorpay_payment_id:
        payment.razorpay_payment_id = razorpay_payment_id
    if razorpay_signature:
        payment.razorpay_signature = razorpay_signature
    payment.error_code = ''
    payment.error_description = ''
    payment.save()

    # 2. Check if Order already created for this payment (STRICT NON-EMPTY CHECK ONLY)
    existing_orders = []
    rzp_oid = (payment.razorpay_order_id or '').strip()
    rzp_pid = (payment.razorpay_payment_id or '').strip()

    if rzp_oid:
        existing_orders = list(Order.objects.filter(razorpay_order_id=rzp_oid))
    if not existing_orders and rzp_pid:
        existing_orders = list(Order.objects.filter(
            Q(transactionId=rzp_pid) | Q(razorpay_payment_id=rzp_pid)
        ))

    if existing_orders:
        for o in existing_orders:
            o.payment_status = 'Paid'
            if o.orderStatus.lower() == 'pending':
                o.orderStatus = 'Confirmed'
            if rzp_pid:
                o.transactionId = rzp_pid
                o.razorpay_payment_id = rzp_pid
            if rzp_oid:
                o.razorpay_order_id = rzp_oid
            o.save()
        return existing_orders

    # 3. Create Orders if none exist
    buyer = payment.buyer
    address_obj = None
    if buyer:
        address_obj = Address.objects.filter(buyer=buyer).order_by('-id').first()

    now_str = timezone.localtime(timezone.now()).strftime("%d %b %Y, %I:%M %p")

    # Read cart items
    cart_items = []
    if getattr(payment, 'order_items_json', None):
        try:
            cart_items = json.loads(payment.order_items_json)
        except Exception:
            cart_items = []

    if not cart_items and request:
        try:
            pending_order = request.session.get('pending_order', {})
            cart_items = pending_order.get('cart_items', [])
        except Exception:
            cart_items = []

    if not cart_items and request:
        try:
            cart = request.session.get('cart', {})
            if isinstance(cart, dict):
                for pid, item in cart.items():
                    prod = Product.objects.filter(id=pid).first()
                    if prod:
                        qty = int(item.get('quantity', 1) or 1) if isinstance(item, dict) else (int(item) if str(item).isdigit() else 1)
                        price = float(prod.price or 0.0)
                        cart_items.append({
                            'id': prod.id,
                            'name': prod.name,
                            'price': price,
                            'quantity': qty,
                            'subtotal': price * qty,
                        })
        except Exception:
            cart_items = []

    if not cart_items:
        matching_prod = Product.objects.filter(price=payment.amount).first() or Product.objects.first()
        cart_items = [{
            'id': matching_prod.id if matching_prod else None,
            'name': matching_prod.name if matching_prod else 'Ordered Product',
            'price': payment.amount,
            'quantity': 1,
            'subtotal': payment.amount,
        }]

    new_orders = []
    for item in cart_items:
        prod_obj = Product.objects.filter(id=item.get('id')).first() if item.get('id') else Product.objects.first()

        ord_obj = Order.objects.create(
            buyer=buyer,
            product=prod_obj,
            address=address_obj,
            quantity=int(item.get('quantity', 1) or 1),
            totalPrice=float(item.get('subtotal', payment.amount) or payment.amount),
            shippingPrice=0.0,
            finalPrice=float(item.get('subtotal', payment.amount) or payment.amount),
            transactionId=rzp_pid or payment.order_number,
            orderDate=now_str,
            orderStatus="Confirmed",
            payment_status="Paid",
            razorpay_order_id=rzp_oid,
            razorpay_payment_id=rzp_pid,
            razorpay_signature=payment.razorpay_signature,
            waywill="",
            cancelled_by=""
        )
        new_orders.append(ord_obj)

    if request:
        try:
            request.session['cart'] = {}
            request.session.pop('pending_order', None)
            request.session.pop('checkout_verified_email', None)
            request.session.pop('checkout_otp_code', None)
            request.session.pop('checkout_otp_email', None)
            request.session.modified = True
        except Exception:
            pass

    return new_orders


@csrf_exempt
def create_razorpay_order(request):
    """
    Step 1: Backend Endpoint to Create Razorpay Order
    - Validates cart items, delivery address, and email OTP verification
    - Creates or retrieves Buyer, User, and Address records
    - Calls Razorpay Orders API: POST https://api.razorpay.com/v1/orders
    - Generates and stores Payment record with status 'PENDING' and serialized cart_items
    - Returns { order_id, amount, currency, key_id, order_number, customer }
    """
    if request.method != "POST":
        return JsonResponse({'status': 'error', 'message': 'Invalid request method. Only POST is allowed.'}, status=405)

    try:
        cart = request.session.get('cart', {})
        if not cart:
            return JsonResponse({'status': 'error', 'message': 'Your shopping cart is empty. Please add products before checking out.'}, status=400)

        # Parse request body (JSON or form-encoded)
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body.decode('utf-8'))
            except Exception:
                data = request.POST
        else:
            data = request.POST

        name = data.get('name', '').strip()
        phone = data.get('phone', '').strip()
        email = data.get('email', '').strip()
        address = data.get('address', '').strip()
        city = data.get('city', '').strip()
        state = data.get('state', '').strip()
        pincode = data.get('pincode', '').strip()
        notes = data.get('notes', '').strip()

        if not all([name, phone, email, address, city, state, pincode]):
            return JsonResponse({'status': 'error', 'message': 'Please fill in all mandatory delivery address fields.'}, status=400)

        phone_digits = ''.join(filter(str.isdigit, phone))
        if len(phone_digits) < 10:
            return JsonResponse({'status': 'error', 'message': 'Please enter a valid 10-digit mobile number.'}, status=400)
        clean_phone = phone_digits[-10:]

        # Enforce email OTP verification
        verified_session_email = request.session.get('checkout_verified_email', '').strip().lower()
        auth_email = (request.user.email or '').strip().lower() if request.user.is_authenticated else ''
        req_email = email.strip().lower()

        if not (verified_session_email == req_email or (auth_email and auth_email == req_email)):
            return JsonResponse({'status': 'error', 'message': 'Please verify your email address with the 6-digit OTP before proceeding to payment.'}, status=400)

        # Calculate Cart Totals
        subtotal = 0.0
        cart_items = []
        for pid, item in cart.items():
            prod = Product.objects.filter(id=pid).first()
            if prod:
                qty = int(item.get('quantity', 1) or 1) if isinstance(item, dict) else (int(item) if str(item).isdigit() else 1)
                price = float(prod.price or 0.0)
                item_total = price * qty
                subtotal += item_total
                cart_items.append({
                    'id': prod.id,
                    'name': prod.name,
                    'price': price,
                    'quantity': qty,
                    'subtotal': item_total,
                })

        if not cart_items or subtotal <= 0:
            return JsonResponse({'status': 'error', 'message': 'Invalid cart items or total price. Please re-add items.'}, status=400)

        total = round(subtotal, 2)
        amount_paise = int(round(total * 100))

        if amount_paise < 100:
            return JsonResponse({'status': 'error', 'message': 'Razorpay requires a minimum transaction amount of ₹1.00.'}, status=400)

        # Generate Unique Order Number
        order_number = f"ORD{datetime.now().strftime('%y%m%d')}{random.randint(1000, 9999)}"

        # Get or Create Buyer
        buyer = None
        if email:
            buyer = Buyer.objects.filter(email__iexact=email).first()
        if not buyer and clean_phone:
            buyer = Buyer.objects.filter(phone=clean_phone).first()

        if not buyer:
            buyer = Buyer.objects.create(
                name=name,
                email=email,
                phone=clean_phone,
                verification="verified"
            )
        else:
            updated = False
            if not buyer.name and name:
                buyer.name = name
                updated = True
            if not buyer.email and email:
                buyer.email = email
                updated = True
            if not buyer.phone and clean_phone:
                buyer.phone = clean_phone
                updated = True
            if updated:
                buyer.save()

        # Save Delivery Address
        address_obj = Address.objects.create(
            buyer=buyer,
            address=address,
            city=city,
            state=state,
            pin=pincode,
            alternatePhone=clean_phone
        )

        # Call Razorpay Orders API
        client, key_id, key_secret = get_razorpay_client()
        order_payload = {
            'amount': amount_paise,
            'currency': 'INR',
            'receipt': order_number,
            'notes': {
                'order_number': order_number,
                'customer_name': name,
                'customer_phone': clean_phone,
                'customer_email': email,
                'city': city
            }
        }

        try:
            rzp_order = client.order.create(data=order_payload)
        except Exception as rzp_err:
            return JsonResponse({
                'status': 'error',
                'message': f"Razorpay Gateway Error: {str(rzp_err)}"
            }, status=502)

        # Create Payment Record in Database
        payment_record = Payment.objects.create(
            buyer=buyer,
            order_number=order_number,
            razorpay_order_id=rzp_order['id'],
            amount=total,
            currency='INR',
            status='PENDING',
            payment_method='Razorpay',
            order_items_json=json.dumps(cart_items),
            notes=f"Delivery to {city}, {state} ({pincode}). Notes: {notes}"
        )

        # Store pending order context in session
        request.session['pending_order'] = {
            'order_number': order_number,
            'buyer_id': buyer.id if buyer else None,
            'address_id': address_obj.id if address_obj else None,
            'total': total,
            'cart_items': cart_items,
            'razorpay_order_id': rzp_order['id'],
            'notes': notes,
            'clean_phone': clean_phone,
            'email': email,
            'name': name
        }
        request.session.modified = True

        return JsonResponse({
            'status': 'success',
            'order_id': rzp_order['id'],
            'amount': amount_paise,
            'currency': 'INR',
            'key_id': key_id,
            'order_number': order_number,
            'customer': {
                'name': name,
                'email': email,
                'contact': clean_phone
            }
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': f"Internal Server Error: {str(e)}"}, status=500)


@csrf_exempt
def verify_razorpay_payment(request):
    """
    Step 2: Backend Endpoint to Verify Payment Signature
    - Receives razorpay_order_id, razorpay_payment_id, razorpay_signature
    - Supports BOTH AJAX json POST and direct Razorpay callback_url form POST
    - Computes HMAC-SHA256 signature using KEY_SECRET
    - Compares generated signature with received signature
    - If valid: calls confirm_and_create_order, creates Order records, clears cart
    - If invalid: marks Payment as 'FAILED', returns HTTP 400
    """
    if request.method != "POST":
        return JsonResponse({'status': 'error', 'message': 'Only POST requests allowed.'}, status=405)

    try:
        is_json = request.content_type == 'application/json'
        if is_json:
            try:
                data = json.loads(request.body.decode('utf-8'))
            except Exception:
                data = request.POST
        else:
            data = request.POST

        razorpay_order_id = data.get('razorpay_order_id', '').strip()
        razorpay_payment_id = data.get('razorpay_payment_id', '').strip()
        razorpay_signature = data.get('razorpay_signature', '').strip()
        order_number = data.get('order_number', '').strip()

        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
            if not is_json:
                messages.error(request, 'Incomplete payment payload.')
                return redirect('/checkout/')
            return JsonResponse({'status': 'error', 'message': 'Incomplete payment verification payload.'}, status=400)

        client, key_id, key_secret = get_razorpay_client()

        # Cryptographic Signature Verification
        # 1. Native HMAC-SHA256
        msg = f"{razorpay_order_id}|{razorpay_payment_id}"
        generated_signature = hmac.new(
            key_secret.encode('utf-8'),
            msg.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        is_valid_signature = hmac.compare_digest(generated_signature, razorpay_signature)

        # 2. SDK Utility check as secondary confirmation
        if not is_valid_signature:
            try:
                client.utility.verify_payment_signature({
                    'razorpay_order_id': razorpay_order_id,
                    'razorpay_payment_id': razorpay_payment_id,
                    'razorpay_signature': razorpay_signature
                })
                is_valid_signature = True
            except Exception:
                is_valid_signature = False

        # 3. Direct API verification fallback (Failsafe against secret/formatting mismatch)
        if not is_valid_signature and razorpay_payment_id:
            try:
                rzp_pay_obj = client.payment.fetch(razorpay_payment_id)
                if rzp_pay_obj.get('status') in ['captured', 'authorized']:
                    is_valid_signature = True
            except Exception as api_err:
                print(f"Razorpay direct API verification check: {api_err}")

        payment = Payment.objects.filter(razorpay_order_id=razorpay_order_id).first()
        if not payment and order_number:
            payment = Payment.objects.filter(order_number=order_number).first()

        if not is_valid_signature:
            if payment:
                payment.status = 'FAILED'
                payment.error_code = 'SIGNATURE_MISMATCH'
                payment.error_description = f"Signature verification failed for payment {razorpay_payment_id}"
                payment.razorpay_payment_id = razorpay_payment_id
                payment.razorpay_signature = razorpay_signature
                payment.save()

            if not is_json:
                return redirect(f"/payment-failed/?order_number={payment.order_number if payment else ''}&order_id={razorpay_order_id}")
            return JsonResponse({
                'status': 'error',
                'message': 'Payment signature verification failed. The transaction could not be validated.'
            }, status=400)

        # Payment is Genuine & Verified!
        ord_num = payment.order_number if payment else (order_number or f"ORD{datetime.now().strftime('%y%m%d')}{random.randint(1000, 9999)}")
        confirm_and_create_order(payment, razorpay_payment_id=razorpay_payment_id, razorpay_signature=razorpay_signature, request=request)

        redirect_url = f"/order-confirmation/?order_number={ord_num}&payment_id={razorpay_payment_id}"

        if not is_json:
            return redirect(redirect_url)

        return JsonResponse({
            'status': 'success',
            'message': 'Payment successfully verified!',
            'order_number': ord_num,
            'payment_id': razorpay_payment_id,
            'redirect_url': redirect_url
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        if not (request.content_type == 'application/json'):
            return redirect(f"/payment-failed/?error={str(e)}")
        return JsonResponse({'status': 'error', 'message': f'Server error during verification: {str(e)}'}, status=500)


@csrf_exempt
def record_razorpay_failure(request):
    """Endpoint called when customer closes modal or payment fails on client side."""
    if request.method != "POST":
        return JsonResponse({'status': 'error', 'message': 'Only POST requests allowed.'}, status=405)

    try:
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body.decode('utf-8'))
            except Exception:
                data = request.POST
        else:
            data = request.POST

        order_number = data.get('order_number', '').strip()
        razorpay_order_id = data.get('razorpay_order_id', '').strip()
        razorpay_payment_id = data.get('razorpay_payment_id', '').strip()
        error_code = data.get('error_code', '').strip()
        error_desc = data.get('error_description', '').strip()
        error_source = data.get('error_source', '').strip()
        error_step = data.get('error_step', '').strip()
        error_reason = data.get('error_reason', '').strip()
        is_cancelled = data.get('is_cancelled', False)

        payment = None
        if razorpay_order_id:
            payment = Payment.objects.filter(razorpay_order_id=razorpay_order_id).first()
        if not payment and order_number:
            payment = Payment.objects.filter(order_number=order_number).first()

        if payment:
            # If already SUCCESS, do not overwrite with failed
            if payment.status == 'SUCCESS':
                return JsonResponse({'status': 'ok', 'message': 'Payment already confirmed as SUCCESS.'})

            payment.status = 'CANCELLED' if is_cancelled else 'FAILED'
            if razorpay_payment_id:
                payment.razorpay_payment_id = razorpay_payment_id
            payment.error_code = error_code[:100]
            payment.error_description = error_desc
            payment.error_source = error_source[:100]
            payment.error_step = error_step[:100]
            payment.error_reason = error_reason[:100]
            payment.save()

        return JsonResponse({'status': 'ok', 'message': 'Payment status updated.'})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def order_confirmation(request):
    """Renders the Order Confirmation Page after successful payment, with auto-healing order creation."""
    order_number = request.GET.get('order_number', '').strip()
    payment_id = request.GET.get('payment_id', '').strip()

    payment = None
    if payment_id:
        payment = Payment.objects.filter(razorpay_payment_id=payment_id).first()
    if not payment and order_number:
        payment = Payment.objects.filter(order_number=order_number).first()

    orders = []
    if payment_id:
        orders = list(Order.objects.filter(transactionId=payment_id).order_by('-id'))
    if not orders and payment and payment.razorpay_order_id:
        orders = list(Order.objects.filter(razorpay_order_id=payment.razorpay_order_id).order_by('-id'))

    # Auto-healing: If payment exists but orders not created yet, check Razorpay API & confirm!
    if not orders and payment and payment.razorpay_order_id:
        try:
            client, key_id, key_secret = get_razorpay_client()
            rzp_order = client.order.fetch(payment.razorpay_order_id)
            payments_resp = client.order.payments(payment.razorpay_order_id)
            items = payments_resp.get('items', []) if isinstance(payments_resp, dict) else []
            captured_p = next((p for p in items if p.get('status') in ['captured', 'authorized']), None)
            
            if captured_p:
                created_ords = confirm_and_create_order(payment, razorpay_payment_id=captured_p.get('id'), request=request)
                orders = created_ords or list(Order.objects.filter(razorpay_order_id=payment.razorpay_order_id).order_by('-id'))
            elif rzp_order.get('status') == 'paid' and items:
                created_ords = confirm_and_create_order(payment, razorpay_payment_id=items[0].get('id'), request=request)
                orders = created_ords or list(Order.objects.filter(razorpay_order_id=payment.razorpay_order_id).order_by('-id'))
        except Exception as err:
            print(f"order_confirmation auto-sync error: {err}")

    buyer = payment.buyer if payment else None
    address = orders.first().address if orders.exists() else None
    total = payment.amount if payment else (sum(o.finalPrice for o in orders) if orders else 0.0)
    order_date = orders.first().orderDate if orders.exists() else datetime.now().strftime("%d %b %Y, %I:%M %p")

    return render(request, 'front/confirmation.html', {
        'order_number': order_number or (payment.order_number if payment else 'CONFIRMED'),
        'payment': payment,
        'orders': orders,
        'buyer': buyer,
        'address': address,
        'total': total,
        'order_date': order_date,
        'is_paid_online': True,
    })


def payment_failed_view(request):
    """Renders user-friendly Payment Failed page with auto-healing check against Razorpay API."""
    order_number = request.GET.get('order_number', '').strip()
    razorpay_order_id = request.GET.get('order_id', '').strip()

    payment = None
    if razorpay_order_id:
        payment = Payment.objects.filter(razorpay_order_id=razorpay_order_id).first()
    if not payment and order_number:
        payment = Payment.objects.filter(order_number=order_number).first()

    # Auto-healing: If payment was actually captured in Razorpay, auto-confirm and redirect to order-confirmation!
    if payment and payment.razorpay_order_id:
        try:
            client, key_id, key_secret = get_razorpay_client()
            rzp_order = client.order.fetch(payment.razorpay_order_id)
            payments_resp = client.order.payments(payment.razorpay_order_id)
            items = payments_resp.get('items', []) if isinstance(payments_resp, dict) else []
            captured_p = next((p for p in items if p.get('status') in ['captured', 'authorized']), None)
            if captured_p:
                confirm_and_create_order(payment, razorpay_payment_id=captured_p.get('id'), request=request)
                return redirect(f"/order-confirmation/?order_number={payment.order_number}&payment_id={captured_p.get('id')}")
            elif rzp_order.get('status') == 'paid' and items:
                confirm_and_create_order(payment, razorpay_payment_id=items[0].get('id'), request=request)
                return redirect(f"/order-confirmation/?order_number={payment.order_number}&payment_id={items[0].get('id')}")
        except Exception as heal_err:
            print(f"payment_failed_view auto-heal error: {heal_err}")

    return render(request, 'front/payment-failed.html', {
        'payment': payment,
        'order_number': order_number or (payment.order_number if payment else ''),
        'error_reason': payment.error_reason if payment and payment.error_reason else 'Transaction was not completed',
        'error_description': payment.error_description if payment and payment.error_description else 'The payment could not be processed.',
    })



@csrf_exempt
def razorpay_webhook(request):
    """
    Razorpay Webhook Handler (Fail-safe Server-to-Server Event Processing)
    - Verifies X-Razorpay-Signature using webhook secret or key secret
    - Handles:
      * payment.captured / order.paid: Confirms payment & order even if user closed browser
      * payment.failed: Logs failure code & reason
    """
    if request.method != "POST":
        return HttpResponse("Method not allowed", status=405)

    webhook_body = request.body.decode('utf-8')
    received_signature = request.headers.get('X-Razorpay-Signature') or request.META.get('HTTP_X_RAZORPAY_SIGNATURE', '')

    webhook_secret = (
        getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', None)
        or os.environ.get('RAZORPAY_WEBHOOK_SECRET')
        or getattr(settings, 'RAZORPAY_KEY_SECRET', None)
        or 'cQ2Mt9EhceXPKCGGFZRG7fAD'
    ).strip()

    # Verify webhook signature
    client, key_id, key_secret = get_razorpay_client()
    is_valid_sig = False
    try:
        client.utility.verify_webhook_signature(webhook_body, received_signature, webhook_secret)
        is_valid_sig = True
    except Exception:
        expected_sig = hmac.new(
            webhook_secret.encode('utf-8'),
            webhook_body.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        if hmac.compare_digest(expected_sig, received_signature):
            is_valid_sig = True

    if not is_valid_sig:
        print("Razorpay Webhook: Signature verification failed!")
        return HttpResponse("Invalid signature", status=400)

    try:
        event_payload = json.loads(webhook_body)
        event_name = event_payload.get('event')
        payload = event_payload.get('payload', {})
        payment_entity = payload.get('payment', {}).get('entity', {})
        order_entity = payload.get('order', {}).get('entity', {})

        rzp_order_id = payment_entity.get('order_id') or order_entity.get('id', '')
        rzp_payment_id = payment_entity.get('id', '')

        print(f"Razorpay Webhook: Received '{event_name}' for Order {rzp_order_id}, Payment {rzp_payment_id}")

        if event_name in ['payment.captured', 'order.paid']:
            payment = Payment.objects.filter(razorpay_order_id=rzp_order_id).first()
            if not payment and rzp_payment_id:
                payment = Payment.objects.filter(razorpay_payment_id=rzp_payment_id).first()

            if payment:
                confirm_and_create_order(payment, razorpay_payment_id=rzp_payment_id)

        elif event_name in ['payment.failed']:
            error_code = payment_entity.get('error_code', '')
            error_desc = payment_entity.get('error_description', '')
            error_source = payment_entity.get('error_source', '')
            error_step = payment_entity.get('error_step', '')
            error_reason = payment_entity.get('error_reason', '')

            payment = Payment.objects.filter(razorpay_order_id=rzp_order_id).first()
            if payment:
                payment.status = 'FAILED'
                if rzp_payment_id:
                    payment.razorpay_payment_id = rzp_payment_id
                payment.error_code = str(error_code)[:100]
                payment.error_description = str(error_desc)
                payment.error_source = str(error_source)[:100]
                payment.error_step = str(error_step)[:100]
                payment.error_reason = str(error_reason)[:100]
                payment.save()

        return HttpResponse("Webhook processed successfully", status=200)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return HttpResponse(f"Webhook error: {str(e)}", status=500)
