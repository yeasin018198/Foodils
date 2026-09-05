import os
import datetime
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = "akash_food_secret_key"

# --- MongoDB Connection ---
MONGO_URI = "mongodb+srv://akash:akash@cluster0.hjyqogc.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['food_business_db']

# Collections
settings_col = db['settings']
foods_col = db['foods']
cats_col = db['categories']
reviews_col = db['reviews']
views_col = db['views']

# --- Helper Functions ---
def get_site_settings():
    conf = settings_col.find_one({"id": "config"})
    if not conf:
        default = {
            "id": "config", "name": "Foodils", "logo": "https://i.imgur.com/86S7R6U.png",
            "fb": "#", "whatsapp": "8801700000000", "dmca": "DMCA Protected", 
            "pass": "admin123", "privacy": "Privacy Policy Content", "copyright": "© 2024 Foodils",
            "theme": "orange", "footer_text": "Best Food delivery in town", "header_text": "Welcome to our shop"
        }
        settings_col.insert_one(default)
        return default
    return conf

def track_view():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    now = datetime.datetime.now()
    six_hours_ago = now - datetime.timedelta(hours=6)
    existing = views_col.find_one({"ip": ip, "time": {"$gt": six_hours_ago}})
    if not existing:
        views_col.insert_one({"ip": ip, "time": now, "date": now.strftime("%Y-%m-%d")})

# --- TEMPLATES ---
HEAD = """
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<script src="https://cdn.tailwindcss.com"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css"/>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@300;500;700&display=swap');
    body { font-family: 'Hind Siliguri', sans-serif; background-color: #f3f4f6; color: #1f2937; }
    .no-scrollbar::-webkit-scrollbar { display: none; }
    .food-card img { height: 160px; object-fit: cover; width: 100%; border-radius: 12px; }
    @media (min-width: 768px) { .food-card img { height: 220px; } }
    .category-icon { min-width: 80px; transition: transform 0.2s; }
    .category-icon:hover { transform: scale(1.1); }
    .premium-shadow { box-shadow: 0 4px 20px -5px rgba(0,0,0,0.1); }
</style>
"""

# --- USER ROUTES ---

