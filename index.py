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
    .category-card { transition: 0.3s; }
    .category-card:hover { transform: translateY(-5px); }
    .food-card img { height: 160px; object-fit: cover; width: 100%; border-radius: 12px; }
    @media (min-width: 768px) { .food-card img { height: 240px; } }
    .glass { background: rgba(255, 255, 255, 0.9); backdrop-filter: blur(10px); }
</style>
"""

# --- USER ROUTES ---

@app.route('/')
def home():
    track_view()
    settings = get_site_settings()
    categories = list(cats_col.find())
    wa_clean = settings['whatsapp'].replace('+', '').replace(' ', '').replace('-', '')
    
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="bn">
    <head>"""+HEAD+"""<title>{{ settings.name }}</title></head>
    <body class="max-w-screen-2xl mx-auto">
        <nav class="glass sticky top-0 z-50 px-4 py-3 flex justify-between items-center border-b">
            <div class="flex items-center gap-3">
                <img src="{{ settings.logo }}" class="w-10 h-10 md:w-14 md:h-14 rounded-full ring-2 ring-{{ settings.theme }}-500">
                <h1 class="text-xl md:text-3xl font-bold text-{{ settings.theme }}-600">{{ settings.name }}</h1>
            </div>
            <a href="https://wa.me/{{ wa_clean }}" class="text-green-500 text-2xl md:text-3xl"><i class="fab fa-whatsapp"></i></a>
        </nav>

        <!-- Search Bar -->
        <div class="p-4 md:px-8">
            <div class="relative max-w-2xl mx-auto mt-4">
                <input type="text" id="catSearch" onkeyup="searchCat()" placeholder="খুঁজুন আপনার পছন্দের খাবার ক্যাটাগরি..." class="w-full p-4 pl-12 rounded-2xl border-none shadow-md outline-none focus:ring-2 focus:ring-{{ settings.theme }}-500">
                <i class="fas fa-search absolute left-4 top-5 text-gray-400"></i>
            </div>
        </div>

        <!-- Banner -->
        <div class="p-4">
            <div class="bg-{{ settings.theme }}-600 rounded-[30px] p-8 md:p-16 text-white shadow-lg relative overflow-hidden text-center">
                <h2 class="text-2xl md:text-5xl font-black relative z-10 leading-tight">{{ settings.header_text }}</h2>
                <i class="fas fa-pizza-slice absolute -right-6 -bottom-6 text-8xl md:text-[200px] opacity-10 rotate-12"></i>
            </div>
        </div>

        <!-- Categories Only - Food Hidden -->
        <div class="p-4 md:p-8">
            <h2 class="text-xl md:text-3xl font-bold mb-8 flex items-center gap-2">
                <span class="w-2 h-8 bg-{{ settings.theme }}-600 rounded-full"></span> সকল ক্যাটাগরি
            </h2>
            <div id="catGrid" class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 md:gap-8">
                {% for cat in categories %}
                <a href="/category/{{ cat.name }}" class="cat-item category-card bg-white p-4 rounded-[30px] shadow-sm border text-center flex flex-col items-center">
                    <div class="w-24 h-24 md:w-40 md:h-40 rounded-full border-4 border-gray-100 overflow-hidden mb-4">
                        <img src="{{ cat.logo }}" class="w-full h-full object-cover">
                    </div>
                    <h3 class="font-bold text-lg md:text-2xl text-gray-800">{{ cat.name }}</h3>
                    <span class="text-xs text-gray-400 mt-1">খাবারগুলো দেখতে ক্লিক করুন</span>
                </a>
                {% endfor %}
            </div>
        </div>

        <footer class="bg-white border-t mt-12 p-10 text-center">
            <p class="text-gray-400 text-sm">{{ settings.footer_text }}</p>
            <div class="flex justify-center gap-6 my-6 text-2xl">
                <a href="{{ settings.fb }}" class="text-blue-600"><i class="fab fa-facebook"></i></a>
                <a href="https://wa.me/{{ wa_clean }}" class="text-green-500"><i class="fab fa-whatsapp"></i></a>
            </div>
            <p class="text-[10px] text-gray-300 uppercase tracking-widest">{{ settings.dmca }} | {{ settings.copyright }}</p>
        </footer>

        <script>
            function searchCat() {
                let input = document.getElementById('catSearch').value.toLowerCase();
                let items = document.getElementsByClassName('cat-item');
                for (let i = 0; i < items.length; i++) {
                    items[i].style.display = items[i].innerText.toLowerCase().includes(input) ? "flex" : "none";
                }
            }
        </script>
    </body>
    </html>
    """, settings=settings, categories=categories, wa_clean=wa_clean)

