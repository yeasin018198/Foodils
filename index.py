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
HEAD = """
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<script src="https://cdn.tailwindcss.com"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css"/>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@300;500;700&display=swap');
    body { font-family: 'Hind Siliguri', sans-serif; background-color: #f8fafc; }
    .no-scrollbar::-webkit-scrollbar { display: none; }
    .food-card img { height: 160px; object-fit: cover; width: 100%; border-radius: 12px; }
    @media (min-width: 768px) { .food-card img { height: 200px; } }
</style>
"""

# --- USER ROUTES ---

@app.route('/')
def home():
    track_view()
    settings = get_site_settings()
    categories = list(cats_col.find())
    
    # Search Logic
    query = request.args.get('q', '')
    if query:
        all_foods = list(foods_col.find({"name": {"$regex": query, "$options": "i"}}))
    else:
        all_foods = list(foods_col.find())

    # Slider logic: 3 items from each category
    slider_items = []
    for c in categories:
        items = list(foods_col.find({"category": c['name']}).limit(3))
        slider_items.extend(items)
    
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>"""+HEAD+"""<title>{{ settings.name }}</title></head>
    <body class="max-w-screen-xl mx-auto">
        <!-- Header & Search -->
        <nav class="bg-white shadow-sm sticky top-0 z-50 p-4">
            <div class="flex justify-between items-center mb-3">
                <div class="flex items-center gap-2">
                    <img src="{{ settings.logo }}" class="w-10 h-10 rounded-full shadow-sm">
                    <h1 class="text-xl font-bold text-{{ settings.theme }}-600">{{ settings.name }}</h1>
                </div>
            </div>
            <form action="/" method="GET" class="relative">
                <input name="q" value="{{ request.args.get('q','') }}" placeholder="Search food..." class="w-full bg-gray-100 border-none p-3 pl-10 rounded-xl outline-none focus:ring-2 focus:ring-{{ settings.theme }}-500">
                <i class="fas fa-search absolute left-4 top-4 text-gray-400"></i>
            </form>
        </nav>

        <!-- Categories Slider -->
        <div class="p-4 flex gap-4 overflow-x-auto no-scrollbar bg-white border-b">
            {% for cat in categories %}
            <a href="/category/{{ cat.name }}" class="flex flex-col items-center min-w-[80px] animate__animated animate__fadeIn">
                <div class="w-14 h-14 rounded-full border-2 border-{{ settings.theme }}-500 p-1">
                    <img src="{{ cat.logo }}" class="w-full h-full rounded-full object-cover">
                </div>
                <span class="text-[10px] mt-1 font-bold">{{ cat.name }}</span>
            </a>
            {% endfor %}
        </div>

        {% if not request.args.get('q') %}
        <!-- Hero Slider (Only if not searching) -->
        <div class="p-4">
            <h2 class="text-lg font-bold mb-3 flex items-center gap-2"><span class="w-1 h-5 bg-{{ settings.theme }}-600 rounded"></span> Featured Food</h2>
            <div class="flex gap-4 overflow-x-auto no-scrollbar">
                {% for item in slider_items %}
                <a href="/food/{{ item._id }}" class="min-w-[280px] bg-white rounded-2xl shadow-sm overflow-hidden border">
                    <img src="{{ item.image }}" class="w-full h-40 object-cover">
                    <div class="p-3">
                        <h3 class="font-bold">{{ item.name }}</h3>
                        <p class="text-{{ settings.theme }}-600 font-bold">৳{{ item.price }}</p>
                    </div>
                </a>
                {% endfor %}
            </div>
        </div>
        {% endif %}

        <!-- All Food Grid -->
        <div class="p-4">
            <h2 class="text-lg font-bold mb-3 flex items-center gap-2"><span class="w-1 h-5 bg-gray-800 rounded"></span> Menu Items</h2>
            <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
                {% for food in all_foods %}
                <a href="/food/{{ food._id }}" class="food-card bg-white rounded-2xl shadow-sm p-2 animate__animated animate__fadeInUp border">
                    <img src="{{ food.image }}" class="w-full h-32 object-cover rounded-lg">
                    <h4 class="text-sm font-bold mt-2 truncate">{{ food.name }}</h4>
                    <div class="flex justify-between items-center mt-1">
                        <span class="text-{{ settings.theme }}-600 font-bold text-sm">৳{{ food.price }}</span>
                        <span class="text-[8px] bg-gray-100 px-2 py-1 rounded text-gray-500 uppercase">{{ food.category }}</span>
                    </div>
                </a>
                {% endfor %}
            </div>
        </div>

        <footer class="bg-white border-t mt-10 p-10 text-center">
            <p class="font-bold text-gray-700">{{ settings.footer_text }}</p>
            <div class="flex justify-center gap-6 my-4 text-2xl">
                <a href="{{ settings.fb }}" class="text-blue-600"><i class="fab fa-facebook"></i></a>
                <a href="https://wa.me/{{ settings.whatsapp }}" class="text-green-500"><i class="fab fa-whatsapp"></i></a>
            </div>
            <p class="text-[10px] text-gray-400">{{ settings.dmca }} | {{ settings.copyright }}</p>
        </footer>
    </body>
    </html>
    """, settings=settings, categories=categories, slider_items=slider_items, all_foods=all_foods)

@app.route('/category/<name>')
def category_view(name):
    settings = get_site_settings()
    foods = list(foods_col.find({"category": name}))
    return render_template_string("""
    <head>"""+HEAD+"""<title>{{ name }}</title></head>
    <body class="p-4 max-w-screen-xl mx-auto">
        <div class="flex items-center gap-4 mb-6">
            <a href="/" class="w-10 h-10 bg-white shadow rounded-full flex items-center justify-center"><i class="fas fa-arrow-left"></i></a>
            <h1 class="text-2xl font-bold">{{ name }} Items</h1>
        </div>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            {% for food in foods %}
            <a href="/food/{{ food._id }}" class="food-card bg-white rounded-2xl shadow-sm p-2 border">
                <img src="{{ food.image }}" class="w-full h-32 object-cover rounded-lg">
                <h4 class="text-sm font-bold mt-2 truncate">{{ food.name }}</h4>
                <div class="flex justify-between items-center mt-1">
                    <span class="text-{{ settings.theme }}-600 font-bold text-sm">৳{{ food.price }}</span>
                </div>
            </a>
            {% endfor %}
        </div>
    </body>
    """, foods=foods, name=name, settings=settings)

@app.route('/food/<id>')
def food_details(id):
    settings = get_site_settings()
    food = foods_col.find_one({"_id": ObjectId(id)})
    reviews = list(reviews_col.find({"food_id": id}).sort("_id", -1))
    
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>"""+HEAD+"""<title>{{ food.name }}</title></head>
    <body class="bg-gray-50 max-w-screen-md mx-auto">
        <div class="bg-white min-h-screen shadow-lg relative">
            <div class="relative">
                <img src="{{ food.image }}" class="w-full h-72 object-cover">
                <a href="/" class="absolute top-4 left-4 bg-white/50 p-2 rounded-full backdrop-blur-md w-10 h-10 flex items-center justify-center shadow-lg"><i class="fas fa-arrow-left"></i></a>
            </div>
            
            <div class="p-6">
                <!-- Unlimited Screenshot Gallery -->
                <div class="flex gap-2 overflow-x-auto no-scrollbar mb-6">
                    {% for ss in food.screenshots %}
                    <img src="{{ ss }}" class="w-24 h-24 rounded-xl object-cover border shadow-sm flex-shrink-0" onclick="window.open(this.src)">
                    {% endfor %}
                </div>

                <div class="flex justify-between items-start">
                    <h1 class="text-3xl font-bold text-gray-800">{{ food.name }}</h1>
                    <p class="text-2xl text-{{ settings.theme }}-600 font-bold">৳{{ food.price }}</p>
                </div>
                
                <div class="mt-6 p-5 bg-gray-50 rounded-2xl border border-dashed border-gray-300">
                    <h4 class="font-bold border-b pb-2 mb-3 text-gray-700"><i class="fas fa-info-circle mr-2"></i> Food Details:</h4>
                    <p class="text-gray-600 whitespace-pre-line leading-relaxed text-sm">{{ food.details }}</p>
                </div>

                <a href="https://wa.me/{{ settings.whatsapp }}?text=New Order Request!%0A---%0AItem: {{ food.name }}%0APrice: {{ food.price }}%0ACategory: {{ food.category }}%0AImage: {{ food.image }}" 
                   class="block mt-10 bg-green-500 text-white text-center py-4 rounded-2xl font-bold text-lg shadow-xl shadow-green-100 active:scale-95 transition-all">
                   <i class="fab fa-whatsapp mr-2 text-xl"></i> Order via WhatsApp
                </a>

                <!-- Reviews -->
                <div class="mt-12 border-t pt-8">
                    <h3 class="text-xl font-bold">Customer Reviews ({{ reviews|length }})</h3>
                    <form action="/review/{{ food._id }}" method="POST" class="mt-4 space-y-3 bg-gray-50 p-4 rounded-2xl border">
                        <select name="stars" class="w-full border p-3 rounded-xl outline-none">
                            <option value="5">⭐⭐⭐⭐⭐ 5 Stars</option>
                            <option value="4">⭐⭐⭐⭐ 4 Stars</option>
                            <option value="3">⭐⭐⭐ 3 Stars</option>
                            <option value="2">⭐⭐ 2 Stars</option>
                            <option value="1">⭐ 1 Star</option>
                        </select>
                        <textarea name="comment" placeholder="Your experience..." class="w-full border p-4 rounded-xl h-24 outline-none" required></textarea>
                        <button class="w-full bg-{{ settings.theme }}-600 text-white py-3 rounded-xl font-bold shadow-lg">Post Feedback</button>
                    </form>

                    <div class="mt-8 space-y-4">
                        {% for r in reviews %}
                        <div class="bg-white p-4 rounded-xl border shadow-sm">
                            <div class="text-yellow-500 text-xs">
                                {% for i in range(r.stars) %}⭐{% endfor %}
                            </div>
                            <p class="text-gray-700 mt-1 italic text-sm">"{{ r.comment }}"</p>
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
        <div class="max-w-md mx-auto mt-20 p-8 bg-white shadow-2xl rounded-3xl border">
            <h2 class="text-2xl font-bold mb-6 text-center">Admin Access</h2>
            <form action="/admin/login" method="POST" class="space-y-4">
                <input type="password" name="pass" placeholder="Enter Password" class="w-full border p-4 rounded-2xl text-center outline-none focus:ring-2 focus:ring-black">
                <button class="w-full bg-slate-900 text-white py-4 rounded-2xl font-bold">Login</button>
            </form>
        </div>
    """)
    
    settings = get_site_settings()
    search = request.args.get('search', '')
    if search:
        foods = list(foods_col.find({"name": {"$regex": search, "$options": "i"}}).sort("_id", -1))
    else:
        foods = list(foods_col.find().sort("_id", -1))

    total_foods = foods_col.count_documents({})
    total_cats = cats_col.count_documents({})
    total_views = views_col.count_documents({})
    today_views = views_col.count_documents({"date": datetime.datetime.now().strftime("%Y-%m-%d")})
    
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>"""+HEAD+"""<title>Admin Dashboard</title></head>
    <body class="flex flex-col md:flex-row bg-gray-100 min-h-screen">
        <!-- Sidebar -->
        <div class="w-full md:w-64 bg-slate-900 text-white p-6">
            <div class="flex items-center gap-3 mb-10">
                <img src="{{ settings.logo }}" class="w-8 h-8 rounded-full">
                <h2 class="text-xl font-bold text-{{ settings.theme }}-500">Panel</h2>
            </div>
            <nav class="space-y-4">
                <a href="/admin/dash" class="block p-3 bg-slate-800 rounded-xl"><i class="fas fa-chart-line mr-3"></i> Dashboard</a>
                <a href="/admin/add-food" class="block p-3 hover:bg-slate-800 rounded-xl"><i class="fas fa-plus-circle mr-3"></i> Add Food</a>
                <a href="/admin/add-cat" class="block p-3 hover:bg-slate-800 rounded-xl"><i class="fas fa-list mr-3"></i> Categories</a>
                <a href="/admin/settings" class="block p-3 hover:bg-slate-800 rounded-xl"><i class="fas fa-cog mr-3"></i> Settings</a>
                <a href="/admin/logout" class="block p-3 text-red-400 mt-10"><i class="fas fa-power-off mr-3"></i> Logout</a>
                <a href="/" class="block p-3 text-blue-400 border border-blue-400/20 rounded-xl text-center mt-5"><i class="fas fa-eye mr-2"></i> View Site</a>
            </nav>
        </div>

        <!-- Content -->
        <div class="flex-1 p-6">
            <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                <div class="bg-white p-5 rounded-2xl shadow-sm border-l-4 border-blue-500">
                    <p class="text-xs text-gray-400 font-bold uppercase">Total Views</p>
                    <h3 class="text-2xl font-bold">{{ total_views }}</h3>
                </div>
                <div class="bg-white p-5 rounded-2xl shadow-sm border-l-4 border-green-500">
                    <p class="text-xs text-gray-400 font-bold uppercase">Today Views</p>
                    <h3 class="text-2xl font-bold">{{ today_views }}</h3>
                </div>
                <div class="bg-white p-5 rounded-2xl shadow-sm border-l-4 border-orange-500">
                    <p class="text-xs text-gray-400 font-bold uppercase">Items</p>
                    <h3 class="text-2xl font-bold">{{ total_foods }}</h3>
                </div>
                <div class="bg-white p-5 rounded-2xl shadow-sm border-l-4 border-purple-500">
                    <p class="text-xs text-gray-400 font-bold uppercase">Categories</p>
                    <h3 class="text-2xl font-bold">{{ total_cats }}</h3>
                </div>
            </div>

            <div class="bg-white p-6 rounded-3xl shadow-sm">
                <div class="flex flex-col md:flex-row justify-between gap-4 mb-6">
                    <h3 class="text-xl font-bold">Manage Menu</h3>
                    <form action="/admin/dash" method="GET" class="relative">
                        <input name="search" value="{{ request.args.get('search','') }}" placeholder="Search items..." class="bg-gray-100 border p-2 pl-8 rounded-lg outline-none w-full">
                        <i class="fas fa-search absolute left-2.5 top-3 text-gray-400 text-sm"></i>
                    </form>
                </div>
                
                <div class="overflow-x-auto">
                    <table class="w-full text-left">
                        <thead>
                            <tr class="bg-gray-50 text-gray-500 text-xs uppercase">
                                <th class="p-3">Item</th>
                                <th class="p-3">Category</th>
                                <th class="p-3">Price</th>
                                <th class="p-3 text-center">Action</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y">
                            {% for f in foods %}
                            <tr>
                                <td class="p-3">
                                    <div class="flex items-center gap-3">
                                        <img src="{{ f.image }}" class="w-10 h-10 rounded-lg object-cover">
                                        <span class="font-bold text-sm">{{ f.name }}</span>
                                    </div>
                                </td>
                                <td class="p-3 text-sm text-gray-500">{{ f.category }}</td>
                                <td class="p-3 font-bold text-sm">৳{{ f.price }}</td>
                                <td class="p-3">
                                    <div class="flex justify-center gap-3">
                                        <a href="/admin/edit-food/{{ f._id }}" class="text-blue-500 hover:scale-110"><i class="fas fa-edit"></i></a>
                                        <a href="/admin/del-food/{{ f._id }}" onclick="return confirm('Delete item?')" class="text-red-500 hover:scale-110"><i class="fas fa-trash"></i></a>
                                    </div>
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
    """, foods=foods, total_foods=total_foods, total_cats=total_cats, total_views=total_views, today_views=today_views, settings=settings)

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

# --- FOOD: ADD / EDIT / DELETE ---

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
    <body class="p-6 bg-gray-100">
        <div class="max-w-2xl mx-auto bg-white p-8 rounded-3xl shadow-lg border">
            <div class="flex items-center gap-4 mb-8">
                <a href="/admin/dash" class="text-gray-400 hover:text-black"><i class="fas fa-arrow-left text-xl"></i></a>
                <h2 class="text-2xl font-bold">Add New Food</h2>
            </div>
            <form method="POST" class="space-y-5">
                <div class="grid grid-cols-2 gap-4">
                    <input name="name" placeholder="Item Name" class="w-full border p-4 rounded-2xl outline-none" required>
                    <input name="price" placeholder="Price (Example: 150)" class="w-full border p-4 rounded-2xl outline-none" required>
                </div>
                <input name="image" placeholder="Main Image URL" class="w-full border p-4 rounded-2xl outline-none" required>
                <select name="category" class="w-full border p-4 rounded-2xl outline-none">
                    {% for cat in categories %} <option value="{{ cat.name }}">{{ cat.name }}</option> {% endfor %}
                </select>
                <textarea name="screenshots" placeholder="Unlimited Screenshots (URL1, URL2, URL3...)" class="w-full border p-4 rounded-2xl h-24 outline-none"></textarea>
                <textarea name="details" placeholder="Full Details..." class="w-full border p-4 rounded-2xl h-40 outline-none" required></textarea>
                <button class="w-full bg-orange-600 text-white py-4 rounded-2xl font-bold text-lg shadow-lg">Save Item</button>
            </form>
        </div>
    </body>
    """, categories=categories)

