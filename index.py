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
    .food-card img { height: 160px; object-fit: cover; width: 100%; border-radius: 12px; transition: 0.3s; }
    .food-card:hover img { transform: scale(1.05); }
    @media (min-width: 768px) { .food-card img { height: 240px; } }
    .category-icon { min-width: 80px; transition: transform 0.2s; }
    .category-icon:hover { transform: scale(1.1); }
    .glass { background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(10px); }
    .theme-gradient { background: linear-gradient(135deg, var(--tw-gradient-from), var(--tw-gradient-to)); }
</style>
"""

# --- USER ROUTES ---

@app.route('/')
def home():
    track_view()
    settings = get_site_settings()
    categories = list(cats_col.find())
    
    # Original Slider logic: 3 items from each category
    slider_items = []
    for c in categories:
        items = list(foods_col.find({"category": c['name']}).limit(3))
        slider_items.extend(items)
    
    all_foods = list(foods_col.find())
    # Clean WhatsApp for global use
    wa_global = settings['whatsapp'].replace('+', '').replace(' ', '').replace('-', '')
    
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="bn">
    <head>"""+HEAD+"""<title>{{ settings.name }} - Home</title></head>
    <body class="max-w-screen-2xl mx-auto">
        <!-- Header -->
        <nav class="glass sticky top-0 z-50 px-4 py-3 flex justify-between items-center border-b">
            <div class="flex items-center gap-2 md:gap-4">
                <img src="{{ settings.logo }}" class="w-10 h-10 md:w-14 md:h-14 rounded-full ring-2 ring-{{ settings.theme }}-500">
                <h1 class="text-xl md:text-3xl font-extrabold text-{{ settings.theme }}-600 tracking-tight">{{ settings.name }}</h1>
            </div>
            <div class="flex items-center gap-4">
                <a href="https://wa.me/{{ wa_global }}" class="text-green-500 text-2xl md:text-3xl hover:scale-110 transition-transform"><i class="fab fa-whatsapp"></i></a>
            </div>
        </nav>

        <!-- Search Bar -->
        <div class="p-4 md:px-8 mt-4">
            <div class="relative max-w-2xl mx-auto">
                <input type="text" id="searchInput" onkeyup="searchFood()" placeholder="Search your favorite food..." class="w-full p-4 pl-12 rounded-2xl border-none shadow-md outline-none focus:ring-2 focus:ring-{{ settings.theme }}-500">
                <i class="fas fa-search absolute left-4 top-5 text-gray-400"></i>
            </div>
        </div>

        <!-- Category Slider -->
        <div class="py-4 px-2 flex gap-4 overflow-x-auto no-scrollbar">
            {% for cat in categories %}
            <a href="/category/{{ cat.name }}" class="category-icon flex flex-col items-center">
                <div class="w-16 h-16 md:w-24 md:h-24 rounded-full border-2 border-{{ settings.theme }}-500 p-1 bg-white shadow-sm overflow-hidden">
                    <img src="{{ cat.logo }}" class="w-full h-full rounded-full object-cover">
                </div>
                <span class="text-xs md:text-sm mt-2 font-bold text-gray-700">{{ cat.name }}</span>
            </a>
            {% endfor %}
        </div>

        <!-- Main Banner -->
        <div class="p-4 md:p-8">
            <div class="bg-{{ settings.theme }}-600 rounded-[30px] md:rounded-[50px] p-8 md:p-20 text-white shadow-2xl relative overflow-hidden">
                <div class="relative z-10">
                    <h2 class="text-2xl md:text-6xl font-black leading-tight mb-4">{{ settings.header_text }}</h2>
                    <p class="opacity-90 text-sm md:text-2xl">Freshness delivered to your doorstep.</p>
                </div>
                <i class="fas fa-pizza-slice absolute -right-10 -bottom-10 text-[150px] md:text-[300px] opacity-10 rotate-12"></i>
            </div>
        </div>

        <!-- Featured Slider -->
        <div class="p-4 md:p-8">
            <h2 class="text-xl md:text-3xl font-bold mb-6 flex items-center gap-3">
                <span class="w-2 h-8 bg-{{ settings.theme }}-600 rounded-full"></span> Featured Foods
            </h2>
            <div class="flex gap-6 overflow-x-auto no-scrollbar pb-4">
                {% for item in slider_items %}
                <a href="/food/{{ item._id }}" class="min-w-[280px] md:min-w-[420px] bg-white rounded-[32px] shadow-lg border overflow-hidden group">
                    <div class="overflow-hidden">
                        <img src="{{ item.image }}" class="w-full h-48 md:h-72 object-cover group-hover:scale-110 transition-transform duration-500">
                    </div>
                    <div class="p-6">
                        <h3 class="font-bold text-lg md:text-2xl text-gray-800">{{ item.name }}</h3>
                        <div class="flex justify-between items-center mt-4">
                            <span class="text-{{ settings.theme }}-600 font-black text-xl md:text-3xl">৳{{ item.price }}</span>
                            <span class="text-xs font-bold bg-{{ settings.theme }}-50 text-{{ settings.theme }}-600 px-4 py-2 rounded-full uppercase tracking-tighter">{{ item.category }}</span>
                        </div>
                    </div>
                </a>
                {% endfor %}
            </div>
        </div>

        <!-- All Food Grid -->
        <div class="p-4 md:p-8">
            <h2 class="text-xl md:text-3xl font-bold mb-6 flex items-center gap-3">
                <span class="w-2 h-8 bg-gray-800 rounded-full"></span> Regular Menu
            </h2>
            <div id="foodGrid" class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 md:gap-10">
                {% for food in all_foods %}
                <a href="/food/{{ food._id }}" class="food-item food-card bg-white rounded-[24px] md:rounded-[40px] p-3 md:p-6 shadow-sm hover:shadow-2xl transition-all border animate__animated animate__fadeIn">
                    <img src="{{ food.image }}" alt="{{ food.name }}" class="rounded-[20px] md:rounded-[30px]">
                    <h4 class="text-sm md:text-xl font-bold mt-4 text-gray-800 truncate px-1">{{ food.name }}</h4>
                    <div class="flex justify-between items-center mt-3 px-1">
                        <span class="text-{{ settings.theme }}-600 font-black text-base md:text-2xl">৳{{ food.price }}</span>
                        <div class="bg-{{ settings.theme }}-600 text-white w-8 h-8 md:w-12 md:h-12 flex items-center justify-center rounded-xl md:rounded-2xl shadow-lg">
                            <i class="fas fa-plus text-xs md:text-base"></i>
                        </div>
                    </div>
                </a>
                {% endfor %}
            </div>
        </div>

        <!-- Footer -->
        <footer class="bg-white border-t mt-20 p-10 md:p-24 text-center">
            <div class="flex flex-col items-center gap-4 mb-8">
                <img src="{{ settings.logo }}" class="w-16 h-16 md:w-24 md:h-24 rounded-full shadow-xl">
                <h2 class="font-black text-2xl md:text-5xl tracking-tighter">{{ settings.name }}</h2>
            </div>
            <p class="text-gray-400 max-w-2xl mx-auto text-sm md:text-xl leading-relaxed">{{ settings.footer_text }}</p>
            <div class="flex justify-center gap-10 my-12 text-4xl">
                <a href="{{ settings.fb }}" class="text-blue-600 hover:scale-125 transition-transform"><i class="fab fa-facebook"></i></a>
                <a href="https://wa.me/{{ wa_global }}" class="text-green-500 hover:scale-125 transition-transform"><i class="fab fa-whatsapp"></i></a>
            </div>
            <div class="text-[10px] md:text-sm text-gray-300 border-t pt-10 space-y-3">
                <p class="uppercase font-bold tracking-widest">{{ settings.dmca }}</p>
                <p>{{ settings.copyright }}</p>
            </div>
        </footer>

        <script>
            function searchFood() {
                let input = document.getElementById('searchInput').value.toLowerCase();
                let items = document.getElementsByClassName('food-item');
                for (let i = 0; i < items.length; i++) {
                    if (!items[i].innerText.toLowerCase().includes(input)) {
                        items[i].style.display = "none";
                    } else {
                        items[i].style.display = "block";
                    }
                }
            }
        </script>
    </body>
    </html>
    """, settings=settings, categories=categories, slider_items=slider_items, all_foods=all_foods, wa_global=wa_global)