@app.route('/category/<name>')
def category_foods(name):
    settings = get_site_settings()
    foods = list(foods_col.find({"category": name}))
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>"""+HEAD+"""<title>{{ name }} - Items</title></head>
    <body class="bg-gray-50 pb-10">
        <nav class="glass sticky top-0 z-50 px-4 py-3 flex items-center gap-4 border-b">
            <a href="/" class="bg-gray-100 w-10 h-10 flex items-center justify-center rounded-full"><i class="fas fa-arrow-left"></i></a>
            <h1 class="text-xl font-bold">{{ name }} আইটেমসমূহ</h1>
        </nav>

        <div class="p-4 md:p-8 grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4 md:gap-8">
            {% for food in foods %}
            <a href="/food/{{ food._id }}" class="bg-white rounded-2xl p-3 md:p-5 shadow-sm hover:shadow-xl transition-all border animate__animated animate__fadeIn">
                <img src="{{ food.image }}" class="rounded-xl object-cover w-full h-40 md:h-56">
                <h4 class="text-sm md:text-xl font-bold mt-4 text-gray-800 truncate">{{ food.name }}</h4>
                <div class="flex justify-between items-center mt-2">
                    <span class="text-{{ settings.theme }}-600 font-black md:text-xl">৳{{ food.price }}</span>
                    <i class="fas fa-plus-circle text-gray-200"></i>
                </div>
            </a>
            {% endfor %}
        </div>
    </body>
    </html>
    """, name=name, foods=foods, settings=settings)

@app.route('/food/<id>')
def food_details(id):
    settings = get_site_settings()
    food = foods_col.find_one({"_id": ObjectId(id)})
    wa_num = settings['whatsapp'].replace('+', '').replace(' ', '').replace('-', '')
    
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>"""+HEAD+"""<title>{{ food.name }}</title></head>
    <body class="bg-gray-50 pb-24">
        <div class="max-w-4xl mx-auto bg-white min-h-screen shadow-lg relative">
            <!-- Back to Category -->
            <a href="/category/{{ food.category }}" class="absolute top-4 left-4 z-50 bg-white/80 p-3 rounded-2xl shadow-xl border">
                <i class="fas fa-chevron-left"></i> Back
            </a>

            <div class="h-64 md:h-[500px]">
                <img src="{{ food.image }}" class="w-full h-full object-cover">
            </div>
            
            <div class="p-6 md:p-12 -mt-10 bg-white rounded-t-[40px] relative z-10">
                <h1 class="text-3xl md:text-6xl font-black text-gray-900 leading-tight">{{ food.name }}</h1>
                <p class="text-3xl md:text-4xl font-black text-{{ settings.theme }}-600 mt-4">৳{{ food.price }}</p>

                <div class="grid grid-cols-4 md:grid-cols-6 gap-3 my-8">
                    {% for ss in food.screenshots %}
                    <img src="{{ ss }}" class="w-full aspect-square rounded-xl object-cover border">
                    {% endfor %}
                </div>

                <!-- Quantity -->
                <div class="bg-gray-50 p-6 rounded-[30px] border flex items-center justify-between mb-8">
                    <span class="font-bold text-lg">Quantity</span>
                    <div class="flex items-center gap-6">
                        <button onclick="changeQty(-1)" class="w-12 h-12 bg-white rounded-2xl shadow-sm border flex items-center justify-center"><i class="fas fa-minus"></i></button>
                        <span id="qty" class="text-2xl font-black">1</span>
                        <button onclick="changeQty(1)" class="w-12 h-12 bg-{{ settings.theme }}-600 text-white rounded-2xl shadow-lg flex items-center justify-center"><i class="fas fa-plus"></i></button>
                    </div>
                </div>

                <!-- Custom Options -->
                {% if food.addons %}
                <div class="mb-8">
                    <h4 class="font-bold text-lg mb-4 text-green-600">Extras / কুল্লু সাই (Add-ons)</h4>
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

                {% if food.exclusions %}
                <div class="mb-8">
                    <h4 class="font-bold text-lg mb-4 text-red-600">Without / ছাড়া (Exclusions)</h4>
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
                    <h4 class="font-bold text-gray-800 border-b pb-3 mb-3">Details</h4>
                    <p class="text-gray-600 whitespace-pre-line leading-relaxed">{{ food.details }}</p>
                </div>

                <div class="bg-blue-50 p-4 rounded-2xl border text-blue-600 text-sm mb-12">
                    <i class="fas fa-truck"></i> ডেলিভারি চার্জ ড্রাইভার বলে দিবে।
                </div>

                <button onclick="sendWA()" class="fixed bottom-4 left-4 right-4 max-w-4xl mx-auto bg-green-500 text-white py-5 rounded-[25px] font-black text-xl shadow-2xl flex items-center justify-center gap-4">
                    <i class="fab fa-whatsapp text-3xl"></i> Order via WhatsApp
                </button>
            </div>
        </div>

        <script>
            let qty = 1;
            function changeQty(val) { qty = Math.max(1, qty + val); document.getElementById('qty').innerText = qty; }
            function sendWA() {
                let addons = Array.from(document.querySelectorAll('input[name="addon"]:checked')).map(e => e.value);
                let exclusions = Array.from(document.querySelectorAll('input[name="exclusion"]:checked')).map(e => e.value);
                let text = `*NEW ORDER*%0A*Item:* {{ food.name }}%0A*Qty:* ${qty}%0A*Price:* ৳{{ food.price }}%0A`;
                if(addons.length) text += `*Extras:* ${addons.join(', ')}%0A`;
                if(exclusions.length) text += `*Without:* ${exclusions.join(', ')}%0A`;
                text += `%0A_Delivery charge will be updated by driver._`;
                window.location.href = `https://wa.me/{{ wa_num }}?text=${text}`;
            }
        </script>
    </body>
    </html>
    """, food=food, settings=settings, wa_num=wa_num)

