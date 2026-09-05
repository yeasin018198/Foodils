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
options_col = db['global_options']

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

# --- TEMPLATES HEAD ---
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
    @media (min-width: 768px) { .food-card img { height: 240px; } }
    .glass { background: rgba(255, 255, 255, 0.9); backdrop-filter: blur(10px); }
    .category-icon { min-width: 80px; transition: 0.2s; }
    .category-icon:hover { transform: scale(1.1); }
</style>
"""

# --- USER ROUTES ---

@app.route('/')
def home():
    track_view()
    settings = get_site_settings()
    categories = list(cats_col.find())
    
    # Slider logic: 3 items from each category
    slider_items = []
    for c in categories:
        items = list(foods_col.find({"category": c['name']}).limit(3))
        slider_items.extend(items)
    
    all_foods = list(foods_col.find())
    wa_clean = settings['whatsapp'].replace('+', '').replace(' ', '').replace('-', '')
    
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="bn">
    <head>"""+HEAD+"""<title>{{ settings.name }}</title></head>
    <body class="max-w-screen-2xl mx-auto">
        <nav class="glass sticky top-0 z-50 px-4 py-3 flex justify-between items-center border-b">
            <div class="flex items-center gap-2">
                <img src="{{ settings.logo }}" class="w-10 h-10 md:w-14 md:h-14 rounded-full ring-2 ring-{{ settings.theme }}-500">
                <h1 class="text-xl md:text-3xl font-bold text-{{ settings.theme }}-600">{{ settings.name }}</h1>
            </div>
            <div class="flex gap-4">
                <a href="https://wa.me/{{ wa_clean }}" class="text-green-500 text-2xl md:text-3xl"><i class="fab fa-whatsapp"></i></a>
            </div>
        </nav>

        <div class="p-4 md:px-8">
            <div class="relative max-w-2xl mx-auto mt-4">
                <input type="text" id="searchInput" onkeyup="searchFood()" placeholder="Search food..." class="w-full p-4 pl-12 rounded-2xl border-none shadow-md outline-none focus:ring-2 focus:ring-{{ settings.theme }}-500">
                <i class="fas fa-search absolute left-4 top-5 text-gray-400"></i>
            </div>
        </div>

        <div class="py-4 px-2 flex gap-4 overflow-x-auto no-scrollbar">
            {% for cat in categories %}
            <a href="/category/{{ cat.name }}" class="category-icon flex flex-col items-center">
                <div class="w-16 h-16 md:w-24 md:h-24 rounded-full border-2 border-{{ settings.theme }}-500 p-1 bg-white overflow-hidden shadow-sm">
                    <img src="{{ cat.logo }}" class="w-full h-full rounded-full object-cover">
                </div>
                <span class="text-xs md:text-sm mt-2 font-bold text-gray-700">{{ cat.name }}</span>
            </a>
            {% endfor %}
        </div>

        <div class="p-4">
            <div class="bg-{{ settings.theme }}-600 rounded-[30px] p-8 md:p-16 text-white shadow-lg relative overflow-hidden">
                <h2 class="text-2xl md:text-5xl font-black relative z-10">{{ settings.header_text }}</h2>
                <p class="mt-4 opacity-90 text-sm md:text-xl">আপনার প্রিয় খাবার এখন এক ক্লিকেই!</p>
                <i class="fas fa-hamburger absolute -right-6 -bottom-6 text-8xl md:text-[200px] opacity-20 rotate-12"></i>
            </div>
        </div>

        <div class="p-4 md:p-8">
            <h2 class="text-lg md:text-2xl font-bold mb-4 flex items-center gap-2">
                <span class="w-1.5 h-6 bg-{{ settings.theme }}-600 rounded-full"></span> Featured Foods
            </h2>
            <div class="flex gap-4 overflow-x-auto no-scrollbar pb-4">
                {% for item in slider_items %}
                <a href="/food/{{ item._id }}" class="min-w-[260px] md:min-w-[380px] bg-white rounded-3xl shadow-md border overflow-hidden">
                    <img src="{{ item.image }}" class="w-full h-44 md:h-64 object-cover">
                    <div class="p-5">
                        <h3 class="font-bold text-gray-800 md:text-xl">{{ item.name }}</h3>
                        <div class="flex justify-between items-center mt-3">
                            <span class="text-{{ settings.theme }}-600 font-bold md:text-2xl">৳{{ item.price }}</span>
                            <span class="text-[10px] bg-{{ settings.theme }}-50 text-{{ settings.theme }}-600 px-3 py-1 rounded-full uppercase">{{ item.category }}</span>
                        </div>
                    </div>
                </a>
                {% endfor %}
            </div>
        </div>

        <div class="p-4 md:p-8">
            <h2 class="text-lg md:text-2xl font-bold mb-4 flex items-center gap-2">
                <span class="w-1.5 h-6 bg-gray-800 rounded-full"></span> Regular Menu
            </h2>
            <div id="foodGrid" class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 md:gap-8">
                {% for food in all_foods %}
                <a href="/food/{{ food._id }}" class="food-item bg-white rounded-2xl p-3 md:p-5 shadow-sm hover:shadow-xl transition-all border animate__animated animate__fadeIn">
                    <img src="{{ food.image }}" alt="{{ food.name }}" class="rounded-xl object-cover w-full h-40 md:h-56">
                    <h4 class="text-sm md:text-lg font-bold mt-4 text-gray-800 truncate">{{ food.name }}</h4>
                    <div class="flex justify-between items-center mt-2">
                        <span class="text-{{ settings.theme }}-600 font-black">৳{{ food.price }}</span>
                        <div class="bg-gray-100 p-2 rounded-lg text-gray-400 text-xs"><i class="fas fa-plus"></i></div>
                    </div>
                </a>
                {% endfor %}
            </div>
        </div>

        <footer class="bg-white border-t mt-12 p-10 md:p-20 text-center">
            <img src="{{ settings.logo }}" class="w-16 h-16 rounded-full mx-auto mb-4">
            <h2 class="font-bold text-2xl mb-4">{{ settings.name }}</h2>
            <p class="text-gray-400 text-sm max-w-md mx-auto">{{ settings.footer_text }}</p>
            <div class="flex justify-center gap-8 my-8 text-3xl">
                <a href="{{ settings.fb }}" class="text-blue-600"><i class="fab fa-facebook"></i></a>
                <a href="https://wa.me/{{ wa_clean }}" class="text-green-500"><i class="fab fa-whatsapp"></i></a>
            </div>
            <div class="text-[10px] text-gray-400 border-t pt-8">
                <p>{{ settings.dmca }}</p>
                <p>{{ settings.copyright }}</p>
            </div>
        </footer>

        <script>
            function searchFood() {
                let input = document.getElementById('searchInput').value.toLowerCase();
                let items = document.getElementsByClassName('food-item');
                for (let i = 0; i < items.length; i++) {
                    items[i].style.display = items[i].innerText.toLowerCase().includes(input) ? "block" : "none";
                }
            }
        </script>
    </body>
    </html>
    """, settings=settings, categories=categories, slider_items=slider_items, all_foods=all_foods, wa_clean=wa_clean)

