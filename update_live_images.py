"""
Universal Live Data Updater for Nari Fashion Store (Narifashionstore)
Updates Hero Sliders & Populates SEO Fashion Blogs.
Works BOTH inside Django OR directly via SQLite3 standard library (no dependencies needed).
"""
import os
import sys
import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'db.sqlite3')

BANNER_DATA = [
    {
        'title': 'Festive Ethnic Designer Wear & Sarees',
        'image': 'https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?auto=format&fit=crop&w=1600&h=600&crop=faces,entropy&q=85',
        'link': '/women'
    },
    {
        'title': 'Royal Bridal Lehenga & Party Collection',
        'image': 'https://images.unsplash.com/photo-1617627143750-d86bc21e42bb?auto=format&fit=crop&w=1600&h=600&crop=faces,top&q=85',
        'link': '/women'
    },
    {
        'title': 'Traditional Silk Sarees & Heritage Drape',
        'image': 'https://images.unsplash.com/photo-1610030469983-98e550d6193c?auto=format&fit=crop&w=1600&h=600&crop=top&q=85',
        'link': '/women'
    },
    {
        'title': "Men's Royal Ethnic Kurta & Sherwani",
        'image': 'https://images.unsplash.com/photo-1605518216938-7c31b7b14ad0?auto=format&fit=crop&w=1600&h=600&crop=faces,top&q=85',
        'link': '/men'
    },
    {
        'title': 'Wedding & Festive Special Offers',
        'image': 'https://images.unsplash.com/photo-1566737236500-c8ac43014a67?auto=format&fit=crop&w=1600&h=600&crop=faces,entropy&q=85',
        'link': '/all'
    }
]

BLOG_DATA = [
    {
        'title': 'The Ultimate Saree Draping & Styling Guide for Weddings (2026)',
        'slug': 'ultimate-saree-draping-styling-guide-2026',
        'meta_description': 'Discover trending saree draping styles, silk saree care tips, and wedding occasion styling secrets from Nari Fashion Store experts.',
        'description': '<p>Sarees represent the quintessence of Indian elegance. Whether it is an opulent Kanjivaram, a regal Banarasi, or a lightweight Georgette, mastering the perfect drape elevates your overall aesthetic. In this guide, explore modern draping techniques, color combinations, and jewelry pairing secrets to stand out at every festive celebration.</p>',
        'image': 'https://images.unsplash.com/photo-1610030469983-98e550d6193c?auto=format&fit=crop&w=1200&h=650&q=85',
        'views': 120
    },
    {
        'title': 'Bridal Lehenga Trends 2026: Colors, Fabrics & Silhouette Secrets',
        'slug': 'bridal-lehenga-trends-2026-colors-fabrics-silhouettes',
        'meta_description': 'Explore top bridal lehenga trends for 2026: pastel hues, intricate embroideries, lightweight dupattas, and designer bridal shopping tips.',
        'description': '<p>The modern Indian bride seeks a harmonious balance of timeless royal heritage and contemporary ease. From blush pinks and royal ruby velvets to multi-layered cancan silhouettes, discover the most coveted bridal lehenga aesthetics crafted for your special day.</p>',
        'image': 'https://images.unsplash.com/photo-1617627143750-d86bc21e42bb?auto=format&fit=crop&w=1200&h=650&q=85',
        'views': 185
    },
    {
        'title': 'Modern Kurti Styling: From Daily Office Wear to Festive Glam',
        'slug': 'modern-kurti-styling-daily-office-to-festive-glam',
        'meta_description': 'How to style ethnic kurtis with palazzos, cigarette pants, and dupattas for a chic Indo-western look. Complete comfort fashion guide.',
        'description': '<p>Kurtis offer unparalleled versatility and comfort. Learn how to transform a casual cotton printed kurti into an evening showstopper with the right silver oxidized accessories, statement stoles, and contemporary footwear.</p>',
        'image': 'https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?auto=format&fit=crop&w=1200&h=650&q=85',
        'views': 95
    },
    {
        'title': "Men's Royal Ethnic Wardrobe: Kurtas, Nehru Jackets & Sherwanis",
        'slug': 'mens-royal-ethnic-wardrobe-kurtas-nehru-jackets-sherwanis',
        'meta_description': 'Upgrade your festive and wedding ethnic look with classic kurta pajamas, tailored bandhgala jackets, and royal sherwanis.',
        'description': '<p>Celebrate festivities in impeccable style. Discover how textured silk kurtas paired with structured Nehru jackets and handcrafted juttis create a sophisticated, masculine ethnic silhouette for sangeet and reception functions.</p>',
        'image': 'https://images.unsplash.com/photo-1605518216938-7c31b7b14ad0?auto=format&fit=crop&w=1200&h=650&q=85',
        'views': 140
    }
]

def run_sqlite_update():
    import sqlite3
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database file not found at {DB_PATH}")
        return

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    print("\n" + "="*60)
    print("  1. UPDATING HERO BANNERS (SLIDERS) IN SQLITE")
    print("="*60)
    cur.execute("DELETE FROM mainApp_slider")
    for b in BANNER_DATA:
        cur.execute("INSERT INTO mainApp_slider (image, link) VALUES (?, ?)", (b['image'], b['link']))
        print(f"[OK] Added Banner: {b['title']} -> {b['link']}")
    print(f"[SUCCESS] 5 HD Landscape Banners Populated!")

    print("\n" + "="*60)
    print("  2. POPULATING SEO-RICH FASHION BLOGS IN SQLITE")
    print("="*60)
    for blog in BLOG_DATA:
        cur.execute("SELECT id FROM mainApp_blog WHERE slug = ?", (blog['slug'],))
        row = cur.fetchone()
        if row:
            cur.execute("""
                UPDATE mainApp_blog 
                SET title = ?, meta_description = ?, description = ?, image = ?, views = ?
                WHERE id = ?
            """, (blog['title'], blog['meta_description'], blog['description'], blog['image'], blog['views'], row[0]))
            print(f"[OK] Updated Blog: '{blog['title']}' -> /blog-details/{blog['slug']}/")
        else:
            cur.execute("""
                INSERT INTO mainApp_blog (title, slug, description, meta_description, views, date, image)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (blog['title'], blog['slug'], blog['description'], blog['meta_description'], blog['views'], now_str, blog['image']))
            print(f"[OK] Created Blog: '{blog['title']}' -> /blog-details/{blog['slug']}/")

    con.commit()
    cur.execute("SELECT count(*) FROM mainApp_blog")
    total_blogs = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM mainApp_slider")
    total_sliders = cur.fetchone()[0]
    con.close()

    print("\n" + "="*60)
    print(f"  ALL DONE! Banners: {total_sliders} | Total Blogs: {total_blogs}")
    print("  PLEASE RESTART PYTHON APP IN CPANEL.")
    print("="*60 + "\n")

if __name__ == '__main__':
    run_sqlite_update()
