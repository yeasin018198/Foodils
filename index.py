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

# --- CSS / Theme mapping ---
THEME_COLORS = {
    "orange": "#f97316", "blue": "#2563eb", "red": "#dc2626", "green": "#16a34a", 
    "indigo": "#4f46e5", "pink": "#db2777", "purple": "#9333ea", "teal": "#0d9488"
}

# --- PREMIUM UI ASSETS ---
HEAD = """
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<script src="https://cdn.tailwindcss.com"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css"/>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap');
    body { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #fdfdfd; }
    .no-scrollbar::-webkit-scrollbar { display: none; }
    .glass { background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(10px); }
    .premium-card { transition: all 0.3s ease; border: 1px solid #f1f5f9; }
    .premium-card:hover { transform: translateY(-5px); box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.1); }
    .gradient-bg { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
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
    <html>
    <head>"""+HEAD+"""<title>{{ settings.name }} - Premium Food</title></head>
    <body class="text-slate-800">
        <!-- Header -->
        <nav class="glass sticky top-0 z-50 px-5 py-4 flex justify-between items-center border-b border-gray-100">
            <div class="flex items-center gap-3">
                <img src="{{ settings.logo }}" class="w-11 h-11 rounded-2xl shadow-lg ring-2 ring-{{ settings.theme }}-500/20">
                <div>
                    <h1 class="text-xl font-extrabold text-slate-900 leading-tight">{{ settings.name }}</h1>
                    <p class="text-[10px] text-{{ settings.theme }}-600 font-bold uppercase tracking-widest">Premium Service</p>
                </div>
            </div>
            <div class="flex items-center gap-4">
                <div class="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center text-slate-500">
                    <i class="fas fa-search"></i>
                </div>
            </div>
        </nav>

        <!-- Welcome Banner -->
        <div class="p-5">
            <div class="bg-{{ settings.theme }}-600 rounded-3xl p-6 text-white relative overflow-hidden shadow-2xl shadow-{{ settings.theme }}-500/30">
                <div class="relative z-10">
                    <h2 class="text-2xl font-bold italic">{{ settings.header_text }}</h2>
                    <p class="text-white/80 mt-1 text-sm">Delicious meals delivered to your doorstep.</p>
                </div>
                <i class="fas fa-utensils absolute -right-4 -bottom-4 text-7xl text-white/10 rotate-12"></i>
            </div>
        </div>

        <!-- Categories -->
        <div class="px-5 mb-2 flex justify-between items-center">
            <h3 class="font-bold text-lg">Categories</h3>
            <span class="text-xs text-{{ settings.theme }}-600 font-bold">View All</span>
        </div>
        <div class="flex gap-5 overflow-x-auto no-scrollbar px-5 py-2">
            {% for cat in categories %}
            <a href="/category/{{ cat.name }}" class="flex flex-col items-center min-w-[70px] group">
                <div class="w-16 h-16 rounded-2xl bg-white shadow-md flex items-center justify-center mb-2 group-hover:bg-{{ settings.theme }}-500 transition-all border border-gray-100 ring-2 ring-transparent group-hover:ring-{{ settings.theme }}-500/30">
                    <img src="{{ cat.logo }}" class="w-12 h-12 rounded-xl object-cover">
                </div>
                <span class="text-[11px] font-bold text-slate-600">{{ cat.name }}</span>
            </a>
            {% endfor %}
        </div>

        <!-- Hero Slider (Featured) -->
        <div class="p-5">
            <h2 class="text-xl font-extrabold mb-4 flex items-center gap-2">
                <span class="w-2 h-6 bg-{{ settings.theme }}-500 rounded-full"></span> Featured Delights
            </h2>
            <div class="flex gap-5 overflow-x-auto no-scrollbar pb-4">
                {% for item in slider_items %}
                <a href="/food/{{ item._id }}" class="min-w-[280px] bg-white rounded-[2rem] shadow-xl shadow-slate-200/50 overflow-hidden relative border border-slate-100">
                    <div class="relative">
                        <img src="{{ item.image }}" class="w-full h-44 object-cover">
                        <div class="absolute top-4 right-4 bg-white/90 backdrop-blur px-3 py-1 rounded-full text-xs font-bold shadow-sm">
                            ⭐ 4.8
                        </div>
                    </div>
                    <div class="p-5">
                        <h3 class="font-bold text-lg text-slate-800">{{ item.name }}</h3>
                        <div class="flex justify-between items-center mt-3">
                            <p class="text-2xl font-black text-{{ settings.theme }}-600">৳{{ item.price }}</p>
                            <span class="bg-{{ settings.theme }}-50 text-{{ settings.theme }}-600 p-2 rounded-xl"><i class="fas fa-plus"></i></span>
                        </div>
                    </div>
                </a>
                {% endfor %}
            </div>
        </div>

        <!-- Food Grid -->
        <div class="px-5 mb-20">
            <h2 class="text-xl font-extrabold mb-4 flex items-center gap-2">
                <span class="w-2 h-6 bg-slate-800 rounded-full"></span> Explore Menu
            </h2>
            <div class="grid grid-cols-2 gap-4">
                {% for food in all_foods %}
                <a href="/food/{{ food._id }}" class="premium-card bg-white rounded-3xl p-3 animate__animated animate__fadeInUp">
                    <img src="{{ food.image }}" class="w-full h-36 object-cover rounded-2xl mb-3 shadow-inner">
                    <h4 class="text-sm font-bold text-slate-800 truncate px-1">{{ food.name }}</h4>
                    <div class="flex justify-between items-center mt-2 px-1">
                        <span class="text-{{ settings.theme }}-600 font-extrabold">৳{{ food.price }}</span>
                        <span class="text-[8px] bg-slate-100 px-2 py-1 rounded-lg text-slate-500 font-bold uppercase tracking-tighter">{{ food.category }}</span>
                    </div>
                </a>
                {% endfor %}
            </div>
        </div>

        <!-- Premium Footer -->
        <footer class="bg-slate-900 text-white rounded-t-[3rem] p-10 text-center">
            <img src="{{ settings.logo }}" class="w-16 h-16 rounded-2xl mx-auto mb-4 border-2 border-white/20">
            <h2 class="text-2xl font-bold mb-2">{{ settings.name }}</h2>
            <p class="text-slate-400 text-sm mb-6">{{ settings.footer_text }}</p>
            <div class="flex justify-center gap-5 mb-8">
                <a href="{{ settings.fb }}" class="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center text-xl hover:bg-{{ settings.theme }}-600 transition-all"><i class="fab fa-facebook-f"></i></a>
                <a href="https://wa.me/{{ settings.whatsapp }}" class="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center text-xl hover:bg-green-500 transition-all"><i class="fab fa-whatsapp"></i></a>
            </div>
            <div class="border-t border-white/5 pt-8">
                <p class="text-[10px] text-slate-500 uppercase tracking-[0.2em] mb-2">{{ settings.dmca }}</p>
                <p class="text-xs text-slate-500">{{ settings.copyright }}</p>
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
    <body class="bg-white">
        <div class="max-w-md mx-auto min-h-screen relative pb-20">
            <!-- Top Nav -->
            <div class="absolute top-6 left-6 z-10">
                <a href="/" class="w-10 h-10 glass rounded-full flex items-center justify-center shadow-lg"><i class="fas fa-chevron-left"></i></a>
            </div>
            
            <img src="{{ food.image }}" class="w-full h-[400px] object-cover rounded-b-[3rem] shadow-2xl">
            
            <div class="px-6 -mt-10 relative z-20">
                <div class="bg-white rounded-[2.5rem] p-8 shadow-xl border border-slate-50">
                    <div class="flex justify-between items-start mb-4">
                        <div>
                            <span class="text-{{ settings.theme }}-600 text-xs font-black uppercase tracking-widest bg-{{ settings.theme }}-50 px-3 py-1 rounded-full">{{ food.category }}</span>
                            <h1 class="text-3xl font-extrabold text-slate-900 mt-2">{{ food.name }}</h1>
                        </div>
                        <p class="text-2xl font-black text-slate-900">৳{{ food.price }}</p>
                    </div>

                    <!-- Gallery -->
                    <div class="flex gap-3 overflow-x-auto no-scrollbar my-6">
                        {% for ss in food.screenshots %}
                        <img src="{{ ss }}" class="w-20 h-20 rounded-2xl object-cover ring-2 ring-slate-100">
                        {% endfor %}
                    </div>

                    <div class="space-y-4">
                        <h4 class="font-bold text-lg flex items-center gap-2"><i class="fas fa-info-circle text-{{ settings.theme }}-500"></i> Description</h4>
                        <p class="text-slate-500 leading-relaxed text-sm">{{ food.details }}</p>
                    </div>

                    <a href="https://wa.me/{{ settings.whatsapp }}?text=New Order Request!%0A---%0AItem: {{ food.name }}%0APrice: {{ food.price }}" 
                       class="flex items-center justify-center gap-3 mt-8 bg-green-500 text-white py-5 rounded-3xl font-bold text-lg shadow-xl shadow-green-200 hover:bg-green-600 transition-all">
                       <i class="fab fa-whatsapp text-2xl"></i> Confirm Order
                    </a>
                </div>

                <!-- Review Section -->
                <div class="mt-10">
                    <h3 class="text-xl font-bold mb-6">Customer Reviews</h3>
                    <form action="/review/{{ food._id }}" method="POST" class="bg-slate-50 p-6 rounded-[2rem] space-y-4 border border-slate-100">
                        <div class="flex gap-2 mb-2">
                            <select name="stars" class="bg-white border-none rounded-xl px-4 py-2 font-bold text-sm shadow-sm outline-none">
                                <option value="5">⭐⭐⭐⭐⭐</option>
                                <option value="4">⭐⭐⭐⭐</option>
                                <option value="3">⭐⭐⭐</option>
                                <option value="2">⭐⭐</option>
                                <option value="1">⭐</option>
                            </select>
                        </div>
                        <textarea name="comment" placeholder="How was the taste?" class="w-full border-none bg-white p-4 rounded-2xl h-24 text-sm shadow-sm outline-none" required></textarea>
                        <button class="w-full bg-slate-900 text-white py-4 rounded-2xl font-bold hover:bg-black">Submit Review</button>
                    </form>

                    <div class="mt-8 space-y-4">
                        {% for r in reviews %}
                        <div class="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm">
                            <div class="flex justify-between items-center mb-2">
                                <div class="flex text-yellow-400 text-[10px]">
                                    {% for i in range(r.stars) %}<i class="fas fa-star"></i>{% endfor %}
                                </div>
                                <span class="text-[10px] text-slate-400 font-bold">Verified User</span>
                            </div>
                            <p class="text-slate-600 text-sm italic">"{{ r.comment }}"</p>
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
        <!DOCTYPE html>
        <html>
        <head>"""+HEAD+"""<title>Admin Login</title></head>
        <body class="gradient-bg min-h-screen flex items-center justify-center p-6">
            <div class="max-w-md w-full bg-white rounded-[3rem] p-10 shadow-2xl animate__animated animate__fadeIn">
                <div class="text-center mb-8">
                    <div class="w-20 h-20 bg-slate-100 rounded-3xl mx-auto flex items-center justify-center mb-4 text-3xl">
                        <i class="fas fa-user-shield text-slate-800"></i>
                    </div>
                    <h2 class="text-3xl font-black text-slate-900">Admin Login</h2>
                    <p class="text-slate-400 text-sm mt-2">Enter your secure password</p>
                </div>
                <form action="/admin/login" method="POST" class="space-y-5">
                    <div class="relative">
                        <i class="fas fa-lock absolute left-5 top-5 text-slate-400"></i>
                        <input type="password" name="pass" placeholder="••••••••" class="w-full bg-slate-50 border-none p-5 pl-14 rounded-2xl focus:ring-2 focus:ring-slate-900 outline-none transition-all">
                    </div>
                    <button class="w-full bg-slate-900 text-white py-5 rounded-2xl font-bold shadow-lg hover:shadow-xl hover:scale-[1.02] active:scale-95 transition-all">Access Dashboard</button>
                </form>
            </div>
        </body>
        </html>
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
    <head>"""+HEAD+"""<title>Premium Admin Panel</title></head>
    <body class="bg-slate-50 flex flex-col md:flex-row">
        <!-- Modern Sidebar -->
        <div class="w-full md:w-72 bg-white min-h-screen p-8 border-r border-slate-200">
            <div class="flex items-center gap-3 mb-12">
                <div class="w-10 h-10 bg-{{ settings.theme }}-600 rounded-xl flex items-center justify-center text-white shadow-lg">
                    <i class="fas fa-bolt"></i>
                </div>
                <h2 class="text-xl font-black tracking-tight">ADMIN PANEL</h2>
            </div>
            <nav class="space-y-2">
                <a href="/admin/dash" class="flex items-center gap-4 p-4 bg-{{ settings.theme }}-50 text-{{ settings.theme }}-600 rounded-2xl font-bold"><i class="fas fa-chart-pie w-6"></i> Dashboard</a>
                <a href="/admin/add-food" class="flex items-center gap-4 p-4 text-slate-500 hover:bg-slate-50 rounded-2xl font-bold transition-all"><i class="fas fa-hamburger w-6"></i> Add Food</a>
                <a href="/admin/add-cat" class="flex items-center gap-4 p-4 text-slate-500 hover:bg-slate-50 rounded-2xl font-bold transition-all"><i class="fas fa-tags w-6"></i> Categories</a>
                <a href="/admin/settings" class="flex items-center gap-4 p-4 text-slate-500 hover:bg-slate-50 rounded-2xl font-bold transition-all"><i class="fas fa-sliders-h w-6"></i> Settings</a>
                <div class="pt-10 space-y-2">
                    <a href="/" class="flex items-center gap-4 p-4 text-blue-600 bg-blue-50 rounded-2xl font-bold"><i class="fas fa-external-link-alt w-6"></i> Live Site</a>
                    <a href="/admin/logout" class="flex items-center gap-4 p-4 text-red-500 bg-red-50 rounded-2xl font-bold"><i class="fas fa-power-off w-6"></i> Logout</a>
                </div>
            </nav>
        </div>

        <!-- Main Content -->
        <div class="flex-1 p-8 md:p-12">
            <header class="flex justify-between items-center mb-10">
                <h1 class="text-3xl font-black text-slate-900">System Overview</h1>
                <div class="text-right">
                    <p class="text-slate-400 font-bold text-xs uppercase tracking-widest">Server Status</p>
                    <p class="text-green-500 font-bold flex items-center justify-end gap-2"><span class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span> Online</p>
                </div>
            </header>

            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                <div class="bg-white p-8 rounded-[2rem] shadow-sm border border-slate-100">
                    <p class="text-slate-400 font-bold text-xs uppercase mb-2">Total Visits</p>
                    <h3 class="text-4xl font-black">{{ total_views }}</h3>
                </div>
                <div class="bg-white p-8 rounded-[2rem] shadow-sm border border-slate-100">
                    <p class="text-slate-400 font-bold text-xs uppercase mb-2">Today's Visits</p>
                    <h3 class="text-4xl font-black text-blue-600">{{ today_views }}</h3>
                </div>
                <div class="bg-white p-8 rounded-[2rem] shadow-sm border border-slate-100">
                    <p class="text-slate-400 font-bold text-xs uppercase mb-2">Active Menu</p>
                    <h3 class="text-4xl font-black text-orange-500">{{ total_foods }}</h3>
                </div>
                <div class="bg-white p-8 rounded-[2rem] shadow-sm border border-slate-100">
                    <p class="text-slate-400 font-bold text-xs uppercase mb-2">Categories</p>
                    <h3 class="text-4xl font-black text-purple-600">{{ total_cats }}</h3>
                </div>
            </div>

            <!-- Recent Reviews Table -->
            <div class="mt-10 bg-white p-10 rounded-[3rem] shadow-sm border border-slate-100">
                <h3 class="text-xl font-extrabold mb-8 flex items-center gap-3"><i class="fas fa-comment-dots text-{{ settings.theme }}-500"></i> Customer Feedback</h3>
                <div class="overflow-hidden">
                    <table class="w-full text-left">
                        <thead>
                            <tr class="text-slate-400 text-xs uppercase border-b">
                                <th class="pb-4 font-black">Comment</th>
                                <th class="pb-4 font-black text-center">Rating</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y">
                            {% for c in comments %}
                            <tr>
                                <td class="py-5 text-slate-600 italic">"{{ c.comment }}"</td>
                                <td class="py-5 text-center">
                                    <span class="bg-yellow-100 text-yellow-600 px-3 py-1 rounded-full text-xs font-black">{{ c.stars }} ⭐</span>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
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
    <!DOCTYPE html>
    <html>
    <head>"""+HEAD+"""<title>Add Premium Food</title></head>
    <body class="bg-slate-50 p-10">
        <div class="max-w-3xl mx-auto">
            <h2 class="text-3xl font-black mb-8">Add New Food Item</h2>
            <form method="POST" class="bg-white p-10 rounded-[3rem] shadow-xl space-y-6">
                <div class="grid grid-cols-2 gap-6">
                    <input name="name" placeholder="Item Name" class="w-full bg-slate-50 p-5 rounded-2xl border-none outline-none focus:ring-2 focus:ring-slate-900" required>
                    <input name="price" placeholder="Price (৳)" class="w-full bg-slate-50 p-5 rounded-2xl border-none outline-none focus:ring-2 focus:ring-slate-900" required>
                </div>
                <input name="image" placeholder="Main Image URL" class="w-full bg-slate-50 p-5 rounded-2xl border-none outline-none focus:ring-2 focus:ring-slate-900" required>
                <select name="category" class="w-full bg-slate-50 p-5 rounded-2xl border-none outline-none focus:ring-2 focus:ring-slate-900">
                    {% for cat in categories %} <option value="{{ cat.name }}">{{ cat.name }}</option> {% endfor %}
                </select>
                <textarea name="screenshots" placeholder="Gallery URLs (URL1, URL2...)" class="w-full bg-slate-50 p-5 rounded-2xl h-24 border-none outline-none focus:ring-2 focus:ring-slate-900"></textarea>
                <textarea name="details" placeholder="Full Description..." class="w-full bg-slate-50 p-5 rounded-2xl h-40 border-none outline-none focus:ring-2 focus:ring-slate-900" required></textarea>
                <button class="w-full bg-slate-900 text-white py-5 rounded-2xl font-bold text-lg shadow-lg hover:shadow-xl transition-all">Publish Item</button>
            </form>
        </div>
    </body>
    </html>
    """, categories=categories)