# --- ADMIN ROUTES ---

@app.route('/admin/dash')
def admin_dash():
    if not session.get('admin_logged'): return render_template_string("""
        <head>"""+HEAD+"""</head>
        <div class="max-w-md mx-auto mt-20 p-10 bg-white shadow-2xl rounded-[40px] text-center border">
            <h2 class="text-3xl font-black mb-8">Admin Access</h2>
            <form action="/admin/login" method="POST" class="space-y-6">
                <input type="password" name="pass" placeholder="Password" class="w-full bg-gray-100 p-5 rounded-2xl text-center outline-none">
                <button class="w-full bg-black text-white py-5 rounded-2xl font-black">Login</button>
            </form>
        </div>
    """)
    settings = get_site_settings()
    total_views = views_col.count_documents({})
    total_foods = foods_col.count_documents({})
    total_cats = cats_col.count_documents({})
    
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>"""+HEAD+"""<title>Admin Dashboard</title></head>
    <body class="flex flex-col lg:flex-row min-h-screen bg-gray-50">
        <div class="w-full lg:w-80 bg-gray-900 text-white p-8">
            <h2 class="text-2xl font-bold mb-10">Admin Panel</h2>
            <nav class="space-y-3 font-medium">
                <a href="/admin/dash" class="block p-4 bg-orange-600 rounded-2xl shadow-xl">Dashboard</a>
                <a href="/admin/manage-foods" class="block p-4 hover:bg-gray-800 rounded-2xl">Manage Foods</a>
                <a href="/admin/add-food" class="block p-4 hover:bg-gray-800 rounded-2xl">Add Food</a>
                <a href="/admin/add-cat" class="block p-4 hover:bg-gray-800 rounded-2xl">Categories</a>
                <a href="/admin/manage-options" class="block p-4 hover:bg-gray-800 rounded-2xl">Options (Add-ons)</a>
                <a href="/admin/settings" class="block p-4 hover:bg-gray-800 rounded-2xl">Settings</a>
                <a href="/admin/logout" class="block p-4 text-red-400 mt-10">Logout</a>
            </nav>
        </div>

        <div class="flex-1 p-6 md:p-12">
            <h2 class="text-3xl font-black mb-10">পরিসংখ্যান (Statistics)</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
                <div class="bg-white p-8 rounded-[30px] border shadow-sm">
                    <p class="text-gray-400 font-bold uppercase text-xs tracking-widest">Total Views</p>
                    <h3 class="text-5xl font-black mt-2">{{ total_views }}</h3>
                </div>
                <div class="bg-white p-8 rounded-[30px] border shadow-sm">
                    <p class="text-gray-400 font-bold uppercase text-xs tracking-widest">Total Foods</p>
                    <h3 class="text-5xl font-black mt-2 text-orange-500">{{ total_foods }}</h3>
                </div>
                <div class="bg-white p-8 rounded-[30px] border shadow-sm">
                    <p class="text-gray-400 font-bold uppercase text-xs tracking-widest">Total Categories</p>
                    <h3 class="text-5xl font-black mt-2 text-blue-500">{{ total_cats }}</h3>
                </div>
            </div>
        </div>
    </body>
    </html>
    """, total_views=total_views, total_foods=total_foods, total_cats=total_cats, settings=settings)

@app.route('/admin/manage-foods')
def admin_manage_foods():
    if not session.get('admin_logged'): return redirect('/admin/dash')
    settings = get_site_settings()
    all_foods = list(foods_col.find())
    categories = list(cats_col.find())
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>"""+HEAD+"""<title>Manage Foods</title></head>
    <body class="bg-gray-50 p-6 md:p-12">
        <div class="max-w-6xl mx-auto">
            <div class="flex justify-between items-center mb-8">
                <h2 class="text-3xl font-black">খাবার তালিকা ব্যবস্থাপনা</h2>
                <a href="/admin/dash" class="bg-gray-200 px-6 py-2 rounded-xl font-bold"><i class="fas fa-arrow-left"></i> Back</a>
            </div>

            <!-- Search & Filter -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
                <div class="relative">
                    <input type="text" id="foodSearch" onkeyup="filterFoods()" placeholder="খাবারের নাম লিখে সার্চ দিন..." class="w-full p-4 pl-12 rounded-2xl border shadow-sm outline-none">
                    <i class="fas fa-search absolute left-4 top-5 text-gray-400"></i>
                </div>
                <select id="catFilter" onchange="filterFoods()" class="p-4 rounded-2xl border shadow-sm outline-none">
                    <option value="">সকল ক্যাটাগরি</option>
                    {% for c in categories %} <option value="{{ c.name }}">{{ c.name }}</option> {% endfor %}
                </select>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" id="foodGrid">
                {% for f in foods %}
                <div class="food-item bg-white p-4 rounded-3xl border shadow-sm" data-name="{{ f.name | lower }}" data-cat="{{ f.category }}">
                    <img src="{{ f.image }}" class="w-full h-40 object-cover rounded-2xl mb-4">
                    <h4 class="font-bold text-lg mb-1">{{ f.name }}</h4>
                    <p class="text-orange-600 font-bold mb-4">৳{{ f.price }} | {{ f.category }}</p>
                    <div class="flex gap-2">
                        <a href="/admin/edit-food/{{ f._id }}" class="flex-1 bg-blue-100 text-blue-600 py-3 rounded-xl text-center font-bold hover:bg-blue-600 hover:text-white transition-all"><i class="fas fa-edit"></i> Edit</a>
                        <a href="/admin/del-food/{{ f._id }}" onclick="return confirm('নিশ্চিত তো?')" class="w-12 bg-red-100 text-red-600 flex items-center justify-center rounded-xl hover:bg-red-600 hover:text-white transition-all"><i class="fas fa-trash"></i></a>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>

        <script>
            function filterFoods() {
                let search = document.getElementById('foodSearch').value.toLowerCase();
                let cat = document.getElementById('catFilter').value;
                let items = document.getElementsByClassName('food-item');
                
                for (let item of items) {
                    let nameMatch = item.getAttribute('data-name').includes(search);
                    let catMatch = cat === "" || item.getAttribute('data-cat') === cat;
                    item.style.display = (nameMatch && catMatch) ? "block" : "none";
                }
            }
        </script>
    </body>
    </html>
    """, foods=all_foods, categories=categories, settings=settings)