@app.route('/admin/edit-food/<id>', methods=['GET', 'POST'])
def edit_food(id):
    if not session.get('admin_logged'): return redirect('/admin/dash')
    food = foods_col.find_one({"_id": ObjectId(id)})
    if request.method == 'POST':
        ss_list = [x.strip() for x in request.form.get('screenshots').split(',') if x.strip()]
        foods_col.update_one({"_id": ObjectId(id)}, {"$set": {
            "name": request.form.get('name'),
            "image": request.form.get('image'),
            "price": request.form.get('price'),
            "category": request.form.get('category'),
            "screenshots": ss_list,
            "details": request.form.get('details')
        }})
        return redirect('/admin/dash')
    
    categories = list(cats_col.find())
    ss_str = ",".join(food.get('screenshots', []))
    return render_template_string("""
    <head>"""+HEAD+"""</head>
    <body class="p-6 bg-gray-100">
        <div class="max-w-2xl mx-auto bg-white p-8 rounded-3xl shadow-lg border">
            <div class="flex items-center gap-4 mb-8">
                <a href="/admin/dash" class="text-gray-400 hover:text-black"><i class="fas fa-arrow-left text-xl"></i></a>
                <h2 class="text-2xl font-bold">Edit Food Item</h2>
            </div>
            <form method="POST" class="space-y-5">
                <div class="grid grid-cols-2 gap-4">
                    <input name="name" value="{{ f.name }}" class="w-full border p-4 rounded-2xl outline-none" required>
                    <input name="price" value="{{ f.price }}" class="w-full border p-4 rounded-2xl outline-none" required>
                </div>
                <input name="image" value="{{ f.image }}" class="w-full border p-4 rounded-2xl outline-none" required>
                <select name="category" class="w-full border p-4 rounded-2xl outline-none">
                    {% for cat in categories %} 
                    <option value="{{ cat.name }}" {% if cat.name == f.category %}selected{% endif %}>{{ cat.name }}</option> 
                    {% endfor %}
                </select>
                <textarea name="screenshots" class="w-full border p-4 rounded-2xl h-24 outline-none">{{ ss_str }}</textarea>
                <textarea name="details" class="w-full border p-4 rounded-2xl h-40 outline-none" required>{{ f.details }}</textarea>
                <button class="w-full bg-blue-600 text-white py-4 rounded-2xl font-bold text-lg shadow-lg">Update Item</button>
            </form>
        </div>
    </body>
    """, f=food, categories=categories, ss_str=ss_str)