@app.route('/food/<id>')
def food_details(id):
    settings = get_site_settings()
    food = foods_col.find_one({"_id": ObjectId(id)})
    reviews = list(reviews_col.find({"food_id": id}).sort("_id", -1))
    wa_num = settings['whatsapp'].replace('+', '').replace(' ', '').replace('-', '')
    
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>"""+HEAD+"""<title>{{ food.name }}</title></head>
    <body class="bg-gray-50 pb-24">
        <div class="max-w-4xl mx-auto bg-white min-h-screen shadow-lg relative">
            <!-- Back Button -->
            <a href="/" class="absolute top-4 left-4 z-50 bg-white/80 p-3 rounded-2xl shadow-xl border backdrop-blur">
                <i class="fas fa-chevron-left text-gray-800"></i> Back
            </a>

            <div class="h-72 md:h-[500px]">
                <img src="{{ food.image }}" class="w-full h-full object-cover">
            </div>
            
            <div class="p-6 md:p-12 -mt-10 bg-white rounded-t-[40px] relative z-10 shadow-inner">
                <div class="flex justify-between items-start mb-8">
                    <div>
                        <span class="bg-{{ settings.theme }}-100 text-{{ settings.theme }}-600 px-4 py-1 rounded-full text-xs font-bold uppercase">{{ food.category }}</span>
                        <h1 class="text-3xl md:text-5xl font-black mt-3 text-gray-900 leading-tight">{{ food.name }}</h1>
                    </div>
                    <div class="text-right">
                        <p class="text-3xl md:text-4xl font-black text-{{ settings.theme }}-600">৳{{ food.price }}</p>
                    </div>
                </div>

                <div class="grid grid-cols-4 md:grid-cols-6 gap-3 mb-10">
                    {% for ss in food.screenshots %}
                    <img src="{{ ss }}" class="w-full aspect-square rounded-xl object-cover border">
                    {% endfor %}
                </div>

                <!-- Quantity -->
                <div class="bg-gray-50 p-6 rounded-[30px] border flex items-center justify-between mb-8">
                    <span class="font-bold text-lg">Quantity</span>
                    <div class="flex items-center gap-6">
                        <button onclick="changeQty(-1)" class="w-12 h-12 bg-white rounded-2xl shadow-sm border flex items-center justify-center text-xl"><i class="fas fa-minus"></i></button>
                        <span id="qty" class="text-2xl font-black">1</span>
                        <button onclick="changeQty(1)" class="w-12 h-12 bg-{{ settings.theme }}-600 text-white rounded-2xl shadow-lg flex items-center justify-center text-xl"><i class="fas fa-plus"></i></button>
                    </div>
                </div>

                <!-- Add-ons Selection -->
                {% if food.addons %}
                <div class="mb-8">
                    <h4 class="font-bold text-lg mb-4 flex items-center gap-2"><i class="fas fa-plus-circle text-green-500"></i> Add Extra (কুল্লু সাই)</h4>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {% for opt in food.addons %}
                        <label class="flex items-center gap-4 p-4 bg-gray-50 rounded-2xl border cursor-pointer hover:bg-green-50 transition-all">
                            <input type="checkbox" name="addon" value="{{ opt }}" class="w-6 h-6 accent-green-600">
                            <span class="font-bold text-gray-700">{{ opt }}</span>
                        </label>
                        {% endfor %}
                    </div>
                </div>
                {% endif %}

                <!-- Exclusions Selection -->
                {% if food.exclusions %}
                <div class="mb-8">
                    <h4 class="font-bold text-lg mb-4 flex items-center gap-2"><i class="fas fa-minus-circle text-red-500"></i> Without (বিদুন / ছাড়া)</h4>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {% for opt in food.exclusions %}
                        <label class="flex items-center gap-4 p-4 bg-gray-50 rounded-2xl border cursor-pointer hover:bg-red-50 transition-all">
                            <input type="checkbox" name="exclusion" value="{{ opt }}" class="w-6 h-6 accent-red-600">
                            <span class="font-bold text-gray-700">{{ opt }}</span>
                        </label>
                        {% endfor %}
                    </div>
                </div>
                {% endif %}

                <div class="bg-gray-50 rounded-3xl p-6 border mb-10">
                    <h4 class="font-bold text-gray-800 border-b pb-3 mb-3 flex items-center gap-2"><i class="fas fa-info-circle text-{{ settings.theme }}-500"></i> Details</h4>
                    <p class="text-gray-600 whitespace-pre-line text-sm md:text-lg">{{ food.details }}</p>
                </div>

                <div class="bg-blue-50 p-4 rounded-2xl border border-blue-100 text-blue-600 text-sm mb-12 flex items-center gap-3">
                    <i class="fas fa-truck-moving text-xl"></i>
                    <p>ডেলিভারি চার্জ অফিসিয়াল ড্রাইভার সরাসরি বলে দিবে।</p>
                </div>

                <button onclick="sendWA()" class="fixed bottom-4 left-4 right-4 max-w-4xl mx-auto bg-green-500 text-white py-5 rounded-[25px] font-black text-xl shadow-2xl flex items-center justify-center gap-4 hover:bg-green-600 transition-all">
                    <i class="fab fa-whatsapp text-3xl"></i> Order via WhatsApp
                </button>

                <!-- Reviews -->
                <div class="mt-16 border-t pt-10">
                    <h3 class="text-xl font-bold mb-6">Reviews ({{ reviews|length }})</h3>
                    <form action="/review/{{ food._id }}" method="POST" class="bg-gray-50 p-6 rounded-3xl space-y-4 mb-8">
                        <select name="stars" class="w-full border p-4 rounded-2xl outline-none">
                            <option value="5">⭐⭐⭐⭐⭐ Excelent</option>
                            <option value="4">⭐⭐⭐⭐ Good</option>
                            <option value="3">⭐⭐⭐ Average</option>
                        </select>
                        <textarea name="comment" placeholder="Your review..." class="w-full border p-4 rounded-2xl h-24 outline-none" required></textarea>
                        <button class="w-full bg-{{ settings.theme }}-600 text-white py-4 rounded-2xl font-bold">Post Review</button>
                    </form>
                    <div class="space-y-4">
                        {% for r in reviews %}
                        <div class="p-5 bg-white border rounded-2xl shadow-sm italic">
                            <div class="text-yellow-400 mb-1">{% for i in range(r.stars) %}⭐{% endfor %}</div>
                            <p class="text-gray-700">"{{ r.comment }}"</p>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>

        <script>
            let qty = 1;
            function changeQty(val) {
                qty = Math.max(1, qty + val);
                document.getElementById('qty').innerText = qty;
            }
            function sendWA() {
                let addons = Array.from(document.querySelectorAll('input[name="addon"]:checked')).map(e => e.value);
                let exclusions = Array.from(document.querySelectorAll('input[name="exclusion"]:checked')).map(e => e.value);
                
                let text = `*NEW ORDER REQUEST*%0A-----------------------%0A`;
                text += `*Food:* {{ food.name }}%0A`;
                text += `*Quantity:* ${qty}%0A`;
                text += `*Price:* ৳{{ food.price }}%0A`;
                if(addons.length > 0) text += `%0A*Add-ons:* ${addons.join(', ')}`;
                if(exclusions.length > 0) text += `%0A*Without:* ${exclusions.join(', ')}`;
                text += `%0A-----------------------%0A_Delivery charge to be paid to the driver._`;
                
                window.location.href = `https://wa.me/{{ wa_num }}?text=${text}`;
            }
        </script>
    </body>
    </html>
    """, food=food, settings=settings, reviews=reviews, wa_num=wa_num)

@app.route('/review/<id>', methods=['POST'])
def post_review(id):
    reviews_col.insert_one({"food_id": id, "stars": int(request.form.get('stars')), "comment": request.form.get('comment'), "created_at": datetime.datetime.now()})
    return redirect(f'/food/{id}')

# --- ADMIN ROUTES ---

@app.route('/admin/dash')
def admin_dash():
    if not session.get('admin_logged'): return render_template_string("""
        <head>"""+HEAD+"""</head>
        <div class="max-w-md mx-auto mt-20 p-10 bg-white shadow-2xl rounded-[40px] text-center border">
            <h2 class="text-3xl font-black mb-8">Admin Access</h2>
            <form action="/admin/login" method="POST" class="space-y-6">
                <input type="password" name="pass" placeholder="Master Password" class="w-full border-none bg-gray-100 p-5 rounded-2xl text-center outline-none focus:ring-2 focus:ring-black">
                <button class="w-full bg-black text-white py-5 rounded-2xl font-black">Login Panel</button>
            </form>
        </div>
    """)
    
    settings = get_site_settings()
    total_foods = foods_col.count_documents({})
    total_views = views_col.count_documents({})
    today_views = views_col.count_documents({"date": datetime.datetime.now().strftime("%Y-%m-%d")})
    all_foods = list(foods_col.find())
    
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>"""+HEAD+"""<title>Admin Dashboard</title></head>
    <body class="flex flex-col lg:flex-row min-h-screen bg-gray-50">
        <!-- Sidebar -->
        <div class="w-full lg:w-80 bg-gray-900 text-white p-8">
            <div class="flex items-center gap-3 mb-10">
                <img src="{{ settings.logo }}" class="w-10 h-10 rounded-full">
                <h2 class="text-xl font-bold">Control Panel</h2>
            </div>
            <nav class="space-y-3 font-medium">
                <a href="/admin/dash" class="flex items-center gap-3 p-4 bg-{{ settings.theme }}-600 rounded-2xl shadow-xl"><i class="fas fa-th"></i> Dashboard</a>
                <a href="/admin/add-food" class="flex items-center gap-3 p-4 hover:bg-gray-800 rounded-2xl transition-all"><i class="fas fa-plus"></i> Add New Food</a>
                <a href="/admin/manage-options" class="flex items-center gap-3 p-4 hover:bg-gray-800 rounded-2xl transition-all"><i class="fas fa-check-square"></i> Food Options</a>
                <a href="/admin/add-cat" class="flex items-center gap-3 p-4 hover:bg-gray-800 rounded-2xl transition-all"><i class="fas fa-list"></i> Categories</a>
                <a href="/admin/settings" class="flex items-center gap-3 p-4 hover:bg-gray-800 rounded-2xl transition-all"><i class="fas fa-cog"></i> Settings</a>
                <a href="/admin/logout" class="flex items-center gap-3 p-4 text-red-400 mt-10"><i class="fas fa-sign-out-alt"></i> Logout</a>
            </nav>
        </div>

        <!-- Content -->
        <div class="flex-1 p-6 md:p-12 overflow-y-auto">
            <h1 class="text-3xl font-black mb-10">Dashboard Overview</h1>
            <div class="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
                <div class="bg-white p-8 rounded-[40px] shadow-sm border-t-4 border-blue-500">
                    <p class="text-gray-400 text-xs font-bold uppercase">Total Views</p>
                    <h3 class="text-4xl font-black mt-1">{{ total_views }}</h3>
                </div>
                <div class="bg-white p-8 rounded-[40px] shadow-sm border-t-4 border-green-500">
                    <p class="text-gray-400 text-xs font-bold uppercase">Today</p>
                    <h3 class="text-4xl font-black mt-1 text-green-600">{{ today_views }}</h3>
                </div>
                <div class="bg-white p-8 rounded-[40px] shadow-sm border-t-4 border-orange-500">
                    <p class="text-gray-400 text-xs font-bold uppercase">Items</p>
                    <h3 class="text-4xl font-black mt-1 text-orange-500">{{ total_foods }}</h3>
                </div>
            </div>

            <div class="bg-white p-8 rounded-[40px] shadow-sm border">
                <h3 class="text-2xl font-black mb-8">Manage All Food Items</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {% for f in all_foods %}
                    <div class="bg-gray-50 p-4 rounded-3xl border flex items-center gap-4">
                        <img src="{{ f.image }}" class="w-16 h-16 rounded-2xl object-cover">
                        <div class="flex-1">
                            <h4 class="font-bold truncate w-32">{{ f.name }}</h4>
                            <p class="text-sm text-gray-400">৳{{ f.price }}</p>
                        </div>
                        <a href="/admin/del-food/{{ f._id }}" class="text-red-500 p-2"><i class="fas fa-trash-alt"></i></a>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </body>
    </html>
    """, total_foods=total_foods, total_views=total_views, today_views=today_views, all_foods=all_foods, settings=settings)

