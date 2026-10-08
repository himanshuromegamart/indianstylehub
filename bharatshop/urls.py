from django.contrib import admin
from django.urls import path
from mainApp import views
from mainApp import backend
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',views.home_page),
    path('search/',views.search_product),
    path('men/',views.men_home_page),
    path('kid/',views.kid_home_page),
    path('product/<str:cat>/',views.product_page),
    path('category/<str:cat>/',views.category_page),
    path('product-details/<str:name>/<int:id>/',views.product_detail),
    # path('dynamic-filter/',views.dynamic_filter),
    path('add-to-cart/',views.add_to_cart),
    path('get-cart-data/',views.get_cart_data),
    path('update-cart/',views.update_cart),
    path('remove-from-cart/',views.remove_from_cart),
    path('cart/',views.cart_page),
    path('wishlist/',views.wishlist_page),
    path('compare/',views.compare_page),
    path('checkout/',views.checkout_page),
    path('blog/',views.blog_page),
    path('blog-details/<str:ops>/',views.blog_details_page),
    
    path('about-us/',views.about_us),
    path('brands/',views.brand_page),
    path('contact/',views.contact_page),
    path('faq/',views.faq),
    path('add-enquiry/',views.add_enquiry),

    #User Dashboard
    path('login/',views.login_page),
    path('logout/',views.logout_page),
    path('register/',views.register),
    path('my-account/',views.my_account),
    path('my-account-address/',views.my_account_address),
    path('my-account-edit/',views.my_account_edit),
    path('my-account-orders/',views.my_account_order),
    path('my-account-orders-details/',views.my_account_order_details),
    path('order-tracking/',views.order_tracking),
    path('payment-confirmation/',views.payment_confirmation),
    path('payment-failure/',views.payment_failure),
    path('filter/',views.web_filter),
    path('sitemap.xml/',views.sitemap_page),
    path('robots.txt/',views.robots_txt),

    #Backend
    #Image Upload
    path('prduct-store/',backend.product_store),
    path('admin-login/',backend.admin_login),
    path('admin-dashboard/',backend.admin_dashboard),


    #Slider
    path('slider/',backend.slider_page),
    path('delete-slider/<int:id>/',backend.delete_slider),

    #Maincategory
    path('supercategory/',backend.supercategory_page),
    path('add-supercategory/',backend.add_supercategory),
    path('update-supercategory/<int:id>/',backend.update_supercategory),
    path('delete-supercategory/<int:id>/',backend.delete_supercategory),

    #Maincategory
    path('maincategory/',backend.maincategory_page),
    path('add-maincategory/',backend.add_maincategory),
    path('update-maincategory/<int:id>/',backend.update_maincategory),
    path('delete-maincategory/<int:id>/',backend.delete_maincategory),

    #Category
    path('category/',backend.category_page),
    path('add-category/',backend.add_category),
    path('update-category/<int:id>/',backend.update_category),
    path('delete-category/<int:id>/',backend.delete_category),

    #Subcategory
    path('subcategory/',backend.subcategory_page),
    path('add-subcategory/',backend.add_subcategory),
    path('update-subcategory/<int:id>/',backend.update_subcategory),
    path('delete-subcategory/<int:id>/',backend.delete_subcategory),
    
    #Brand bha123se
    path('brand/',backend.brand_page),
    path('add-brand/',backend.add_brand),
    path('update-brand/<int:id>/',backend.update_brand),
    path('delete-brand/<int:id>/',backend.delete_brand),
    path('clear-session/',backend.clear_session),
    
    #Color
    path('color/',backend.color_page),
    path('add-color/',backend.add_color),
    path('update-color/<int:id>/',backend.update_color),
    path('delete-color/<int:id>/',backend.delete_color),
    
    #Color
    path('size/',backend.size_page),
    path('add-size/',backend.add_size),
    path('update-size/<int:id>/',backend.update_size),
    path('delete-size/<int:id>/',backend.delete_size),
    
    #Product
    path('product/',backend.product_page),
    path('add-product/',backend.add_product),
    path('update-product/<int:id>/<int:pn>/',backend.update_product),
    path('duplicate-product/<int:id>/<int:pn>/',backend.duplicate_product),
    path('delete-product/<int:id>/',backend.delete_product),
    #updating offers
    path('update-product-offers/<int:id>/<str:ops>/',backend.update_product_offers),

    #Enquiry
    path('admin-enquiry/',backend.enquiry),
    path('enquiry-details/<int:id>/',backend.enquiry_details),
    
    #Blog
    path('admin-blog/',backend.admin_blog),
    path('admin-add-blog/',backend.admin_add_blog),
    path('admin-update-blog/<int:id>/',backend.admin_update_blog),
    path('admin-delete-blog/<int:id>/',backend.admin_delete_blog),
    
    #Slider
    path('gallery/',backend.gallery_page),
    path('delete-gallery/<int:id>/',backend.delete_gallery),

    path('<str:supercat>/<str:mcat>/<str:cat>/<str:scat>/', views.dynamic_category_view, name='subcategory_view'),
    path('<str:supercat>/<str:mcat>/<str:cat>/', views.dynamic_category_view, name='category_view'),
    path('<str:supercat>/<str:mcat>/', views.dynamic_category_view, name='maincategory_view'),
    path('<str:supercat>/', views.dynamic_category_view, name='supercategory_view'),
]+static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)+static(settings.STATIC_URL,document_root=settings.STATIC_ROOT)