@app.route('/')
def home():
    track_view()
    settings = get_site_settings()
    categories = list(cats_col.find())
    
    # Slider logic: 3 items from each category (Original Logic preserved)
    slider_items = []
    for c in categories:
        items = list(foods_col.find({"category": c['name']}).limit(3))
        slider_items.extend(items)
    
    all_foods = list(foods_col.find())
    
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="bn">
    <head>"""+HEAD+"""<title>{{ settings.name }} - Home</title></head>
    <body class="max-w-screen-2xl mx-auto">
        <!-- Header -->
        <nav class="bg-white/80 backdrop-blur-md sticky top-0 z-50 px-4 py-3 flex justify-between items-center border-b">
            <div class="flex items-center gap-3">
                <img src="{{ settings.logo }}" class="w-10 h-10 md:w-12 md:h-12 rounded-full ring-2 ring-{{ settings.theme }}-500">
                <h1 class="text-xl md:text-2xl font-bold text-{{ settings.theme }}-600">{{ settings.name }}</h1>
            </div>
            <!-- Admin access is hidden as per request -->
        </nav>

        <!-- Category Horizontal Slider -->
        <div class="bg-white py-4 px-2 flex gap-4 overflow-x-auto no-scrollbar border-b">
            {% for cat in categories %}
            <a href="/category/{{ cat.name }}" class="category-icon flex flex-col items-center">
                <div class="w-14 h-14 md:w-16 md:h-16 rounded-full border-2 border-{{ settings.theme }}-500 p-0.5 overflow-hidden">
                    <img src="{{ cat.logo }}" class="w-full h-full rounded-full object-cover">
                </div>
                <span class="text-[10px] md:text-xs mt-2 font-bold text-gray-700">{{ cat.name }}</span>
            </a>
            {% endfor %}
        </div>

        <!-- Main Banner -->
        <div class="p-4">
            <div class="bg-{{ settings.theme }}-600 rounded-2xl p-6 text-white shadow-lg relative overflow-hidden">
                <h2 class="text-xl md:text-3xl font-bold relative z-10">{{ settings.header_text }}</h2>
                <p class="mt-1 opacity-90 text-sm md:text-base">Order your favorite food now!</p>
                <i class="fas fa-hamburger absolute -right-4 -bottom-4 text-7xl opacity-20 rotate-12"></i>
            </div>
        </div>

        <!-- Featured Slider (Original 3 items per category logic) -->
        <div class="p-4">
            <h2 class="text-lg md:text-xl font-bold mb-4 flex items-center gap-2">
                <span class="w-1.5 h-6 bg-{{ settings.theme }}-600 rounded-full"></span> Featured Foods
            </h2>
            <div class="flex gap-4 overflow-x-auto no-scrollbar pb-2">
                {% for item in slider_items %}
                <a href="/food/{{ item._id }}" class="min-w-[260px] md:min-w-[320px] bg-white rounded-2xl shadow-sm border overflow-hidden">
                    <img src="{{ item.image }}" class="w-full h-40 md:h-48 object-cover">
                    <div class="p-4">
                        <h3 class="font-bold text-gray-800">{{ item.name }}</h3>
                        <div class="flex justify-between items-center mt-2">
                            <span class="text-{{ settings.theme }}-600 font-bold">৳{{ item.price }}</span>
                            <span class="text-[10px] bg-{{ settings.theme }}-50 text-{{ settings.theme }}-600 px-2 py-1 rounded-md">{{ item.category }}</span>
                        </div>
                    </div>
                </a>
                {% endfor %}
            </div>
        </div>

        <!-- All Food Grid (Fully Responsive) -->
        <div class="p-4">
            <h2 class="text-lg md:text-xl font-bold mb-4 flex items-center gap-2">
                <span class="w-1.5 h-6 bg-gray-800 rounded-full"></span> Regular Menu
            </h2>
            <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 md:gap-6">
                {% for food in all_foods %}
                <a href="/food/{{ food._id }}" class="food-card bg-white rounded-2xl p-2 md:p-3 shadow-sm hover:shadow-md transition-all border animate__animated animate__fadeIn">
                    <img src="{{ food.image }}" alt="{{ food.name }}">
                    <h4 class="text-sm md:text-base font-bold mt-3 text-gray-800 truncate px-1">{{ food.name }}</h4>
                    <div class="flex justify-between items-center mt-2 px-1 pb-1">
                        <span class="text-{{ settings.theme }}-600 font-bold text-sm md:text-base">৳{{ food.price }}</span>
                        <div class="bg-gray-100 p-1.5 rounded-lg text-gray-400 text-xs md:text-sm">
                            <i class="fas fa-cart-plus"></i>
                        </div>
                    </div>
                </a>
                {% endfor %}
            </div>
        </div>

        <!-- Footer -->
        <footer class="bg-white border-t mt-12 p-8 md:p-12 text-center">
            <div class="flex justify-center items-center gap-2 mb-4">
                <img src="{{ settings.logo }}" class="w-8 h-8 rounded-full">
                <span class="font-bold text-xl">{{ settings.name }}</span>
            </div>
            <p class="text-gray-500 max-w-md mx-auto text-sm">{{ settings.footer_text }}</p>
            <div class="flex justify-center gap-8 my-6 text-2xl">
                <a href="{{ settings.fb }}" class="text-blue-600 hover:scale-110 transition-transform"><i class="fab fa-facebook"></i></a>
                <a href="https://wa.me/{{ settings.whatsapp }}" class="text-green-500 hover:scale-110 transition-transform"><i class="fab fa-whatsapp"></i></a>
            </div>
            <div class="text-[10px] md:text-xs text-gray-400 border-t pt-6 space-y-1">
                <p>{{ settings.dmca }}</p>
                <p>{{ settings.copyright }}</p>
            </div>
        </footer>
    </body>
    </html>
    """, settings=settings, categories=categories, slider_items=slider_items, all_foods=all_foods)

@app.route('/food/<id>')
def food_details(id):
    settings = get_site_settings()
    food = foods_col.find_one({"_id": ObjectId(id)})
    reviews = list(reviews_col.find({"food_id": id}).sort("_id", -1))
    
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>"""+HEAD+"""<title>{{ food.name }} - Details</title></head>
    <body class="bg-gray-50">
        <div class="max-w-4xl mx-auto bg-white min-h-screen shadow-sm">
            <!-- Hero Image Section -->
            <div class="relative h-[300px] md:h-[450px]">
                <img src="{{ food.image }}" class="w-full h-full object-cover">
                <a href="/" class="absolute top-4 left-4 bg-white/70 backdrop-blur-md w-10 h-10 rounded-full flex items-center justify-center text-gray-800 shadow-lg">
                    <i class="fas fa-arrow-left"></i>
                </a>
            </div>
            
            <div class="p-6 md:p-10 -mt-8 bg-white rounded-t-[32px] relative z-10">
                <div class="flex justify-between items-start mb-6">
                    <div>
                        <span class="bg-{{ settings.theme }}-100 text-{{ settings.theme }}-600 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider">{{ food.category }}</span>
                        <h1 class="text-2xl md:text-4xl font-bold mt-2 text-gray-900">{{ food.name }}</h1>
                    </div>
                    <div class="text-right">
                        <p class="text-2xl md:text-3xl font-bold text-{{ settings.theme }}-600">৳{{ food.price }}</p>
                        <p class="text-xs text-gray-400 font-medium">Per Plate/Unit</p>
                    </div>
                </div>

                <!-- Gallery Grid -->
                <div class="grid grid-cols-4 md:grid-cols-6 gap-3 mb-8">
                    {% for ss in food.screenshots %}
                    <img src="{{ ss }}" class="w-full aspect-square rounded-xl object-cover border-2 border-gray-100">
                    {% endfor %}
                </div>

                <!-- Info Box -->
                <div class="bg-gray-50 rounded-2xl p-5 border border-gray-100">
                    <h4 class="font-bold text-gray-800 border-b pb-3 mb-3 flex items-center gap-2">
                        <i class="fas fa-list-ul text-{{ settings.theme }}-500"></i> Description & Details
                    </h4>
                    <p class="text-gray-600 leading-relaxed whitespace-pre-line text-sm md:text-base">{{ food.details }}</p>
                </div>

                <!-- Order Button (Original WhatsApp Link Logic) -->
                <a href="https://wa.me/{{ settings.whatsapp }}?text=New Order Request!%0A---%0AItem: {{ food.name }}%0APrice: {{ food.price }}%0ACategory: {{ food.category }}%0AImage: {{ food.image }}" 
                   class="flex items-center justify-center gap-3 mt-10 bg-green-500 text-white py-4 rounded-2xl font-bold text-lg shadow-xl shadow-green-100 hover:bg-green-600 transition-all active:scale-95">
                   <i class="fab fa-whatsapp text-2xl"></i> Order Now via WhatsApp
                </a>

                <!-- Reviews Section -->
                <div class="mt-12 border-t pt-10">
                    <h3 class="text-xl font-bold text-gray-900 mb-6">Customer Reviews ({{ reviews|length }})</h3>
                    
                    <form action="/review/{{ food._id }}" method="POST" class="bg-gray-50 p-6 rounded-2xl space-y-4 mb-8">
                        <select name="stars" class="w-full bg-white border p-3 rounded-xl outline-none focus:ring-2 focus:ring-{{ settings.theme }}-500">
                            <option value="5">⭐⭐⭐⭐⭐ Excellent</option>
                            <option value="4">⭐⭐⭐⭐ Good</option>
                            <option value="3">⭐⭐⭐ Average</option>
                            <option value="2">⭐⭐ Poor</option>
                            <option value="1">⭐ Very Bad</option>
                        </select>
                        <textarea name="comment" placeholder="Tell others about the taste..." class="w-full bg-white border p-4 rounded-xl h-24 outline-none focus:ring-2 focus:ring-{{ settings.theme }}-500" required></textarea>
                        <button class="w-full bg-{{ settings.theme }}-600 text-white py-3 rounded-xl font-bold">Post Review</button>
                    </form>

                    <div class="space-y-4">
                        {% for r in reviews %}
                        <div class="p-5 bg-white border rounded-2xl shadow-sm">
                            <div class="text-yellow-400 text-xs mb-2">
                                {% for i in range(r.stars) %}⭐{% endfor %}
                            </div>
                            <p class="text-gray-700 text-sm italic">"{{ r.comment }}"</p>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """, food=food, settings=settings, reviews=reviews)