@app.route('/food/<id>')
def food_details(id):
    settings = get_site_settings()
    food = foods_col.find_one({"_id": ObjectId(id)})
    reviews = list(reviews_col.find({"food_id": id}).sort("_id", -1))
    # WhatsApp Clean Logic
    wa_clean = settings['whatsapp'].replace('+', '').replace(' ', '').replace('-', '')
    
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>"""+HEAD+"""<title>{{ food.name }} - Details</title></head>
    <body class="bg-gray-50">
        <div class="max-w-6xl mx-auto bg-white min-h-screen shadow-2xl overflow-hidden">
            <div class="relative h-[350px] md:h-[600px]">
                <img src="{{ food.image }}" class="w-full h-full object-cover">
                <a href="/" class="absolute top-6 left-6 bg-white/90 backdrop-blur w-12 h-12 rounded-2xl flex items-center justify-center text-gray-800 shadow-xl">
                    <i class="fas fa-chevron-left"></i>
                </a>
            </div>
            
            <div class="p-6 md:p-16 -mt-16 bg-white rounded-t-[50px] md:rounded-t-[80px] relative z-10 shadow-inner">
                <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-12">
                    <div class="flex-1">
                        <span class="bg-{{ settings.theme }}-100 text-{{ settings.theme }}-600 px-5 py-2 rounded-full text-xs font-black uppercase tracking-widest">{{ food.category }}</span>
                        <h1 class="text-3xl md:text-6xl font-black mt-4 text-gray-900 tracking-tighter leading-none">{{ food.name }}</h1>
                    </div>
                    <div class="bg-gray-50 px-8 py-6 rounded-[30px] border-2 border-gray-100 text-center">
                        <p class="text-3xl md:text-5xl font-black text-{{ settings.theme }}-600">৳{{ food.price }}</p>
                        <p class="text-xs text-gray-400 font-bold uppercase mt-2">Special Price</p>
                    </div>
                </div>

                <!-- Gallery -->
                <div class="grid grid-cols-4 md:grid-cols-6 gap-4 mb-12">
                    {% for ss in food.screenshots %}
                    <img src="{{ ss }}" class="w-full aspect-square rounded-[20px] object-cover border-4 border-gray-50 hover:border-{{ settings.theme }}-400 transition-all shadow-sm">
                    {% endfor %}
                </div>

                <!-- Description -->
                <div class="bg-gray-50 rounded-[40px] p-8 md:p-12 border border-gray-100">
                    <h4 class="font-black text-gray-800 border-b pb-6 mb-6 flex items-center gap-3 text-xl md:text-3xl">
                        <i class="fas fa-file-alt text-{{ settings.theme }}-500"></i> Description
                    </h4>
                    <p class="text-gray-600 leading-relaxed whitespace-pre-line text-base md:text-2xl">{{ food.details }}</p>
                </div>

                <!-- WhatsApp Button -->
                <a href="https://wa.me/{{ wa_clean }}?text=Order: {{ food.name }} (৳{{ food.price }})" 
                   class="flex items-center justify-center gap-4 mt-12 bg-green-500 text-white py-5 md:py-8 rounded-[30px] font-black text-xl md:text-3xl shadow-2xl hover:bg-green-600 transition-all active:scale-95">
                   <i class="fab fa-whatsapp text-3xl md:text-5xl"></i> Order Now on WhatsApp
                </a>

                <!-- Reviews -->
                <div class="mt-20 border-t pt-16">
                    <h3 class="text-2xl md:text-4xl font-black text-gray-900 mb-10 tracking-tighter">Customer Voice ({{ reviews|length }})</h3>
                    
                    <form action="/review/{{ food._id }}" method="POST" class="bg-gray-50 p-8 rounded-[40px] space-y-6 mb-12 border">
                        <select name="stars" class="w-full bg-white border-none shadow-sm p-5 rounded-2xl outline-none focus:ring-2 focus:ring-{{ settings.theme }}-500 text-lg">
                            <option value="5">⭐⭐⭐⭐⭐ Outstanding</option>
                            <option value="4">⭐⭐⭐⭐ Good</option>
                            <option value="3">⭐⭐⭐ Average</option>
                            <option value="2">⭐⭐ Poor</option>
                            <option value="1">⭐ Bad</option>
                        </select>
                        <textarea name="comment" placeholder="How was the taste?" class="w-full bg-white border-none shadow-sm p-6 rounded-2xl h-32 md:h-48 outline-none focus:ring-2 focus:ring-{{ settings.theme }}-500 text-lg" required></textarea>
                        <button class="w-full bg-{{ settings.theme }}-600 text-white py-5 rounded-2xl font-black text-xl shadow-xl">Post Review</button>
                    </form>

                    <div class="space-y-6">
                        {% for r in reviews %}
                        <div class="p-8 bg-white border rounded-[30px] shadow-sm hover:shadow-md transition-shadow">
                            <div class="text-yellow-400 text-sm md:text-xl mb-4">
                                {% for i in range(r.stars) %}⭐{% endfor %}
                            </div>
                            <p class="text-gray-700 text-base md:text-2xl italic leading-relaxed">"{{ r.comment }}"</p>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """, food=food, settings=settings, reviews=reviews, wa_clean=wa_clean)

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
        <div class="max-w-md mx-auto mt-24 p-10 bg-white shadow-2xl rounded-[50px] border text-center animate__animated animate__zoomIn">
            <h2 class="text-3xl font-black mb-8 text-gray-800 tracking-tighter">Admin Access</h2>
            <form action="/admin/login" method="POST" class="space-y-6">
                <input type="password" name="pass" placeholder="Master Password" class="w-full border-none bg-gray-100 p-5 rounded-2xl text-center outline-none focus:ring-2 focus:ring-black text-lg">
                <button class="w-full bg-gray-900 text-white py-5 rounded-2xl font-black text-xl hover:bg-black transition-all">Unlock Panel</button>
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
    <head>"""+HEAD+"""<title>Admin Panel</title></head>
    <body class="flex flex-col lg:flex-row min-h-screen bg-gray-50">
        <!-- Sidebar -->
        <div class="w-full lg:w-80 bg-gray-900 text-white p-10 flex flex-col">
            <h2 class="text-3xl font-black mb-16 tracking-tighter flex items-center gap-3"><img src="{{ settings.logo }}" class="w-10 h-10 rounded-full"> Control</h2>
            <nav class="space-y-4 flex-1">
                <a href="/admin/dash" class="flex items-center gap-4 p-5 bg-{{ settings.theme }}-600 rounded-[24px] shadow-xl"><i class="fas fa-chart-pie"></i> Dashboard</a>
                <a href="/admin/add-food" class="flex items-center gap-4 p-5 hover:bg-gray-800 rounded-[24px] transition-all"><i class="fas fa-utensils"></i> Add Food</a>
                <a href="/admin/add-cat" class="flex items-center gap-4 p-5 hover:bg-gray-800 rounded-[24px] transition-all"><i class="fas fa-layer-group"></i> Categories</a>
                <a href="/admin/settings" class="flex items-center gap-4 p-5 hover:bg-gray-800 rounded-[24px] transition-all"><i class="fas fa-sliders-h"></i> Settings</a>
            </nav>
            <a href="/admin/logout" class="mt-10 p-5 text-red-400 font-bold border border-red-900/20 rounded-2xl flex items-center gap-3 justify-center"><i class="fas fa-sign-out-alt"></i> Logout</a>
        </div>

        <!-- Content -->
        <div class="flex-1 p-6 md:p-16">
            <div class="grid grid-cols-2 lg:grid-cols-4 gap-6 md:gap-10 mb-16">
                <div class="bg-white p-8 rounded-[40px] shadow-sm border-b-8 border-blue-500">
                    <p class="text-gray-400 text-xs font-black uppercase tracking-widest">Global Reach</p>
                    <h3 class="text-4xl font-black mt-2">{{ total_views }}</h3>
                </div>
                <div class="bg-white p-8 rounded-[40px] shadow-sm border-b-8 border-green-500">
                    <p class="text-gray-400 text-xs font-black uppercase tracking-widest">Today</p>
                    <h3 class="text-4xl font-black mt-2 text-green-600">{{ today_views }}</h3>
                </div>
                <div class="bg-white p-8 rounded-[40px] shadow-sm border-b-8 border-orange-500">
                    <p class="text-gray-400 text-xs font-black uppercase tracking-widest">Inventory</p>
                    <h3 class="text-4xl font-black mt-2 text-orange-500">{{ total_foods }}</h3>
                </div>
                <div class="bg-white p-8 rounded-[40px] shadow-sm border-b-8 border-purple-500">
                    <p class="text-gray-400 text-xs font-black uppercase tracking-widest">Groups</p>
                    <h3 class="text-4xl font-black mt-2 text-purple-600">{{ total_cats }}</h3>
                </div>
            </div>

            <div class="bg-white p-10 rounded-[50px] shadow-sm border">
                <h3 class="text-2xl font-black mb-8 tracking-tighter">Recent Reviews</h3>
                <div class="space-y-4">
                    {% for c in latest_comments %}
                    <div class="p-6 bg-gray-50 rounded-3xl border flex justify-between items-center">
                        <p class="text-gray-600 italic">"{{ c.comment }}"</p>
                        <span class="bg-yellow-100 text-yellow-600 px-4 py-2 rounded-full font-black text-xs">{{ c.stars }} ⭐</span>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </body>
    </html>
    """, total_foods=total_foods, total_cats=total_cats, total_views=total_views, today_views=today_views, latest_comments=latest_comments, settings=settings)

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
    <body class="p-6 md:p-16 bg-gray-50">
        <div class="max-w-4xl mx-auto">
            <h2 class="text-3xl md:text-5xl font-black mb-10 tracking-tighter">Register New Food</h2>
            <form method="POST" class="bg-white p-10 md:p-16 rounded-[50px] shadow-2xl border space-y-6">
                <div class="grid md:grid-cols-2 gap-6">
                    <input name="name" placeholder="Item Name" class="w-full bg-gray-50 border-none p-5 rounded-2xl outline-none focus:ring-2 focus:ring-orange-500" required>
                    <input name="price" placeholder="Price (৳)" class="w-full bg-gray-50 border-none p-5 rounded-2xl outline-none focus:ring-2 focus:ring-orange-500" required>
                </div>
                <input name="image" placeholder="Primary Image URL" class="w-full bg-gray-50 border-none p-5 rounded-2xl outline-none focus:ring-2 focus:ring-orange-500" required>
                <select name="category" class="w-full bg-gray-50 border-none p-5 rounded-2xl outline-none focus:ring-2 focus:ring-orange-500">
                    {% for cat in categories %} <option value="{{ cat.name }}">{{ cat.name }}</option> {% endfor %}
                </select>
                <textarea name="screenshots" placeholder="Comma separated screenshot URLs" class="w-full bg-gray-50 border-none p-5 rounded-2xl h-24 outline-none focus:ring-2 focus:ring-orange-500"></textarea>
                <textarea name="details" placeholder="Full preparation details..." class="w-full bg-gray-50 border-none p-5 rounded-2xl h-48 outline-none focus:ring-2 focus:ring-orange-500" required></textarea>
                <button class="w-full bg-orange-600 text-white py-6 rounded-2xl font-black text-2xl shadow-2xl hover:bg-orange-700 transition-all">Launch Item</button>
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
    <body class="p-6 md:p-16 bg-gray-100 min-h-screen">
        <div class="max-w-6xl mx-auto grid md:grid-cols-2 gap-12">
            <form method="POST" class="bg-white p-12 rounded-[50px] shadow-xl border h-fit">
                <h3 class="text-3xl font-black mb-8 tracking-tighter">New Category</h3>
                <input name="name" placeholder="Name" class="w-full bg-gray-50 border-none p-5 rounded-2xl mb-4 outline-none focus:ring-2 focus:ring-gray-900" required>
                <input name="logo" placeholder="Icon URL" class="w-full bg-gray-50 border-none p-5 rounded-2xl mb-6 outline-none focus:ring-2 focus:ring-gray-900" required>
                <button class="w-full bg-gray-900 text-white py-5 rounded-2xl font-black text-xl">Create Group</button>
            </form>
            <div class="bg-white p-12 rounded-[50px] shadow-xl border">
                <h3 class="text-3xl font-black mb-8 tracking-tighter">Existing Groups</h3>
                <div class="space-y-4">
                    {% for cat in categories %}
                    <div class="flex justify-between items-center p-5 bg-gray-50 rounded-[24px] border">
                        <div class="flex items-center gap-4">
                            <img src="{{ cat.logo }}" class="w-14 h-14 rounded-full object-cover shadow-sm">
                            <span class="font-black text-gray-700 text-lg">{{ cat.name }}</span>
                        </div>
                        <a href="/admin/del-cat/{{ cat._id }}" class="text-red-500 bg-red-50 w-12 h-12 flex items-center justify-center rounded-2xl hover:bg-red-500 hover:text-white transition-all"><i class="fas fa-trash-alt"></i></a>
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
            "privacy": request.form.get('privacy'),
            "header_text": request.form.get('header_text')
        }
        settings_col.update_one({"id": "config"}, {"$set": updated})
        return redirect('/admin/dash')

    return render_template_string("""
    <head>"""+HEAD+"""</head>
    <body class="p-6 md:p-16 bg-gray-50">
        <form method="POST" class="max-w-5xl mx-auto bg-white p-10 md:p-20 rounded-[60px] shadow-2xl grid grid-cols-1 md:grid-cols-2 gap-8 border">
            <h2 class="col-span-full text-4xl font-black mb-6 tracking-tighter">Global Parameters</h2>
            
            <div class="space-y-1"><label class="text-xs font-black text-gray-400 px-2 uppercase tracking-widest">Brand Name</label><input name="name" value="{{ s.name }}" class="w-full bg-gray-50 border-none p-5 rounded-2xl outline-none"></div>
            <div class="space-y-1"><label class="text-xs font-black text-gray-400 px-2 uppercase tracking-widest">Brand Logo</label><input name="logo" value="{{ s.logo }}" class="w-full bg-gray-50 border-none p-5 rounded-2xl outline-none"></div>
            <div class="space-y-1"><label class="text-xs font-black text-gray-400 px-2 uppercase tracking-widest">WhatsApp</label><input name="whatsapp" value="{{ s.whatsapp }}" class="w-full bg-gray-50 border-none p-5 rounded-2xl outline-none"></div>
            <div class="space-y-1"><label class="text-xs font-black text-gray-400 px-2 uppercase tracking-widest">Facebook</label><input name="fb" value="{{ s.fb }}" class="w-full bg-gray-50 border-none p-5 rounded-2xl outline-none"></div>
            <div class="space-y-1"><label class="text-xs font-black text-gray-400 px-2 uppercase tracking-widest">Master Key</label><input name="pass" value="{{ s.pass }}" class="w-full bg-gray-50 border-none p-5 rounded-2xl outline-none"></div>
            
            <div class="space-y-1"><label class="text-xs font-black text-gray-400 px-2 uppercase tracking-widest">Theme Palette</label>
                <select name="theme" class="w-full bg-gray-50 border-none p-5 rounded-2xl outline-none">
                    <option value="orange" {% if s.theme=='orange' %}selected{% endif %}>Sunset Orange</option>
                    <option value="blue" {% if s.theme=='blue' %}selected{% endif %}>Ocean Blue</option>
                    <option value="green" {% if s.theme=='green' %}selected{% endif %}>Forest Green</option>
                    <option value="red" {% if s.theme=='red' %}selected{% endif %}>Ruby Red</option>
                    <option value="purple" {% if s.theme=='purple' %}selected{% endif %}>Royal Purple</option>
                </select>
            </div>

            <div class="col-span-full space-y-1"><label class="text-xs font-black text-gray-400 px-2 uppercase tracking-widest">Hero Header Text</label><input name="header_text" value="{{ s.header_text }}" class="w-full bg-gray-50 border-none p-5 rounded-2xl outline-none"></div>
            <div class="col-span-full space-y-1"><label class="text-xs font-black text-gray-400 px-2 uppercase tracking-widest">Footer Slogan</label><input name="footer_text" value="{{ s.footer_text }}" class="w-full bg-gray-50 border-none p-5 rounded-2xl outline-none"></div>
            <div class="col-span-full space-y-1"><label class="text-xs font-black text-gray-400 px-2 uppercase tracking-widest">Compliance & Privacy</label><textarea name="privacy" class="w-full bg-gray-50 border-none p-6 rounded-[30px] h-40 outline-none">{{ s.privacy }}</textarea></div>
            
            <div class="space-y-1"><label class="text-xs font-black text-gray-400 px-2 uppercase tracking-widest">DMCA Rights</label><input name="dmca" value="{{ s.dmca }}" class="w-full bg-gray-50 border-none p-5 rounded-2xl outline-none"></div>
            <div class="space-y-1"><label class="text-xs font-black text-gray-400 px-2 uppercase tracking-widest">Copyright Signature</label><input name="copyright" value="{{ s.copyright }}" class="w-full bg-gray-50 border-none p-5 rounded-2xl outline-none"></div>
            
            <button class="col-span-full bg-gray-900 text-white py-6 rounded-[30px] font-black text-2xl mt-10 shadow-2xl">Push Updates</button>
        </form>
    </body>
    """, s=settings)

if __name__ == '__main__':
    app.run(debug=True)