@app.route('/admin/manage-options', methods=['GET', 'POST'])
def admin_options():
    if not session.get('admin_logged'): return redirect('/admin/dash')
    if request.method == 'POST':
        options_col.insert_one({"name": request.form.get('name'), "type": request.form.get('type')})
    
    all_opts = list(options_col.find())
    return render_template_string("""
    <head>"""+HEAD+"""</head>
    <body class="p-8 bg-gray-50">
        <a href="/admin/dash" class="inline-block mb-6 bg-gray-200 px-6 py-2 rounded-xl font-bold"><i class="fas fa-arrow-left"></i> Back to Dash</a>
        <div class="max-w-4xl mx-auto">
            <h2 class="text-3xl font-black mb-8">মেইন অপশনসমূহ (Extras / Without)</h2>
            <form method="POST" class="bg-white p-6 rounded-3xl shadow-sm border flex gap-4 mb-10">
                <input name="name" placeholder="Option Name" class="flex-1 border p-4 rounded-xl outline-none" required>
                <select name="type" class="border p-4 rounded-xl">
                    <option value="addon">Add-on (Extras)</option>
                    <option value="exclusion">Exclusion (Without)</option>
                </select>
                <button class="bg-black text-white px-8 rounded-xl font-bold">Add</button>
            </form>
            <div class="grid md:grid-cols-2 gap-8">
                <div class="bg-white p-8 rounded-3xl border">
                    <h3 class="font-bold text-green-600 mb-4">Extras List</h3>
                    {% for o in all_opts if o.type == 'addon' %}
                    <div class="flex justify-between items-center py-2 border-b">
                        <span>{{ o.name }}</span> 
                        <div class="flex gap-3">
                            <a href="/admin/edit-opt/{{ o._id }}" class="text-blue-500"><i class="fas fa-edit"></i></a>
                            <a href="/admin/del-opt/{{ o._id }}" class="text-red-400"><i class="fas fa-times"></i></a>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                <div class="bg-white p-8 rounded-3xl border">
                    <h3 class="font-bold text-red-600 mb-4">Without List</h3>
                    {% for o in all_opts if o.type == 'exclusion' %}
                    <div class="flex justify-between items-center py-2 border-b">
                        <span>{{ o.name }}</span> 
                        <div class="flex gap-3">
                            <a href="/admin/edit-opt/{{ o._id }}" class="text-blue-500"><i class="fas fa-edit"></i></a>
                            <a href="/admin/del-opt/{{ o._id }}" class="text-red-400"><i class="fas fa-times"></i></a>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </body>
    """, all_opts=all_opts)

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
        return redirect('/admin/manage-foods')
    
    categories = list(cats_col.find())
    all_options = list(options_col.find())
    return render_template_string("""
    <head>"""+HEAD+"""</head>
    <body class="p-8 bg-gray-50">
        <a href="/admin/dash" class="inline-block mb-6 bg-gray-200 px-6 py-2 rounded-xl font-bold"><i class="fas fa-arrow-left"></i> Back to Dash</a>
        <form method="POST" class="max-w-4xl mx-auto bg-white p-10 rounded-[40px] shadow-sm border space-y-6">
            <h2 class="text-3xl font-black mb-4">নতুন খাবার যুক্ত করুন</h2>
            <div class="grid md:grid-cols-2 gap-6">
                <input name="name" placeholder="Name" class="w-full border p-4 rounded-2xl outline-none" required>
                <input name="price" placeholder="Price" class="w-full border p-4 rounded-2xl outline-none" required>
            </div>
            <input name="image" placeholder="Main Image URL" class="w-full border p-4 rounded-2xl outline-none" required>
            <select name="category" class="w-full border p-4 rounded-2xl">
                {% for c in categories %} <option value="{{ c.name }}">{{ c.name }}</option> {% endfor %}
            </select>
            <textarea name="screenshots" placeholder="Screenshots URLs (comma separated)" class="w-full border p-4 rounded-2xl outline-none"></textarea>
            
            <div class="grid md:grid-cols-2 gap-8 border-t pt-6">
                <div>
                    <h4 class="font-bold text-green-600 mb-4">Extra Options</h4>
                    <div class="max-h-48 overflow-y-auto border p-4 rounded-2xl">
                        {% for o in all_options if o.type == 'addon' %}
                        <label class="flex items-center gap-2 mb-2"><input type="checkbox" name="addons" value="{{ o.name }}"> {{ o.name }}</label>
                        {% endfor %}
                    </div>
                </div>
                <div>
                    <h4 class="font-bold text-red-600 mb-4">Without Options</h4>
                    <div class="max-h-48 overflow-y-auto border p-4 rounded-2xl">
                        {% for o in all_options if o.type == 'exclusion' %}
                        <label class="flex items-center gap-2 mb-2"><input type="checkbox" name="exclusions" value="{{ o.name }}"> {{ o.name }}</label>
                        {% endfor %}
                    </div>
                </div>
            </div>
            <textarea name="details" placeholder="Food details..." class="w-full border p-4 rounded-2xl h-32 outline-none" required></textarea>
            <button class="w-full bg-black text-white py-6 rounded-3xl font-black text-xl">Publish Food</button>
        </form>
    </body>
    """, categories=categories, all_options=all_options)