@app.route('/admin/manage-options', methods=['GET', 'POST'])
def admin_options():
    if not session.get('admin_logged'): return redirect('/admin/dash')
    if request.method == 'POST':
        options_col.insert_one({"name": request.form.get('name'), "type": request.form.get('type')})
    
    all_opts = list(options_col.find())
    return render_template_string("""
    <head>"""+HEAD+"""</head>
    <body class="p-6 md:p-16 bg-gray-50">
        <div class="max-w-4xl mx-auto">
            <!-- Back Button -->
            <a href="/admin/dash" class="inline-block mb-8 bg-gray-200 px-6 py-2 rounded-xl font-bold"><i class="fas fa-arrow-left"></i> Back to Dash</a>
            
            <h2 class="text-3xl font-black mb-8">Manage Food Options (Add-ons / Exclusions)</h2>
            <form method="POST" class="bg-white p-8 rounded-3xl shadow-sm border flex flex-col md:flex-row gap-4 mb-10">
                <input name="name" placeholder="Option Name (e.g. Kullu Shai / No Cheese)" class="flex-1 border p-4 rounded-2xl outline-none" required>
                <select name="type" class="border p-4 rounded-2xl outline-none">
                    <option value="addon">Extras (Add-on)</option>
                    <option value="exclusion">Without (Exclusion)</option>
                </select>
                <button class="bg-black text-white px-8 py-4 rounded-2xl font-bold">Add Option</button>
            </form>

            <div class="grid md:grid-cols-2 gap-8">
                <div class="bg-white p-8 rounded-3xl shadow-sm border">
                    <h3 class="font-bold text-green-600 mb-6">Extras (Add-ons)</h3>
                    {% for o in all_opts if o.type == 'addon' %}
                    <div class="flex justify-between border-b py-3"><span>{{ o.name }}</span> <a href="/admin/del-opt/{{ o._id }}" class="text-red-400"><i class="fas fa-times"></i></a></div>
                    {% endfor %}
                </div>
                <div class="bg-white p-8 rounded-3xl shadow-sm border">
                    <h3 class="font-bold text-red-600 mb-6">Without (Exclusions)</h3>
                    {% for o in all_opts if o.type == 'exclusion' %}
                    <div class="flex justify-between border-b py-3"><span>{{ o.name }}</span> <a href="/admin/del-opt/{{ o._id }}" class="text-red-400"><i class="fas fa-times"></i></a></div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </body>
    """, all_opts=all_opts)