@app.route('/admin/del-food/<id>')
def del_food(id):
    if not session.get('admin_logged'): return redirect('/admin/dash')
    foods_col.delete_one({"_id": ObjectId(id)})
    return redirect('/admin/dash')

# --- CATEGORY: ADD / EDIT / DELETE ---

@app.route('/admin/add-cat', methods=['GET', 'POST'])
def admin_add_cat():
    if not session.get('admin_logged'): return redirect('/admin/dash')
    if request.method == 'POST':
        cats_col.insert_one({"name": request.form.get('name'), "logo": request.form.get('logo')})
    
    categories = list(cats_col.find())
    return render_template_string("""
    <head>"""+HEAD+"""</head>
    <body class="p-6 bg-gray-100">
        <div class="max-w-4xl mx-auto grid md:grid-cols-2 gap-10">
            <div class="bg-white p-8 rounded-3xl shadow h-fit border">
                <div class="flex items-center gap-4 mb-6">
                    <a href="/admin/dash" class="text-gray-400"><i class="fas fa-arrow-left"></i></a>
                    <h3 class="text-xl font-bold">Create Category</h3>
                </div>
                <form method="POST" class="space-y-4">
                    <input name="name" placeholder="Category Name" class="w-full border p-4 rounded-2xl outline-none" required>
                    <input name="logo" placeholder="Logo Image URL" class="w-full border p-4 rounded-2xl outline-none" required>
                    <button class="w-full bg-slate-900 text-white py-4 rounded-2xl font-bold">Add Category</button>
                </form>
            </div>
            <div class="bg-white p-8 rounded-3xl shadow border">
                <h3 class="text-xl font-bold mb-6">All Categories</h3>
                <div class="space-y-3">
                    {% for cat in categories %}
                    <div class="flex justify-between items-center p-3 bg-gray-50 rounded-2xl border">
                        <div class="flex items-center gap-3">
                            <img src="{{ cat.logo }}" class="w-10 h-10 rounded-full object-cover">
                            <span class="font-bold">{{ cat.name }}</span>
                        </div>
                        <div class="flex gap-4">
                            <a href="/admin/edit-cat/{{ cat._id }}" class="text-blue-500"><i class="fas fa-edit"></i></a>
                            <a href="/admin/del-cat/{{ cat._id }}" onclick="return confirm('Delete category?')" class="text-red-500"><i class="fas fa-trash"></i></a>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </body>
    """, categories=categories)