@app.route('/admin/edit-food/<id>', methods=['GET', 'POST'])
def admin_edit_food(id):
    if not session.get('admin_logged'): return redirect('/admin/dash')
    food = foods_col.find_one({"_id": ObjectId(id)})
    if request.method == 'POST':
        ss_list = [x.strip() for x in request.form.get('screenshots').split(',') if x.strip()]
        foods_col.update_one({"_id": ObjectId(id)}, {"$set": {
            "name": request.form.get('name'), "price": request.form.get('price'), "image": request.form.get('image'),
            "category": request.form.get('category'), "details": request.form.get('details'), "screenshots": ss_list,
            "addons": request.form.getlist('addons'), "exclusions": request.form.getlist('exclusions')
        }})
        return redirect('/admin/manage-foods')
    
    categories = list(cats_col.find())
    all_options = list(options_col.find())
    return render_template_string("""
    <head>"""+HEAD+"""</head>
    <body class="p-8 bg-gray-50">
        <a href="/admin/manage-foods" class="inline-block mb-6 bg-gray-200 px-6 py-2 rounded-xl font-bold"><i class="fas fa-arrow-left"></i> Back to List</a>
        <form method="POST" class="max-w-4xl mx-auto bg-white p-10 rounded-[40px] shadow-sm border space-y-6">
            <h2 class="text-3xl font-black mb-4">খাবার ইডিট করুন</h2>
            <div class="grid md:grid-cols-2 gap-6">
                <input name="name" value="{{ f.name }}" placeholder="Name" class="w-full border p-4 rounded-2xl outline-none" required>
                <input name="price" value="{{ f.price }}" placeholder="Price" class="w-full border p-4 rounded-2xl outline-none" required>
            </div>
            <input name="image" value="{{ f.image }}" placeholder="Main Image URL" class="w-full border p-4 rounded-2xl outline-none" required>
            <select name="category" class="w-full border p-4 rounded-2xl">
                {% for c in categories %} <option value="{{ c.name }}" {% if c.name == f.category %}selected{% endif %}>{{ c.name }}</option> {% endfor %}
            </select>
            <textarea name="screenshots" placeholder="Screenshots URLs" class="w-full border p-4 rounded-2xl outline-none">{{ f.screenshots | join(',') }}</textarea>
            
            <div class="grid md:grid-cols-2 gap-8 border-t pt-6">
                <div>
                    <h4 class="font-bold text-green-600 mb-4">Extra Options</h4>
                    <div class="max-h-48 overflow-y-auto border p-4 rounded-2xl">
                        {% for o in all_options if o.type == 'addon' %}
                        <label class="flex items-center gap-2 mb-2"><input type="checkbox" name="addons" value="{{ o.name }}" {% if o.name in f.addons %}checked{% endif %}> {{ o.name }}</label>
                        {% endfor %}
                    </div>
                </div>
                <div>
                    <h4 class="font-bold text-red-600 mb-4">Without Options</h4>
                    <div class="max-h-48 overflow-y-auto border p-4 rounded-2xl">
                        {% for o in all_options if o.type == 'exclusion' %}
                        <label class="flex items-center gap-2 mb-2"><input type="checkbox" name="exclusions" value="{{ o.name }}" {% if o.name in f.exclusions %}checked{% endif %}> {{ o.name }}</label>
                        {% endfor %}
                    </div>
                </div>
            </div>
            <textarea name="details" class="w-full border p-4 rounded-2xl h-32 outline-none" required>{{ f.details }}</textarea>
            <button class="w-full bg-blue-600 text-white py-6 rounded-3xl font-black text-xl">Update Food</button>
        </form>
    </body>
    """, f=food, categories=categories, all_options=all_options)