@app.route('/admin/del-opt/<id>')
def del_opt(id):
    if not session.get('admin_logged'): return redirect('/admin/dash')
    options_col.delete_one({"_id": ObjectId(id)})
    return redirect('/admin/manage-options')

@app.route('/admin/add-food', methods=['GET', 'POST'])
def admin_add_food():
    if not session.get('admin_logged'): return redirect('/admin/dash')
    if request.method == 'POST':
        ss_list = [x.strip() for x in request.form.get('screenshots').split(',') if x.strip()]
        foods_col.insert_one({
            "name": request.form.get('name'), "price": request.form.get('price'), "image": request.form.get('image'),
            "category": request.form.get('category'), "details": request.form.get('details'), "screenshots": ss_list,
            "addons": request.form.getlist('addons'), "exclusions": request.form.getlist('exclusions')
        })
        return redirect('/admin/dash')
    
    categories = list(cats_col.find())
    all_options = list(options_col.find())
    return render_template_string("""
    <head>"""+HEAD+"""</head>
    <body class="p-6 md:p-12 bg-gray-50">
        <div class="max-w-4xl mx-auto">
            <!-- Back Button -->
            <a href="/admin/dash" class="inline-block mb-8 bg-gray-200 px-6 py-2 rounded-xl font-bold"><i class="fas fa-arrow-left"></i> Back to Dash</a>

            <h2 class="text-3xl font-black mb-8">Add New Food Item</h2>
            <form method="POST" class="bg-white p-8 md:p-12 rounded-[40px] shadow-sm border space-y-6">
                <div class="grid md:grid-cols-2 gap-6">
                    <input name="name" placeholder="Food Name" class="w-full border p-5 rounded-2xl outline-none" required>
                    <input name="price" placeholder="Price" class="w-full border p-5 rounded-2xl outline-none" required>
                </div>
                <input name="image" placeholder="Main Image URL" class="w-full border p-5 rounded-2xl outline-none" required>
                <select name="category" class="w-full border p-5 rounded-2xl outline-none">
                    {% for c in categories %} <option value="{{ c.name }}">{{ c.name }}</option> {% endfor %}
                </select>
                <textarea name="screenshots" placeholder="Screenshots URLs (comma separated)" class="w-full border p-5 rounded-2xl h-24 outline-none"></textarea>
                
                <div class="grid md:grid-cols-2 gap-8 border-t pt-8">
                    <div>
                        <h4 class="font-bold text-green-600 mb-4 uppercase text-xs">Extras (Add-ons)</h4>
                        <div class="max-h-48 overflow-y-auto border p-5 rounded-2xl space-y-3">
                            {% for o in all_options if o.type == 'addon' %}
                            <label class="flex items-center gap-3"><input type="checkbox" name="addons" value="{{ o.name }}" class="w-5 h-5"> <span>{{ o.name }}</span></label>
                            {% endfor %}
                        </div>
                    </div>
                    <div>
                        <h4 class="font-bold text-red-600 mb-4 uppercase text-xs">Without (Exclusions)</h4>
                        <div class="max-h-48 overflow-y-auto border p-5 rounded-2xl space-y-3">
                            {% for o in all_options if o.type == 'exclusion' %}
                            <label class="flex items-center gap-3"><input type="checkbox" name="exclusions" value="{{ o.name }}" class="w-5 h-5"> <span>{{ o.name }}</span></label>
                            {% endfor %}
                        </div>
                    </div>
                </div>

                <textarea name="details" placeholder="Full Food Details..." class="w-full border p-5 rounded-2xl h-40 outline-none" required></textarea>
                <button class="w-full bg-black text-white py-6 rounded-3xl font-black text-xl shadow-xl">Publish Food Item</button>
            </form>
        </div>
    </body>
    """, categories=categories, all_options=all_options)