@app.route('/admin/edit-cat/<id>', methods=['GET', 'POST'])
def edit_cat(id):
    if not session.get('admin_logged'): return redirect('/admin/dash')
    cat = cats_col.find_one({"_id": ObjectId(id)})
    if request.method == 'POST':
        cats_col.update_one({"_id": ObjectId(id)}, {"$set": {
            "name": request.form.get('name'),
            "logo": request.form.get('logo')
        }})
        return redirect('/admin/add-cat')
    
    return render_template_string("""
    <head>"""+HEAD+"""</head>
    <body class="p-6 bg-gray-100 flex items-center justify-center min-h-screen">
        <form method="POST" class="bg-white p-8 rounded-3xl shadow-xl w-full max-w-md border">
            <div class="flex items-center gap-4 mb-6">
                <a href="/admin/add-cat" class="text-gray-400"><i class="fas fa-arrow-left"></i></a>
                <h3 class="text-xl font-bold">Edit Category</h3>
            </div>
            <input name="name" value="{{ c.name }}" class="w-full border p-4 rounded-2xl mb-4 outline-none">
            <input name="logo" value="{{ c.logo }}" class="w-full border p-4 rounded-2xl mb-6 outline-none">
            <button class="w-full bg-blue-600 text-white py-4 rounded-2xl font-bold">Update Category</button>
        </form>
    </body>
    """, c=cat)