@app.route('/admin/add-cat', methods=['GET', 'POST'])
def admin_add_cat():
    if not session.get('admin_logged'): return redirect('/admin/dash')
    if request.method == 'POST':
        cats_col.insert_one({"name": request.form.get('name'), "logo": request.form.get('logo')})
    
    categories = list(cats_col.find())
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>"""+HEAD+"""<title>Categories Manager</title></head>
    <body class="p-10 bg-slate-50">
        <div class="max-w-6xl mx-auto grid md:grid-cols-2 gap-10">
            <form method="POST" class="bg-white p-10 rounded-[3rem] shadow-xl h-fit">
                <h3 class="text-2xl font-black mb-6">Create Category</h3>
                <input name="name" placeholder="Category Name" class="w-full bg-slate-50 p-5 rounded-2xl mb-4 border-none outline-none focus:ring-2 focus:ring-slate-900">
                <input name="logo" placeholder="Logo Image URL" class="w-full bg-slate-50 p-5 rounded-2xl mb-6 border-none outline-none focus:ring-2 focus:ring-slate-900">
                <button class="w-full bg-slate-900 text-white py-5 rounded-2xl font-bold">Add Category</button>
            </form>
            <div class="bg-white p-10 rounded-[3rem] shadow-xl">
                <h3 class="text-2xl font-black mb-6">Existing Categories</h3>
                <div class="space-y-4">
                    {% for cat in categories %}
                    <div class="flex justify-between items-center p-4 bg-slate-50 rounded-2xl border border-slate-100">
                        <div class="flex items-center gap-4">
                            <img src="{{ cat.logo }}" class="w-12 h-12 rounded-xl object-cover ring-2 ring-white">
                            <span class="font-bold text-slate-700">{{ cat.name }}</span>
                        </div>
                        <a href="/admin/del-cat/{{ cat._id }}" class="text-red-500 bg-red-100 w-10 h-10 flex items-center justify-center rounded-xl hover:bg-red-500 hover:text-white transition-all"><i class="fas fa-trash-alt"></i></a>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </body>
    </html>
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
    <!DOCTYPE html>
    <html>
    <head>"""+HEAD+"""<title>System Settings</title></head>
    <body class="p-10 bg-slate-50">
        <form method="POST" class="max-w-4xl mx-auto bg-white p-12 rounded-[3rem] shadow-xl">
            <h2 class="text-3xl font-black mb-10 flex items-center gap-4 text-slate-900"><i class="fas fa-tools text-{{ s.theme }}-500"></i> Settings & UI</h2>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div class="space-y-2">
                    <label class="font-black text-xs uppercase text-slate-400 px-1">Brand Name</label>
                    <input name="name" value="{{ s.name }}" class="w-full bg-slate-50 p-5 rounded-2xl border-none outline-none focus:ring-2 focus:ring-slate-900">
                </div>
                <div class="space-y-2">
                    <label class="font-black text-xs uppercase text-slate-400 px-1">Logo URL</label>
                    <input name="logo" value="{{ s.logo }}" class="w-full bg-slate-50 p-5 rounded-2xl border-none outline-none focus:ring-2 focus:ring-slate-900">
                </div>
                <div class="space-y-2">
                    <label class="font-black text-xs uppercase text-slate-400 px-1">WhatsApp Business</label>
                    <input name="whatsapp" value="{{ s.whatsapp }}" class="w-full bg-slate-50 p-5 rounded-2xl border-none outline-none focus:ring-2 focus:ring-slate-900">
                </div>
                <div class="space-y-2">
                    <label class="font-black text-xs uppercase text-slate-400 px-1">Facebook URL</label>
                    <input name="fb" value="{{ s.fb }}" class="w-full bg-slate-50 p-5 rounded-2xl border-none outline-none focus:ring-2 focus:ring-slate-900">
                </div>
                <div class="space-y-2">
                    <label class="font-black text-xs uppercase text-slate-400 px-1">Admin Password</label>
                    <input name="pass" value="{{ s.pass }}" class="w-full bg-slate-50 p-5 rounded-2xl border-none outline-none focus:ring-2 focus:ring-slate-900">
                </div>
                <div class="space-y-2">
                    <label class="font-black text-xs uppercase text-slate-400 px-1">Accent Theme</label>
                    <select name="theme" class="w-full bg-slate-50 p-5 rounded-2xl border-none outline-none focus:ring-2 focus:ring-slate-900">
                        <option value="orange" {% if s.theme=='orange' %}selected{% endif %}>Sunset Orange</option>
                        <option value="blue" {% if s.theme=='blue' %}selected{% endif %}>Ocean Blue</option>
                        <option value="red" {% if s.theme=='red' %}selected{% endif %}>Crimson Red</option>
                        <option value="green" {% if s.theme=='green' %}selected{% endif %}>Eco Green</option>
                        <option value="pink" {% if s.theme=='pink' %}selected{% endif %}>Hot Pink</option>
                        <option value="indigo" {% if s.theme=='indigo' %}selected{% endif %}>Indigo</option>
                    </select>
                </div>
                <div class="col-span-2 space-y-2">
                    <label class="font-black text-xs uppercase text-slate-400 px-1">Footer Tagline</label>
                    <input name="footer_text" value="{{ s.footer_text }}" class="w-full bg-slate-50 p-5 rounded-2xl border-none outline-none focus:ring-2 focus:ring-slate-900">
                </div>
                <div class="col-span-2 space-y-2">
                    <label class="font-black text-xs uppercase text-slate-400 px-1">Privacy Content</label>
                    <textarea name="privacy" class="w-full bg-slate-50 p-5 rounded-2xl h-32 border-none outline-none focus:ring-2 focus:ring-slate-900">{{ s.privacy }}</textarea>
                </div>
            </div>
            <button class="w-full bg-slate-900 text-white py-6 rounded-3xl font-black text-xl mt-12 shadow-2xl hover:bg-black transition-all">Save All Configurations</button>
        </form>
    </body>
    </html>
    """, s=settings)

if __name__ == '__main__':
    app.run(debug=True)