@app.route('/review/<id>', methods=['POST'])
def post_review(id):
    reviews_col.insert_one({
        "food_id": id,
        "stars": int(request.form.get('stars')),
        "comment": request.form.get('comment'),
        "created_at": datetime.datetime.now()
    })
    return redirect(f'/food/{id}')

# --- ADMIN ROUTES ---

@app.route('/admin/dash')
def admin_dash():
    if not session.get('admin_logged'): return render_template_string("""
        <head>"""+HEAD+"""</head>
        <div class="max-w-md mx-auto mt-20 p-8 bg-white shadow-2xl rounded-3xl border text-center">
            <div class="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl text-gray-500">
                <i class="fas fa-user-lock"></i>
            </div>
            <h2 class="text-2xl font-bold mb-6">Admin Login</h2>
            <form action="/admin/login" method="POST" class="space-y-4">
                <input type="password" name="pass" placeholder="Enter Password" class="w-full border p-4 rounded-2xl text-center outline-none focus:ring-2 focus:ring-black">
                <button class="w-full bg-gray-900 text-white py-4 rounded-2xl font-bold hover:bg-black transition-all">Login to Panel</button>
            </form>
        </div>
    """)
    
    settings = get_site_settings()
    total_foods = foods_col.count_documents({})
    total_cats = cats_col.count_documents({})
    total_views = views_col.count_documents({})
    today_views = views_col.count_documents({"date": datetime.datetime.now().strftime("%Y-%m-%d")})
    
    latest_comments = list(reviews_col.find().sort("_id", -1).limit(10))
    
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>"""+HEAD+"""<title>Admin Dashboard</title></head>
    <body class="flex flex-col lg:flex-row min-h-screen bg-gray-50">
        <!-- Sidebar -->
        <div class="w-full lg:w-72 bg-gray-900 text-white p-8">
            <div class="flex items-center gap-3 mb-10">
                <img src="{{ settings.logo }}" class="w-10 h-10 rounded-lg">
                <h2 class="text-xl font-bold">{{ settings.name }} Control</h2>
            </div>
            <nav class="space-y-4 font-medium">
                <a href="/admin/dash" class="flex items-center gap-3 p-4 bg-{{ settings.theme }}-600 rounded-xl"><i class="fas fa-th-large w-5"></i> Dashboard</a>
                <a href="/admin/add-food" class="flex items-center gap-3 p-4 hover:bg-gray-800 rounded-xl"><i class="fas fa-plus-circle w-5"></i> Add New Food</a>
                <a href="/admin/add-cat" class="flex items-center gap-3 p-4 hover:bg-gray-800 rounded-xl"><i class="fas fa-tags w-5"></i> Categories</a>
                <a href="/admin/settings" class="flex items-center gap-3 p-4 hover:bg-gray-800 rounded-xl"><i class="fas fa-cogs w-5"></i> Settings</a>
                <div class="pt-10 space-y-4">
                    <a href="/" class="flex items-center gap-3 p-4 text-blue-400 border border-blue-400/20 rounded-xl"><i class="fas fa-eye w-5"></i> Live Site</a>
                    <a href="/admin/logout" class="flex items-center gap-3 p-4 text-red-400"><i class="fas fa-sign-out-alt w-5"></i> Logout</a>
                </div>
            </nav>
        </div>

        <!-- Main Content -->
        <div class="flex-1 p-6 md:p-12 overflow-y-auto">
            <h1 class="text-3xl font-bold mb-10 text-gray-800">Overview</h1>
            
            <div class="grid grid-cols-2 lg:grid-cols-4 gap-6">
                <div class="bg-white p-6 rounded-3xl shadow-sm border-t-4 border-blue-500">
                    <p class="text-gray-400 text-xs font-bold uppercase tracking-widest">Total Views</p>
                    <h3 class="text-3xl font-black mt-1">{{ total_views }}</h3>
                </div>
                <div class="bg-white p-6 rounded-3xl shadow-sm border-t-4 border-green-500">
                    <p class="text-gray-400 text-xs font-bold uppercase tracking-widest">Today Views</p>
                    <h3 class="text-3xl font-black mt-1 text-green-600">{{ today_views }}</h3>
                </div>
                <div class="bg-white p-6 rounded-3xl shadow-sm border-t-4 border-orange-500">
                    <p class="text-gray-400 text-xs font-bold uppercase tracking-widest">Total Items</p>
                    <h3 class="text-3xl font-black mt-1 text-orange-500">{{ total_foods }}</h3>
                </div>
                <div class="bg-white p-6 rounded-3xl shadow-sm border-t-4 border-purple-500">
                    <p class="text-gray-400 text-xs font-bold uppercase tracking-widest">Categories</p>
                    <h3 class="text-3xl font-black mt-1 text-purple-600">{{ total_cats }}</h3>
                </div>
            </div>

            <div class="mt-12 bg-white p-8 rounded-3xl shadow-sm border">
                <h3 class="text-xl font-bold mb-6 flex items-center gap-2"><i class="fas fa-comments text-{{ settings.theme }}-500"></i> Recent Customer Feedback</h3>
                <div class="space-y-4">
                    {% for c in comments %}
                    <div class="flex justify-between items-center p-4 bg-gray-50 rounded-2xl border border-gray-100">
                        <p class="text-gray-600 text-sm italic">"{{ c.comment }}"</p>
                        <span class="text-[10px] font-bold bg-yellow-100 text-yellow-600 px-3 py-1 rounded-full">{{ c.stars }} ⭐</span>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </body>
    </html>
    """, total_foods=total_foods, total_cats=total_cats, total_views=total_views, today_views=today_views, comments=latest_comments, settings=settings)

@app.route('/admin/login', methods=['POST'])
def admin_login_post():
    settings = get_site_settings()
    if request.form.get('pass') == settings['pass']:
        session['admin_logged'] = True
    return redirect('/admin/dash')

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect('/')

@app.route('/admin/add-food', methods=['GET', 'POST'])
def admin_add_food():
    if not session.get('admin_logged'): return redirect('/admin/dash')
    settings = get_site_settings()
    if request.method == 'POST':
        ss_list = [x.strip() for x in request.form.get('screenshots').split(',') if x.strip()]
        foods_col.insert_one({
            "name": request.form.get('name'),
            "image": request.form.get('image'),
            "price": request.form.get('price'),
            "category": request.form.get('category'),
            "screenshots": ss_list,
            "details": request.form.get('details')
        })
        return redirect('/admin/dash')
    
    categories = list(cats_col.find())
    return render_template_string("""
    <head>"""+HEAD+"""</head>
    <body class="p-6 bg-gray-50">
        <div class="max-w-3xl mx-auto">
            <h2 class="text-3xl font-bold mb-8 flex items-center gap-3"><i class="fas fa-plus text-orange-600"></i> Add New Food</h2>
            <form method="POST" class="bg-white p-8 rounded-3xl shadow-sm border space-y-5">
                <div class="grid md:grid-cols-2 gap-5">
                    <input name="name" placeholder="Food Name" class="w-full border p-4 rounded-2xl outline-none focus:ring-2 focus:ring-orange-500" required>
                    <input name="price" placeholder="Price (৳)" class="w-full border p-4 rounded-2xl outline-none focus:ring-2 focus:ring-orange-500" required>
                </div>
                <input name="image" placeholder="Main Image URL" class="w-full border p-4 rounded-2xl outline-none focus:ring-2 focus:ring-orange-500" required>
                <select name="category" class="w-full border p-4 rounded-2xl outline-none focus:ring-2 focus:ring-orange-500">
                    {% for cat in categories %} <option value="{{ cat.name }}">{{ cat.name }}</option> {% endfor %}
                </select>
                <textarea name="screenshots" placeholder="Other Screenshot URLs (separated by comma)" class="w-full border p-4 rounded-2xl h-24 outline-none focus:ring-2 focus:ring-orange-500"></textarea>
                <textarea name="details" placeholder="Write full food details..." class="w-full border p-4 rounded-2xl h-40 outline-none focus:ring-2 focus:ring-orange-500" required></textarea>
                <button class="w-full bg-orange-600 text-white py-5 rounded-2xl font-bold text-lg shadow-lg hover:bg-orange-700 transition-all">Save & Publish</button>
            </form>
        </div>
    </body>
    """, categories=categories)

@app.route('/admin/add-cat', methods=['GET', 'POST'])
def admin_add_cat():
    if not session.get('admin_logged'): return redirect('/admin/dash')
    if request.method == 'POST':
        cats_col.insert_one({"name": request.form.get('name'), "logo": request.form.get('logo')})
    
    categories = list(cats_col.find())
    return render_template_string("""
    <head>"""+HEAD+"""</head>
    <body class="p-6 bg-gray-100 min-h-screen">
        <div class="max-w-6xl mx-auto grid md:grid-cols-2 gap-10 mt-10">
            <form method="POST" class="bg-white p-8 rounded-[32px] shadow-sm h-fit">
                <h3 class="text-2xl font-bold mb-8">Create Category</h3>
                <input name="name" placeholder="Category Name" class="w-full border p-4 rounded-2xl mb-4 outline-none focus:ring-2 focus:ring-gray-900" required>
                <input name="logo" placeholder="Logo URL" class="w-full border p-4 rounded-2xl mb-6 outline-none focus:ring-2 focus:ring-gray-900" required>
                <button class="w-full bg-gray-900 text-white py-4 rounded-2xl font-bold">Add Now</button>
            </form>
            <div class="bg-white p-8 rounded-[32px] shadow-sm">
                <h3 class="text-2xl font-bold mb-8">All Categories</h3>
                <div class="space-y-4">
                    {% for cat in categories %}
                    <div class="flex justify-between items-center p-4 bg-gray-50 rounded-2xl border">
                        <div class="flex items-center gap-4">
                            <img src="{{ cat.logo }}" class="w-12 h-12 rounded-full object-cover border">
                            <span class="font-bold text-gray-700">{{ cat.name }}</span>
                        </div>
                        <a href="/admin/del-cat/{{ cat._id }}" class="text-red-500 bg-red-50 w-10 h-10 flex items-center justify-center rounded-full hover:bg-red-500 hover:text-white transition-all"><i class="fas fa-trash-alt"></i></a>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </body>
    """, categories=categories)

@app.route('/admin/del-cat/<id>')
def del_cat(id):
    if not session.get('admin_logged'): return redirect('/admin/dash')
    cats_col.delete_one({"_id": ObjectId(id)})
    return redirect('/admin/add-cat')

@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    if not session.get('admin_logged'): return redirect('/admin/dash')
    settings = get_site_settings()
    if request.method == 'POST':
        updated = {
            "name": request.form.get('name'),
            "logo": request.form.get('logo'),
            "whatsapp": request.form.get('whatsapp'),
            "fb": request.form.get('fb'),
            "pass": request.form.get('pass'),
            "dmca": request.form.get('dmca'),
            "copyright": request.form.get('copyright'),
            "footer_text": request.form.get('footer_text'),
            "theme": request.form.get('theme'),
            "privacy": request.form.get('privacy')
        }
        settings_col.update_one({"id": "config"}, {"$set": updated})
        return redirect('/admin/dash')

    return render_template_string("""
    <head>"""+HEAD+"""</head>
    <body class="p-6 bg-gray-50">
        <form method="POST" class="max-w-4xl mx-auto bg-white p-10 rounded-[40px] shadow-sm grid grid-cols-1 md:grid-cols-2 gap-8 border">
            <h2 class="col-span-1 md:col-span-2 text-3xl font-bold mb-4 flex items-center gap-3"><i class="fas fa-palette text-blue-600"></i> Settings & Customization</h2>
            
            <div class="space-y-2"><label class="font-bold text-gray-500 text-sm uppercase px-1">Site Name</label><input name="name" value="{{ s.name }}" class="w-full border p-4 rounded-2xl outline-none focus:ring-2 focus:ring-black"></div>
            <div class="space-y-2"><label class="font-bold text-gray-500 text-sm uppercase px-1">Logo URL</label><input name="logo" value="{{ s.logo }}" class="w-full border p-4 rounded-2xl outline-none focus:ring-2 focus:ring-black"></div>
            <div class="space-y-2"><label class="font-bold text-gray-500 text-sm uppercase px-1">WhatsApp</label><input name="whatsapp" value="{{ s.whatsapp }}" class="w-full border p-4 rounded-2xl outline-none focus:ring-2 focus:ring-black"></div>
            <div class="space-y-2"><label class="font-bold text-gray-500 text-sm uppercase px-1">Facebook Profile</label><input name="fb" value="{{ s.fb }}" class="w-full border p-4 rounded-2xl outline-none focus:ring-2 focus:ring-black"></div>
            <div class="space-y-2"><label class="font-bold text-gray-500 text-sm uppercase px-1">Admin Pass</label><input name="pass" value="{{ s.pass }}" class="w-full border p-4 rounded-2xl outline-none focus:ring-2 focus:ring-black"></div>
            
            <div class="space-y-2"><label class="font-bold text-gray-500 text-sm uppercase px-1">Main Theme Color</label>
                <select name="theme" class="w-full border p-4 rounded-2xl outline-none focus:ring-2 focus:ring-black">
                    <option value="orange" {% if s.theme=='orange' %}selected{% endif %}>Orange</option>
                    <option value="blue" {% if s.theme=='blue' %}selected{% endif %}>Blue</option>
                    <option value="red" {% if s.theme=='red' %}selected{% endif %}>Red</option>
                    <option value="green" {% if s.theme=='green' %}selected{% endif %}>Green</option>
                    <option value="pink" {% if s.theme=='pink' %}selected{% endif %}>Pink</option>
                    <option value="purple" {% if s.theme=='purple' %}selected{% endif %}>Purple</option>
                    <option value="indigo" {% if s.theme=='indigo' %}selected{% endif %}>Indigo</option>
                </select>
            </div>

            <div class="col-span-1 md:col-span-2 space-y-2"><label class="font-bold text-gray-500 text-sm uppercase px-1">Footer Tagline</label><input name="footer_text" value="{{ s.footer_text }}" class="w-full border p-4 rounded-2xl outline-none focus:ring-2 focus:ring-black"></div>
            <div class="col-span-1 md:col-span-2 space-y-2"><label class="font-bold text-gray-500 text-sm uppercase px-1">Privacy Policy Box</label><textarea name="privacy" class="w-full border p-4 rounded-2xl h-32 outline-none focus:ring-2 focus:ring-black">{{ s.privacy }}</textarea></div>
            
            <div class="space-y-2"><label class="font-bold text-gray-500 text-sm uppercase px-1">DMCA Protection</label><input name="dmca" value="{{ s.dmca }}" class="w-full border p-4 rounded-2xl outline-none focus:ring-2 focus:ring-black"></div>
            <div class="space-y-2"><label class="font-bold text-gray-500 text-sm uppercase px-1">Copyright Text</label><input name="copyright" value="{{ s.copyright }}" class="w-full border p-4 rounded-2xl outline-none focus:ring-2 focus:ring-black"></div>
            
            <button class="col-span-1 md:col-span-2 bg-gray-900 text-white py-5 rounded-2xl font-bold text-xl mt-6 hover:bg-black shadow-xl">Apply Changes</button>
        </form>
    </body>
    """, s=settings)

if __name__ == '__main__':
    app.run(debug=True)