@app.route('/admin/add-cat', methods=['GET', 'POST'])
def admin_add_cat():
    if not session.get('admin_logged'): return redirect('/admin/dash')
    if request.method == 'POST':
        cats_col.insert_one({"name": request.form.get('name'), "logo": request.form.get('logo')})
    categories = list(cats_col.find())
    return render_template_string("""
    <head>"""+HEAD+"""</head>
    <body class="p-8 bg-gray-50">
        <a href="/admin/dash" class="inline-block mb-6 bg-gray-200 px-6 py-2 rounded-xl font-bold"><i class="fas fa-arrow-left"></i> Back to Dash</a>
        <div class="max-w-4xl mx-auto grid md:grid-cols-2 gap-10">
            <form method="POST" class="bg-white p-8 rounded-3xl shadow-sm border">
                <h3 class="text-2xl font-black mb-6">Create Cat</h3>
                <input name="name" placeholder="Name" class="w-full border p-4 rounded-2xl mb-4" required>
                <input name="logo" placeholder="Logo URL" class="w-full border p-4 rounded-2xl mb-6" required>
                <button class="w-full bg-black text-white py-4 rounded-2xl font-bold">Save</button>
            </form>
            <div class="bg-white p-8 rounded-3xl shadow-sm border">
                <h3 class="text-2xl font-black mb-6">Existing Cats</h3>
                {% for c in categories %}
                <div class="flex justify-between items-center py-3 border-b">
                    <span>{{ c.name }}</span> 
                    <div class="flex gap-3">
                        <a href="/admin/edit-cat/{{ c._id }}" class="text-blue-500"><i class="fas fa-edit"></i></a>
                        <a href="/admin/del-cat/{{ c._id }}" class="text-red-500"><i class="fas fa-trash"></i></a>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </body>
    """, categories=categories)

