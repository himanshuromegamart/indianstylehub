from .models import Supercategory, Maincategory, Category, Subcategory

def navigation_context(request):
    """
    Context processor to supply category hierarchy to all templates dynamically.
    """
    all_sc = Supercategory.objects.all().order_by('id')
    # Filter out old promotional offer tags if they have no maincategories
    offer_slugs = {'new-arrivals', 'best-sellers', 'top-rated', 'brands-we-love', 'trending', 'the-re-imagined', 'sale'}
    catalog_sc = [sc for sc in all_sc if sc.slug not in offer_slugs or sc.maincategories.exists()]
    if not catalog_sc:
        catalog_sc = list(all_sc)

    return {
        'nav_supercategories': catalog_sc,
        'all_supercategories': all_sc,
        'all_maincategories': Maincategory.objects.select_related('supercategory').all(),
        'all_categories': Category.objects.select_related('maincategory').all(),
        'all_subcategories': Subcategory.objects.select_related('category').all(),
    }