@app.route('/admin/del-cat/<id>')
def del_cat(id):
    if not session.get('admin_logged'): return redirect('/admin/dash')
    cats_col.delete_one({"_id": ObjectId(id)})
    return redirect('/admin/add-cat')

# --- SETTINGS ---

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
        <form method="POST" class="max-w-4xl mx-auto bg-white p-10 rounded-3xl shadow-lg border grid grid-cols-1 md:grid-cols-2 gap-6 relative">
            <div class="col-span-2 flex items-center gap-4 mb-4">
                <a href="/admin/dash" class="text-gray-400"><i class="fas fa-arrow-left text-xl"></i></a>
                <h2 class="text-3xl font-bold">Site Settings</h2>
            </div>
            
            <div class="space-y-2"><label class="font-bold text-sm text-gray-500">Site Name</label><input name="name" value="{{ s.name }}" class="w-full border p-3 rounded-xl outline-none focus:ring-2 focus:ring-black"></div>
            <div class="space-y-2"><label class="font-bold text-sm text-gray-500">Logo URL</label><input name="logo" value="{{ s.logo }}" class="w-full border p-3 rounded-xl outline-none focus:ring-2 focus:ring-black"></div>
            <div class="space-y-2"><label class="font-bold text-sm text-gray-500">WhatsApp (Number Only)</label><input name="whatsapp" value="{{ s.whatsapp }}" class="w-full border p-3 rounded-xl outline-none focus:ring-2 focus:ring-black"></div>
            <div class="space-y-2"><label class="font-bold text-sm text-gray-500">Facebook URL</label><input name="fb" value="{{ s.fb }}" class="w-full border p-3 rounded-xl outline-none focus:ring-2 focus:ring-black"></div>
            <div class="space-y-2"><label class="font-bold text-sm text-gray-500">Admin Password</label><input name="pass" value="{{ s.pass }}" class="w-full border p-3 rounded-xl outline-none focus:ring-2 focus:ring-black"></div>
            
            <div class="space-y-2"><label class="font-bold text-sm text-gray-500">Theme Color</label>
                <select name="theme" class="w-full border p-3 rounded-xl outline-none focus:ring-2 focus:ring-black">
                    <option value="orange" {% if s.theme=='orange' %}selected{% endif %}>Orange</option>
                    <option value="blue" {% if s.theme=='blue' %}selected{% endif %}>Blue</option>
                    <option value="red" {% if s.theme=='red' %}selected{% endif %}>Red</option>
                    <option value="green" {% if s.theme=='green' %}selected{% endif %}>Green</option>
                    <option value="pink" {% if s.theme=='pink' %}selected{% endif %}>Pink</option>
                    <option value="purple" {% if s.theme=='purple' %}selected{% endif %}>Purple</option>
                    <option value="teal" {% if s.theme=='teal' %}selected{% endif %}>Teal</option>
                </select>
            </div>

            <div class="col-span-2 space-y-2"><label class="font-bold text-sm text-gray-500">Footer Tagline</label><input name="footer_text" value="{{ s.footer_text }}" class="w-full border p-3 rounded-xl outline-none w-full"></div>
            <div class="col-span-2 space-y-2"><label class="font-bold text-sm text-gray-500">Privacy Policy Content</label><textarea name="privacy" class="w-full border p-3 rounded-xl h-24 outline-none">{{ s.privacy }}</textarea></div>
            
            <div class="space-y-2"><label class="font-bold text-sm text-gray-500">DMCA Text</label><input name="dmca" value="{{ s.dmca }}" class="w-full border p-3 rounded-xl outline-none"></div>
            <div class="space-y-2"><label class="font-bold text-sm text-gray-500">Copyright Text</label><input name="copyright" value="{{ s.copyright }}" class="w-full border p-3 rounded-xl outline-none"></div>
            
            <button class="col-span-2 bg-slate-900 text-white py-5 rounded-2xl font-bold text-xl mt-6 shadow-xl">Apply Changes</button>
        </form>
    </body>
    """, s=settings)

if __name__ == '__main__':
    app.run(debug=True)