@app.route('/admin/edit-cat/<id>', methods=['GET', 'POST'])
def admin_edit_cat(id):
    if not session.get('admin_logged'): return redirect('/admin/dash')
    cat = cats_col.find_one({"_id": ObjectId(id)})
    if request.method == 'POST':
        cats_col.update_one({"_id": ObjectId(id)}, {"$set": {"name": request.form.get('name'), "logo": request.form.get('logo')}})
        return redirect('/admin/add-cat')
    return render_template_string("""
    <head>"""+HEAD+"""</head>
    <body class="p-8 bg-gray-50">
        <form method="POST" class="max-w-md mx-auto bg-white p-8 rounded-3xl shadow-sm border">
            <h3 class="text-2xl font-black mb-6">ক্যাটাগরি ইডিট করুন</h3>
            <input name="name" value="{{ c.name }}" class="w-full border p-4 rounded-2xl mb-4" required>
            <input name="logo" value="{{ c.logo }}" class="w-full border p-4 rounded-2xl mb-6" required>
            <button class="w-full bg-blue-600 text-white py-4 rounded-2xl font-bold">Update</button>
        </form>
    </body>
    """, c=cat)

@app.route('/admin/edit-opt/<id>', methods=['GET', 'POST'])
def admin_edit_opt(id):
    if not session.get('admin_logged'): return redirect('/admin/dash')
    opt = options_col.find_one({"_id": ObjectId(id)})
    if request.method == 'POST':
        options_col.update_one({"_id": ObjectId(id)}, {"$set": {"name": request.form.get('name'), "type": request.form.get('type')}})
        return redirect('/admin/manage-options')
    return render_template_string("""
    <head>"""+HEAD+"""</head>
    <body class="p-8 bg-gray-50">
        <form method="POST" class="max-w-md mx-auto bg-white p-8 rounded-3xl shadow-sm border">
            <h3 class="text-2xl font-black mb-6">অপশন ইডিট করুন</h3>
            <input name="name" value="{{ o.name }}" class="w-full border p-4 rounded-2xl mb-4" required>
            <select name="type" class="w-full border p-4 rounded-2xl mb-6">
                <option value="addon" {% if o.type == 'addon' %}selected{% endif %}>Add-on (Extras)</option>
                <option value="exclusion" {% if o.type == 'exclusion' %}selected{% endif %}>Exclusion (Without)</option>
            </select>
            <button class="w-full bg-blue-600 text-white py-4 rounded-2xl font-bold">Update</button>
        </form>
    </body>
    """, o=opt)

