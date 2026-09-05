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
    .category-icon { min-width: 70px; transition: transform 0.2s; }
    @media (min-width: 768px) { .category-icon { min-width: 90px; } }
    .category-icon:hover { transform: scale(1.1); }
</style>
"""

# --- USER ROUTES ---

@app.route('/')
def home():
    track_view()
    settings = get_site_settings()
    categories = list(cats_col.find())
    
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
        <nav class="bg-white/90 backdrop-blur-md sticky top-0 z-50 px-4 py-3 flex justify-between items-center border-b">
            <div class="flex items-center gap-2 md:gap-4">
                <img src="{{ settings.logo }}" class="w-10 h-10 md:w-14 md:h-14 rounded-full ring-2 ring-{{ settings.theme }}-500">
                <h1 class="text-lg md:text-2xl font-bold text-{{ settings.theme }}-600">{{ settings.name }}</h1>
            </div>
            <div class="flex gap-4">
                <a href="https://wa.me/{{ settings.whatsapp|replace('+', '')|replace(' ', '') }}" class="text-green-500 text-xl md:text-2xl"><i class="fab fa-whatsapp"></i></a>
            </div>
        </nav>

        <!-- Category Horizontal Slider -->
        <div class="bg-white py-4 px-2 flex gap-3 md:gap-6 overflow-x-auto no-scrollbar border-b">
            {% for cat in categories %}
            <a href="/category/{{ cat.name }}" class="category-icon flex flex-col items-center text-center">
                <div class="w-12 h-12 md:w-20 md:h-20 rounded-full border-2 border-{{ settings.theme }}-500 p-0.5 overflow-hidden">
                    <img src="{{ cat.logo }}" class="w-full h-full rounded-full object-cover">
                </div>
                <span class="text-[10px] md:text-sm mt-2 font-bold text-gray-700 truncate w-full px-1">{{ cat.name }}</span>
            </a>
            {% endfor %}
        </div>

        <!-- Main Banner -->
        <div class="p-3 md:p-6">
            <div class="bg-{{ settings.theme }}-600 rounded-2xl md:rounded-[30px] p-6 md:p-12 text-white shadow-lg relative overflow-hidden">
                <h2 class="text-xl md:text-5xl font-bold relative z-10 leading-tight">{{ settings.header_text }}</h2>
                <p class="mt-2 md:mt-4 opacity-90 text-sm md:text-xl">আপনার পছন্দের খাবার এখন হাতের নাগালে!</p>
                <i class="fas fa-hamburger absolute -right-4 -bottom-4 text-7xl md:text-9xl opacity-20 rotate-12"></i>
            </div>
        </div>

        <!-- Featured Slider -->
        <div class="p-3 md:p-6">
            <h2 class="text-lg md:text-2xl font-bold mb-4 flex items-center gap-2">
                <span class="w-1.5 h-6 bg-{{ settings.theme }}-600 rounded-full"></span> Featured Foods
            </h2>
            <div class="flex gap-4 overflow-x-auto no-scrollbar pb-2">
                {% for item in slider_items %}
                <a href="/food/{{ item._id }}" class="min-w-[240px] md:min-w-[350px] bg-white rounded-2xl shadow-sm border overflow-hidden">
                    <img src="{{ item.image }}" class="w-full h-40 md:h-56 object-cover">
                    <div class="p-4">
                        <h3 class="font-bold text-gray-800 text-sm md:text-lg">{{ item.name }}</h3>
                        <div class="flex justify-between items-center mt-2">
                            <span class="text-{{ settings.theme }}-600 font-bold md:text-xl">৳{{ item.price }}</span>
                            <span class="text-[10px] md:text-xs bg-{{ settings.theme }}-50 text-{{ settings.theme }}-600 px-2 py-1 rounded-md">{{ item.category }}</span>
                        </div>
                    </div>
                </a>
                {% endfor %}
            </div>
        </div>

        <!-- All Food Grid -->
        <div class="p-3 md:p-6">
            <h2 class="text-lg md:text-2xl font-bold mb-4 flex items-center gap-2">
                <span class="w-1.5 h-6 bg-gray-800 rounded-full"></span> Regular Menu
            </h2>
            <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3 md:gap-6">
                {% for food in all_foods %}
                <a href="/food/{{ food._id }}" class="food-card bg-white rounded-xl md:rounded-2xl p-2 md:p-4 shadow-sm hover:shadow-md transition-all border animate__animated animate__fadeIn">
                    <img src="{{ food.image }}" alt="{{ food.name }}">
                    <h4 class="text-sm md:text-lg font-bold mt-3 text-gray-800 truncate px-1">{{ food.name }}</h4>
                    <div class="flex justify-between items-center mt-2 px-1">
                        <span class="text-{{ settings.theme }}-600 font-bold text-sm md:text-lg">৳{{ food.price }}</span>
                        <div class="bg-gray-100 p-1.5 md:p-2 rounded-lg text-gray-400 text-xs md:text-sm">
                            <i class="fas fa-cart-plus"></i>
                        </div>
                    </div>
                </a>
                {% endfor %}
            </div>
        </div>

        <!-- Footer -->
        <footer class="bg-white border-t mt-12 p-8 md:p-16 text-center">
            <div class="flex flex-col items-center gap-4 mb-6">
                <img src="{{ settings.logo }}" class="w-12 h-12 md:w-20 md:h-20 rounded-full shadow-md">
                <span class="font-bold text-xl md:text-3xl">{{ settings.name }}</span>
            </div>
            <p class="text-gray-500 max-w-xl mx-auto text-sm md:text-lg mb-8">{{ settings.footer_text }}</p>
            <div class="flex justify-center gap-8 mb-10 text-3xl md:text-4xl">
                <a href="{{ settings.fb }}" class="text-blue-600 hover:scale-110 transition-transform"><i class="fab fa-facebook"></i></a>
                <a href="https://wa.me/{{ settings.whatsapp|replace('+', '')|replace(' ', '') }}" class="text-green-500 hover:scale-110 transition-transform"><i class="fab fa-whatsapp"></i></a>
            </div>
            <div class="text-[10px] md:text-sm text-gray-400 border-t pt-8 space-y-2">
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
    
    # Clean WhatsApp number for link
    wa_num = settings['whatsapp'].replace('+', '').replace(' ', '')
    order_text = f"New Order Request!%0A---%0AItem: {food['name']}%0APrice: {food['price']}%0ACategory: {food['category']}%0AImage: {food['image']}"
    wa_link = f"https://wa.me/{wa_num}?text={order_text}"

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>"""+HEAD+"""<title>{{ food.name }} - Details</title></head>
    <body class="bg-gray-50">
        <div class="max-w-4xl mx-auto bg-white min-h-screen shadow-sm relative">
            <!-- Back Button -->
            <a href="/" class="fixed top-4 left-4 z-50 bg-white/80 backdrop-blur-md w-10 h-10 md:w-12 md:h-12 rounded-full flex items-center justify-center text-gray-800 shadow-xl border">
                <i class="fas fa-arrow-left"></i>
            </a>

            <div class="relative h-[250px] md:h-[500px]">
                <img src="{{ food.image }}" class="w-full h-full object-cover">
            </div>
            
            <div class="p-5 md:p-12 -mt-10 bg-white rounded-t-[30px] md:rounded-t-[50px] relative z-10 shadow-2xl">
                <div class="flex flex-col md:flex-row md:justify-between md:items-center gap-4 mb-8">
                    <div>
                        <span class="bg-{{ settings.theme }}-100 text-{{ settings.theme }}-600 px-4 py-1 rounded-full text-xs md:text-sm font-bold uppercase">{{ food.category }}</span>
                        <h1 class="text-2xl md:text-5xl font-extrabold mt-3 text-gray-900">{{ food.name }}</h1>
                    </div>
                    <div class="bg-{{ settings.theme }}-50 p-4 rounded-2xl border-l-4 border-{{ settings.theme }}-500">
                        <p class="text-2xl md:text-4xl font-black text-{{ settings.theme }}-600">৳{{ food.price }}</p>
                        <p class="text-[10px] md:text-xs text-gray-500 font-bold uppercase mt-1">Special Price</p>
                    </div>
                </div>

                <!-- Screenshots -->
                {% if food.screenshots %}
                <div class="grid grid-cols-4 gap-2 md:gap-4 mb-8">
                    {% for ss in food.screenshots %}
                    <img src="{{ ss }}" class="w-full aspect-square rounded-xl object-cover border-2 border-gray-100 hover:border-{{ settings.theme }}-400 transition-colors">
                    {% endfor %}
                </div>
                {% endif %}

                <!-- Description -->
                <div class="bg-gray-50 rounded-2xl md:rounded-3xl p-6 md:p-10 border border-gray-100 mb-10">
                    <h4 class="font-bold text-gray-800 border-b pb-4 mb-4 flex items-center gap-2 text-lg md:text-xl">
                        <i class="fas fa-utensils text-{{ settings.theme }}-500"></i> Food Description
                    </h4>
                    <p class="text-gray-600 leading-relaxed whitespace-pre-line text-sm md:text-lg">{{ food.details }}</p>
                </div>

                <!-- WhatsApp Order -->
                <a href="{{ wa_link }}" 
                   class="flex items-center justify-center gap-3 bg-green-500 text-white py-4 md:py-6 rounded-2xl md:rounded-[25px] font-bold text-lg md:text-2xl shadow-xl shadow-green-100 hover:bg-green-600 transition-all active:scale-95 mb-12">
                   <i class="fab fa-whatsapp text-2xl md:text-4xl"></i> Order Now on WhatsApp
                </a>

                <!-- Reviews -->
                <div class="border-t pt-10">
                    <h3 class="text-xl md:text-2xl font-bold text-gray-900 mb-8">Customer Feedback ({{ reviews|length }})</h3>
                    
                    <form action="/review/{{ food._id }}" method="POST" class="bg-gray-50 p-6 rounded-3xl space-y-4 mb-10 border">
                        <select name="stars" class="w-full bg-white border p-4 rounded-2xl outline-none focus:ring-2 focus:ring-{{ settings.theme }}-500">
                            <option value="5">⭐⭐⭐⭐⭐ Excellent</option>
                            <option value="4">⭐⭐⭐⭐ Good</option>
                            <option value="3">⭐⭐⭐ Average</option>
                            <option value="2">⭐⭐ Poor</option>
                            <option value="1">⭐ Very Bad</option>
                        </select>
                        <textarea name="comment" placeholder="আপনার মন্তব্য লিখুন..." class="w-full bg-white border p-4 rounded-2xl h-24 md:h-32 outline-none focus:ring-2 focus:ring-{{ settings.theme }}-500" required></textarea>
                        <button class="w-full bg-{{ settings.theme }}-600 text-white py-4 rounded-2xl font-bold text-lg">Post Review</button>
                    </form>

                    <div class="space-y-4">
                        {% for r in reviews %}
                        <div class="p-5 bg-white border rounded-2xl shadow-sm">
                            <div class="text-yellow-400 text-xs md:text-sm mb-2">
                                {% for i in range(r.stars) %}⭐{% endfor %}
                            </div>
                            <p class="text-gray-700 text-sm md:text-base italic">"{{ r.comment }}"</p>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """, food=food, settings=settings, reviews=reviews, wa_link=wa_link)

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
        <div class="max-w-md mx-auto mt-20 p-8 bg-white shadow-2xl rounded-[40px] border text-center">
            <div class="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6 text-3xl text-gray-600">
                <i class="fas fa-lock"></i>
            </div>
            <h2 class="text-2xl font-bold mb-6">Admin Panel</h2>
            <form action="/admin/login" method="POST" class="space-y-4">
                <input type="password" name="pass" placeholder="Password" class="w-full border p-4 rounded-2xl text-center text-lg outline-none focus:ring-2 focus:ring-black">
                <button class="w-full bg-gray-900 text-white py-4 rounded-2xl font-bold text-lg hover:bg-black transition-all">Login</button>
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
        <!-- Sidebar (Responsive) -->
        <div class="w-full lg:w-72 bg-gray-900 text-white p-6 lg:p-10">
            <div class="flex items-center gap-3 mb-10">
                <img src="{{ settings.logo }}" class="w-10 h-10 rounded-full border">
                <h2 class="text-xl font-bold">Admin Panel</h2>
            </div>
            <nav class="grid grid-cols-2 lg:grid-cols-1 gap-3 font-medium">
                <a href="/admin/dash" class="flex items-center gap-3 p-4 bg-{{ settings.theme }}-600 rounded-2xl"><i class="fas fa-chart-line"></i> Dash</a>
                <a href="/admin/add-food" class="flex items-center gap-3 p-4 hover:bg-gray-800 rounded-2xl"><i class="fas fa-plus"></i> Add Food</a>
                <a href="/admin/add-cat" class="flex items-center gap-3 p-4 hover:bg-gray-800 rounded-2xl"><i class="fas fa-list"></i> Categories</a>
                <a href="/admin/settings" class="flex items-center gap-3 p-4 hover:bg-gray-800 rounded-2xl"><i class="fas fa-cog"></i> Settings</a>
                <a href="/" class="flex items-center gap-3 p-4 text-blue-400"><i class="fas fa-globe"></i> Visit Site</a>
                <a href="/admin/logout" class="flex items-center gap-3 p-4 text-red-400"><i class="fas fa-sign-out-alt"></i> Logout</a>
            </nav>
        </div>

        <div class="flex-1 p-4 md:p-10">
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-8">
                <div class="bg-white p-6 rounded-3xl shadow-sm border-t-4 border-blue-500">
                    <p class="text-gray-400 text-xs font-bold uppercase">Total Views</p>
                    <h3 class="text-2xl md:text-4xl font-black mt-2">{{ total_views }}</h3>
                </div>
                <div class="bg-white p-6 rounded-3xl shadow-sm border-t-4 border-green-500">
                    <p class="text-gray-400 text-xs font-bold uppercase">Today</p>
                    <h3 class="text-2xl md:text-4xl font-black mt-2">{{ today_views }}</h3>
                </div>
                <div class="bg-white p-6 rounded-3xl shadow-sm border-t-4 border-orange-500">
                    <p class="text-gray-400 text-xs font-bold uppercase">Foods</p>
                    <h3 class="text-2xl md:text-4xl font-black mt-2">{{ total_foods }}</h3>
                </div>
                <div class="bg-white p-6 rounded-3xl shadow-sm border-t-4 border-purple-500">
                    <p class="text-gray-400 text-xs font-bold uppercase">Categories</p>
                    <h3 class="text-2xl md:text-4xl font-black mt-2">{{ total_cats }}</h3>
                </div>
            </div>

            <!-- Recent Reviews -->
            <div class="mt-10 bg-white p-6 md:p-10 rounded-3xl shadow-sm border">
                <h3 class="text-xl font-bold mb-6">Recent Feedback</h3>
                <div class="space-y-4">
                    {% for c in comments %}
                    <div class="flex justify-between items-center p-4 bg-gray-50 rounded-2xl border">
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
    <body class="p-4 md:p-10 bg-gray-50">
        <div class="max-w-3xl mx-auto">
            <h2 class="text-2xl md:text-3xl font-bold mb-8">Add New Food Item</h2>
            <form method="POST" class="bg-white p-6 md:p-10 rounded-[35px] shadow-sm border space-y-5">
                <div class="grid md:grid-cols-2 gap-5">
                    <input name="name" placeholder="Food Name" class="w-full border p-4 rounded-2xl outline-none focus:ring-2 focus:ring-orange-500" required>
                    <input name="price" placeholder="Price (৳)" class="w-full border p-4 rounded-2xl outline-none focus:ring-2 focus:ring-orange-500" required>
                </div>
                <input name="image" placeholder="Main Image URL" class="w-full border p-4 rounded-2xl outline-none focus:ring-2 focus:ring-orange-500" required>
                <select name="category" class="w-full border p-4 rounded-2xl outline-none focus:ring-2 focus:ring-orange-500">
                    {% for cat in categories %} <option value="{{ cat.name }}">{{ cat.name }}</option> {% endfor %}
                </select>
                <textarea name="screenshots" placeholder="Screenshots (URL separated by comma)" class="w-full border p-4 rounded-2xl h-24 outline-none focus:ring-2 focus:ring-orange-500"></textarea>
                <textarea name="details" placeholder="Full details..." class="w-full border p-4 rounded-2xl h-40 outline-none focus:ring-2 focus:ring-orange-500" required></textarea>
                <button class="w-full bg-orange-600 text-white py-5 rounded-2xl font-bold text-lg">Publish Item</button>
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
    <body class="p-4 md:p-10 bg-gray-100 min-h-screen">
        <div class="max-w-6xl mx-auto grid md:grid-cols-2 gap-6 mt-6">
            <form method="POST" class="bg-white p-6 md:p-10 rounded-[35px] shadow-sm h-fit">
                <h3 class="text-2xl font-bold mb-6">Create Category</h3>
                <input name="name" placeholder="Name" class="w-full border p-4 rounded-2xl mb-4 outline-none" required>
                <input name="logo" placeholder="Logo URL" class="w-full border p-4 rounded-2xl mb-6 outline-none" required>
                <button class="w-full bg-gray-900 text-white py-4 rounded-2xl font-bold">Add Category</button>
            </form>
            <div class="bg-white p-6 md:p-10 rounded-[35px] shadow-sm">
                <h3 class="text-2xl font-bold mb-6">Active Categories</h3>
                <div class="space-y-4">
                    {% for cat in categories %}
                    <div class="flex justify-between items-center p-4 bg-gray-50 rounded-2xl border">
                        <div class="flex items-center gap-4">
                            <img src="{{ cat.logo }}" class="w-12 h-12 rounded-full object-cover">
                            <span class="font-bold">{{ cat.name }}</span>
                        </div>
                        <a href="/admin/del-cat/{{ cat._id }}" class="text-red-500 p-2"><i class="fas fa-trash"></i></a>
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
    <body class="p-4 md:p-10 bg-gray-50">
        <form method="POST" class="max-w-4xl mx-auto bg-white p-6 md:p-12 rounded-[40px] shadow-sm grid grid-cols-1 md:grid-cols-2 gap-6 border">
            <h2 class="md:col-span-2 text-2xl md:text-3xl font-bold mb-4">Site Customization</h2>
            
            <div class="space-y-1"><label class="text-xs font-bold text-gray-400 px-2 uppercase">Site Name</label><input name="name" value="{{ s.name }}" class="w-full border p-4 rounded-2xl outline-none"></div>
            <div class="space-y-1"><label class="text-xs font-bold text-gray-400 px-2 uppercase">Logo URL</label><input name="logo" value="{{ s.logo }}" class="w-full border p-4 rounded-2xl outline-none"></div>
            <div class="space-y-1"><label class="text-xs font-bold text-gray-400 px-2 uppercase">WhatsApp Number</label><input name="whatsapp" value="{{ s.whatsapp }}" class="w-full border p-4 rounded-2xl outline-none"></div>
            <div class="space-y-1"><label class="text-xs font-bold text-gray-400 px-2 uppercase">Admin Password</label><input name="pass" value="{{ s.pass }}" class="w-full border p-4 rounded-2xl outline-none"></div>
            
            <div class="md:col-span-2 space-y-1"><label class="text-xs font-bold text-gray-400 px-2 uppercase">Main Theme</label>
                <select name="theme" class="w-full border p-4 rounded-2xl outline-none">
                    <option value="orange" {% if s.theme=='orange' %}selected{% endif %}>Orange</option>
                    <option value="blue" {% if s.theme=='blue' %}selected{% endif %}>Blue</option>
                    <option value="green" {% if s.theme=='green' %}selected{% endif %}>Green</option>
                    <option value="red" {% if s.theme=='red' %}selected{% endif %}>Red</option>
                    <option value="purple" {% if s.theme=='purple' %}selected{% endif %}>Purple</option>
                </select>
            </div>

            <div class="md:col-span-2 space-y-1"><label class="text-xs font-bold text-gray-400 px-2 uppercase">Footer Text</label><input name="footer_text" value="{{ s.footer_text }}" class="w-full border p-4 rounded-2xl outline-none"></div>
            
            <button class="md:col-span-2 bg-gray-900 text-white py-5 rounded-2xl font-bold text-xl mt-6">Save Settings</button>
        </form>
    </body>
    """, s=settings)

if __name__ == '__main__':
    app.run(debug=True)