@app.route('/admin/add-cat', methods=['GET', 'POST'])
def admin_add_cat():
    if not session.get('admin_logged'): return redirect('/admin/dash')
    if request.method == 'POST':
        cats_col.insert_one({"name": request.form.get('name'), "logo": request.form.get('logo')})
    
    categories = list(cats_col.find())
    return render_template_string("""
    <head>"""+HEAD+"""</head>
    <body class="p-6 md:p-16 bg-gray-100">
        <div class="max-w-6xl mx-auto">
            <!-- Back Button -->
            <a href="/admin/dash" class="inline-block mb-8 bg-gray-200 px-6 py-2 rounded-xl font-bold"><i class="fas fa-arrow-left"></i> Back to Dash</a>

            <div class="grid md:grid-cols-2 gap-10">
                <form method="POST" class="bg-white p-8 rounded-[35px] shadow-sm border h-fit">
                    <h3 class="text-2xl font-black mb-8">Create Category</h3>
                    <input name="name" placeholder="Category Name" class="w-full border p-4 rounded-2xl mb-4 outline-none" required>
                    <input name="logo" placeholder="Logo Icon URL" class="w-full border p-4 rounded-2xl mb-6 outline-none" required>
                    <button class="w-full bg-gray-900 text-white py-4 rounded-2xl font-black">Add Now</button>
                </form>
                <div class="bg-white p-8 rounded-[35px] shadow-sm border">
                    <h3 class="text-2xl font-black mb-8">Existing Categories</h3>
                    <div class="space-y-4">
                        {% for cat in categories %}
                        <div class="flex justify-between items-center p-4 bg-gray-50 rounded-2xl border">
                            <div class="flex items-center gap-4">
                                <img src="{{ cat.logo }}" class="w-12 h-12 rounded-full object-cover">
                                <span class="font-bold">{{ cat.name }}</span>
                            </div>
                            <a href="/admin/del-cat/{{ cat._id }}" class="text-red-500"><i class="fas fa-trash-alt"></i></a>
                        </div>
                        {% endfor %}
                    </div>
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

@app.route('/admin/del-food/<id>')
def del_food(id):
    if not session.get('admin_logged'): return redirect('/admin/dash')
    foods_col.delete_one({"_id": ObjectId(id)})
    return redirect('/admin/dash')

@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    if not session.get('admin_logged'): return redirect('/admin/dash')
    settings = get_site_settings()
    if request.method == 'POST':
        updated = {
            "name": request.form.get('name'), "logo": request.form.get('logo'), "whatsapp": request.form.get('whatsapp'),
            "fb": request.form.get('fb'), "pass": request.form.get('pass'), "dmca": request.form.get('dmca'),
            "copyright": request.form.get('copyright'), "footer_text": request.form.get('footer_text'),
            "theme": request.form.get('theme'), "privacy": request.form.get('privacy'), "header_text": request.form.get('header_text')
        }
        settings_col.update_one({"id": "config"}, {"$set": updated})
        return redirect('/admin/dash')

    return render_template_string("""
    <head>"""+HEAD+"""</head>
    <body class="p-6 md:p-16 bg-gray-50">
        <div class="max-w-5xl mx-auto">
            <!-- Back Button -->
            <a href="/admin/dash" class="inline-block mb-8 bg-gray-200 px-6 py-2 rounded-xl font-bold"><i class="fas fa-arrow-left"></i> Back to Dash</a>

            <form method="POST" class="bg-white p-10 md:p-16 rounded-[60px] shadow-sm grid grid-cols-1 md:grid-cols-2 gap-8 border">
                <h2 class="col-span-full text-4xl font-black mb-4">Site Customization</h2>
                <div class="space-y-1"><label class="text-xs font-bold text-gray-400 px-2 uppercase tracking-widest">Brand Name</label><input name="name" value="{{ s.name }}" class="w-full border p-5 rounded-2xl outline-none"></div>
                <div class="space-y-1"><label class="text-xs font-bold text-gray-400 px-2 uppercase tracking-widest">Brand Logo</label><input name="logo" value="{{ s.logo }}" class="w-full border p-5 rounded-2xl outline-none"></div>
                <div class="space-y-1"><label class="text-xs font-bold text-gray-400 px-2 uppercase tracking-widest">WhatsApp</label><input name="whatsapp" value="{{ s.whatsapp }}" class="w-full border p-5 rounded-2xl outline-none"></div>
                <div class="space-y-1"><label class="text-xs font-bold text-gray-400 px-2 uppercase tracking-widest">Master Key</label><input name="pass" value="{{ s.pass }}" class="w-full border p-5 rounded-2xl outline-none"></div>
                
                <div class="col-span-full space-y-1"><label class="text-xs font-bold text-gray-400 px-2 uppercase tracking-widest">Hero Header Text</label><input name="header_text" value="{{ s.header_text }}" class="w-full border p-5 rounded-2xl outline-none"></div>
                <div class="col-span-full space-y-1"><label class="text-xs font-bold text-gray-400 px-2 uppercase tracking-widest">Privacy Policy Content</label><textarea name="privacy" class="w-full border p-5 rounded-[30px] h-40 outline-none">{{ s.privacy }}</textarea></div>
                
                <button class="col-span-full bg-black text-white py-6 rounded-[30px] font-black text-2xl shadow-2xl">Apply Global Changes</button>
            </form>
        </div>
    </body>
    """, s=settings)

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

if __name__ == '__main__':
    app.run(debug=True)