@app.route('/admin/del-cat/<id>')
def del_cat(id):
    if not session.get('admin_logged'): return redirect('/admin/dash')
    cats_col.delete_one({"_id": ObjectId(id)})
    return redirect('/admin/add-cat')

@app.route('/admin/del-food/<id>')
def del_food(id):
    if not session.get('admin_logged'): return redirect('/admin/dash')
    foods_col.delete_one({"_id": ObjectId(id)})
    return redirect('/admin/manage-foods')

@app.route('/admin/del-opt/<id>')
def del_opt(id):
    if not session.get('admin_logged'): return redirect('/admin/dash')
    options_col.delete_one({"_id": ObjectId(id)})
    return redirect('/admin/manage-options')

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
    <body class="p-8 bg-gray-50">
        <a href="/admin/dash" class="inline-block mb-6 bg-gray-200 px-6 py-2 rounded-xl font-bold"><i class="fas fa-arrow-left"></i> Back to Dash</a>
        <form method="POST" class="max-w-4xl mx-auto bg-white p-10 rounded-[60px] shadow-sm grid grid-cols-1 md:grid-cols-2 gap-8 border">
            <h2 class="col-span-full text-4xl font-black mb-4">Settings</h2>
            <input name="name" value="{{ s.name }}" placeholder="Site Name" class="w-full border p-4 rounded-2xl outline-none">
            <input name="logo" value="{{ s.logo }}" placeholder="Logo URL" class="w-full border p-4 rounded-2xl outline-none">
            <input name="whatsapp" value="{{ s.whatsapp }}" placeholder="WhatsApp" class="w-full border p-4 rounded-2xl outline-none">
            <input name="pass" value="{{ s.pass }}" placeholder="Admin Pass" class="w-full border p-4 rounded-2xl outline-none">
            <button class="col-span-full bg-black text-white py-6 rounded-3xl font-black text-2xl">Apply</button>
        </form>
    </body>
    """, s=settings)

@app.route('/admin/login', methods=['POST'])
def admin_login_post():
    settings = get_site_settings()
    if request.form.get('pass') == settings['pass']: session['admin_logged'] = True
    return redirect('/admin/dash')

@app.route('/admin/logout')
def admin_logout(): session.clear(); return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
