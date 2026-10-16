from django.core.management.base import BaseCommand
from mainApp.models import Supercategory, Maincategory, Category, Subcategory, Product, PopularLink

class Command(BaseCommand):
    help = "Seeds test data for Bags, Handbags, and Popular Links (SEO)"

    def handle(self, *args, **options):
        self.stdout.write("Seeding Bags & Handbags SEO test data...")

        # 1. Supercategory
        women, _ = Supercategory.objects.get_or_create(
            slug="women",
            defaults={"name": "Women", "title": "Women Fashion Collection"}
        )

        # 2. Maincategory
        bags_mcat, _ = Maincategory.objects.get_or_create(
            slug="bags-luggage",
            defaults={
                "name": "Bags & Luggage",
                "supercategory": women,
                "title": "Bags & Luggage Collection"
            }
        )
        if not bags_mcat.supercategory:
            bags_mcat.supercategory = women
            bags_mcat.save()

        # 3. Category
        handbags_cat = Category.objects.filter(slug="handbags").first()
        if not handbags_cat:
            handbags_cat = Category.objects.filter(name__icontains="handbag").first()
        if not handbags_cat:
            handbags_cat = Category.objects.create(
                name="Handbags",
                slug="handbags",
                maincategory=bags_mcat,
                title="Designer Handbags Collection"
            )

        # 4. Subcategory
        tote_subcat = Subcategory.objects.filter(slug="tote-handbags").first()
        if not tote_subcat:
            tote_subcat = Subcategory.objects.filter(name__icontains="tote").first()
        if not tote_subcat:
            tote_subcat = Subcategory.objects.create(
                name="Tote Handbags",
                slug="tote-handbags",
                category=handbags_cat,
                title="Trendy Tote Handbags"
            )

        # 5. Sample Products (if none exist)
        if not Product.objects.filter(category=handbags_cat).exists():
            Product.objects.create(
                name="Luxury Vegan Leather Handbag",
                price=1499,
                base_price=2499,
                discount=40,
                supercategory=women,
                maincategory=bags_mcat,
                category=handbags_cat,
                subcategory=tote_subcat,
                description="Premium handcrafted vegan leather handbag with gold accents.",
                image1="/static/assets/img/image.png"
            )
            Product.objects.create(
                name="Designer Classic Tote Bag",
                price=1199,
                base_price=1999,
                discount=40,
                supercategory=women,
                maincategory=bags_mcat,
                category=handbags_cat,
                subcategory=tote_subcat,
                description="Spacious multi-compartment tote handbag for daily fashion.",
                image1="/static/assets/img/image.png"
            )
            Product.objects.create(
                name="Embossed Shoulder Handbag",
                price=899,
                base_price=1499,
                discount=40,
                supercategory=women,
                maincategory=bags_mcat,
                category=handbags_cat,
                subcategory=tote_subcat,
                description="Elegant embossed shoulder handbag with adjustable strap.",
                image1="/static/assets/img/image.png"
            )
            self.stdout.write(self.style.SUCCESS("Created 3 sample Handbag products for testing."))

        # 6. Seed Sample Popular SEO Links
        sample_links = [
            {
                "title": "Luxury Handbags Manufacturer & Wholesaler in Maharashtra",
                "url": "/search/?query=Handbags+Maharashtra",
                "state": "Maharashtra",
                "category": handbags_cat,
                "subcategory": None,
                "order": 1
            },
            {
                "title": "Designer Handbags Supplier & Exporter in Delhi NCR",
                "url": "/search/?query=Handbags+Delhi",
                "state": "Delhi",
                "category": handbags_cat,
                "subcategory": None,
                "order": 2
            },
            {
                "title": "Handbags Wholesale Market in Surat, Gujarat",
                "url": "/search/?query=Handbags+Gujarat",
                "state": "Gujarat",
                "category": handbags_cat,
                "subcategory": None,
                "order": 3
            },
            {
                "title": "Bridal Handbags Manufacturer in Jaipur, Rajasthan",
                "url": "/search/?query=Handbags+Rajasthan",
                "state": "Rajasthan",
                "category": handbags_cat,
                "subcategory": None,
                "order": 4
            },
            {
                "title": "Leather Handbags Wholesale Dealer in Kolkata, West Bengal",
                "url": "/search/?query=Handbags+West+Bengal",
                "state": "West Bengal",
                "category": handbags_cat,
                "subcategory": None,
                "order": 5
            },
            {
                "title": "Trending Tote Handbags in Bengaluru, Karnataka",
                "url": "/search/?query=Handbags+Karnataka",
                "state": "Karnataka",
                "category": handbags_cat,
                "subcategory": tote_subcat,
                "order": 6
            },
            {
                "title": "Handbags Supplier & Wholesaler in Lucknow, Uttar Pradesh",
                "url": "/search/?query=Handbags+Uttar+Pradesh",
                "state": "Uttar Pradesh",
                "category": handbags_cat,
                "subcategory": None,
                "order": 7
            },
            {
                "title": "Partywear Handbags Wholesale in Ludhiana, Punjab",
                "url": "/search/?query=Handbags+Punjab",
                "state": "Punjab",
                "category": handbags_cat,
                "subcategory": None,
                "order": 8
            },
            {
                "title": "Nari Fashion Luxury Handbags Nationwide Collection",
                "url": "/women/bags-luggage/handbags/",
                "state": "All India",
                "category": handbags_cat,
                "subcategory": None,
                "order": 9
            },
        ]

        created_count = 0
        for item in sample_links:
            obj, created = PopularLink.objects.get_or_create(
                title=item["title"],
                defaults={
                    "url": item["url"],
                    "state": item["state"],
                    "category": item["category"],
                    "subcategory": item["subcategory"],
                    "order": item["order"],
                    "is_active": True
                }
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {created_count} custom Popular Links for Handbags!"))

        # 7. Seed Home Page Popular Links
        home_links = [
            {
                "title": "Surat Sarees & Wholesale Textile Market in Gujarat",
                "url": "/women/",
                "state": "Gujarat",
                "show_on_home": True,
                "order": 1
            },
            {
                "title": "Chandni Chowk Bridal Lehengas & Ethnic Wear in Delhi",
                "url": "/women/",
                "state": "Delhi",
                "show_on_home": True,
                "order": 2
            },
            {
                "title": "Mumbai Designer Handbags & Western Fashion in Maharashtra",
                "url": "/women/bags-luggage/handbags/",
                "state": "Maharashtra",
                "show_on_home": True,
                "order": 3
            },
            {
                "title": "Jaipur Handcrafted Kurtis & Bandhani in Rajasthan",
                "url": "/search/?query=Kurtis",
                "state": "Rajasthan",
                "show_on_home": True,
                "order": 4
            },
            {
                "title": "Lucknow Chikankari Kurtis & Suits in Uttar Pradesh",
                "url": "/search/?query=Kurtis",
                "state": "Uttar Pradesh",
                "show_on_home": True,
                "order": 5
            },
            {
                "title": "Kolkata Traditional Silk Sarees in West Bengal",
                "url": "/women/",
                "state": "West Bengal",
                "show_on_home": True,
                "order": 6
            },
            {
                "title": "Ludhiana Woolen & Partywear Suits in Punjab",
                "url": "/women/",
                "state": "Punjab",
                "show_on_home": True,
                "order": 7
            },
            {
                "title": "Bengaluru Contemporary Fashion & Tote Bags in Karnataka",
                "url": "/women/bags-luggage/handbags/",
                "state": "Karnataka",
                "show_on_home": True,
                "order": 8
            },
            {
                "title": "Hyderabad Festive & Bridal Wear in Telangana",
                "url": "/women/",
                "state": "Telangana",
                "show_on_home": True,
                "order": 9
            },
            {
                "title": "Chennai Pure Kanchipuram Silk Sarees in Tamil Nadu",
                "url": "/women/",
                "state": "Tamil Nadu",
                "show_on_home": True,
                "order": 10
            },
            {
                "title": "Indore Cotton Kurtis & Printed Fabrics in Madhya Pradesh",
                "url": "/search/?query=Kurtis",
                "state": "Madhya Pradesh",
                "show_on_home": True,
                "order": 11
            },
            {
                "title": "Ahmedabad Chaniya Choli & Designer Kurtis in Gujarat",
                "url": "/women/",
                "state": "Gujarat",
                "show_on_home": True,
                "order": 12
            },
        ]

        home_created = 0
        for item in home_links:
            obj, created = PopularLink.objects.get_or_create(
                title=item["title"],
                defaults={
                    "url": item["url"],
                    "state": item["state"],
                    "show_on_home": item["show_on_home"],
                    "order": item["order"],
                    "is_active": True
                }
            )
            if not created and not obj.show_on_home:
                obj.show_on_home = True
                obj.save()
            if created:
                home_created += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {home_created} featured Home Page Popular Links!"))
        self.stdout.write(self.style.SUCCESS(f"Total Popular Links in DB: {PopularLink.objects.count()}"))


