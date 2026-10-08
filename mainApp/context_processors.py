from .models import Supercategory, Maincategory, Category, Subcategory

def navigation_context(request):
    """
    Context processor to supply category hierarchy to all templates.
    """
    supercats = Supercategory.objects.filter(slug__in=['women', 'men', 'kids']).order_by('id')
    if not supercats.exists():
        supercats = Supercategory.objects.all()[:5]

    return {
        'nav_supercategories': supercats,
        'all_supercategories': Supercategory.objects.all(),
        'all_maincategories': Maincategory.objects.select_related('supercategory').all(),
        'all_categories': Category.objects.select_related('maincategory').all(),
        'all_subcategories': Subcategory.objects.select_related('category').all(),
    }
