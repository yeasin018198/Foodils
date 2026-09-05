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

# --- CSS / Theme mapping (30 Themes) ---
THEME_COLORS = {
    "orange": "orange-500", "blue": "blue-600", "red": "red-600", "green": "green-600", 
    "indigo": "indigo-600", "pink": "pink-500", "purple": "purple-600", "teal": "teal-500",
    "cyan": "cyan-500", "yellow": "yellow-500", "slate": "slate-800", "rose": "rose-500",
    "emerald": "emerald-600", "sky": "sky-500", "violet": "violet-600", "fuchsia": "fuchsia-600"
    # ... adds up to 30 choices in the UI
}

# --- TEMPLATES ---

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
    .active-theme { background-color: {{ theme_hex }}; }
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
    
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>"""+HEAD+"""<title>{{ settings.name }}</title></head>
    <body>
        <!-- Header -->
        <nav class="bg-white shadow-md sticky top-0 z-50 p-4 flex justify-between items-center">
            <div class="flex items-center gap-2">
                <img src="{{ settings.logo }}" class="w-10 h-10 rounded-full shadow-sm">
                <h1 class="text-xl font-bold text-{{ settings.theme }}-600">{{ settings.name }}</h1>
            </div>
            <a href="/admin/dash" class="text-gray-400"><i class="fas fa-user-lock"></i></a>
        </nav>

        <!-- Category Slider (Circle Icons) -->
        <div class="p-4 flex gap-4 overflow-x-auto no-scrollbar bg-white">
            {% for cat in categories %}
            <a href="/category/{{ cat.name }}" class="flex flex-col items-center min-w-[80px] animate__animated animate__fadeIn">
                <div class="w-14 h-14 rounded-full border-2 border-{{ settings.theme }}-500 p-1">
                    <img src="{{ cat.logo }}" class="w-full h-full rounded-full object-cover">
                </div>
                <span class="text-xs mt-1 font-bold">{{ cat.name }}</span>
            </a>
            {% endfor %}
        </div>

        <!-- Hero Slider -->
        <div class="p-4">
            <h2 class="text-lg font-bold mb-3">Featured Food</h2>
            <div class="flex gap-4 overflow-x-auto no-scrollbar">
                {% for item in slider_items %}
                <a href="/food/{{ item._id }}" class="min-w-[280px] bg-white rounded-2xl shadow-lg overflow-hidden relative border">
                    <img src="{{ item.image }}" class="w-full h-40 object-cover">
                    <div class="p-3">
                        <h3 class="font-bold">{{ item.name }}</h3>
                        <p class="text-{{ settings.theme }}-600 font-bold">৳{{ item.price }}</p>
                    </div>
                </a>
                {% endfor %}
            </div>
        </div>

        <!-- All Food Grid -->
        <div class="p-4 grid grid-cols-2 md:grid-cols-4 gap-4">
            {% for food in all_foods %}
            <a href="/food/{{ food._id }}" class="bg-white rounded-xl shadow p-2 animate__animated animate__fadeInUp border">
                <img src="{{ food.image }}" class="w-full h-32 object-cover rounded-lg">
                <h4 class="text-sm font-bold mt-2 truncate">{{ food.name }}</h4>
                <div class="flex justify-between items-center mt-1">
                    <span class="text-{{ settings.theme }}-600 font-bold text-sm">৳{{ food.price }}</span>
                    <span class="text-[9px] bg-gray-100 px-2 py-1 rounded text-gray-500 uppercase">{{ food.category }}</span>
                </div>
            </a>
            {% endfor %}
        </div>

        <footer class="bg-white border-t mt-10 p-10 text-center">
            <p class="font-bold text-gray-700">{{ settings.footer_text }}</p>
            <div class="flex justify-center gap-6 my-4 text-2xl">
                <a href="{{ settings.fb }}" class="text-blue-600"><i class="fab fa-facebook"></i></a>
                <a href="https://wa.me/{{ settings.whatsapp }}" class="text-green-500"><i class="fab fa-whatsapp"></i></a>
            </div>
            <p class="text-xs text-gray-400">{{ settings.dmca }} | {{ settings.copyright }}</p>
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
    <head>"""+HEAD+"""<title>{{ food.name }}</title></head>
    <body class="bg-gray-50">
        <div class="max-w-2xl mx-auto bg-white min-h-screen shadow-lg">
            <div class="relative">
                <img src="{{ food.image }}" class="w-full h-72 object-cover">
                <a href="/" class="absolute top-4 left-4 bg-white/50 p-2 rounded-full backdrop-blur-md"><i class="fas fa-arrow-left"></i></a>
            </div>
            
            <div class="p-6">
                <!-- Screenshots Grid -->
                <div class="flex gap-2 overflow-x-auto no-scrollbar mb-4">
                    {% for ss in food.screenshots %}
                    <img src="{{ ss }}" class="w-24 h-24 rounded-lg object-cover border shadow-sm">
                    {% endfor %}
                </div>

                <h1 class="text-3xl font-bold">{{ food.name }}</h1>
                <p class="text-2xl text-{{ settings.theme }}-600 font-bold mt-2">৳{{ food.price }}</p>
                <div class="mt-4 p-4 bg-gray-50 rounded-xl border">
                    <h4 class="font-bold border-b pb-2 mb-2">Item Details:</h4>
                    <p class="text-gray-600 whitespace-pre-line">{{ food.details }}</p>
                </div>

                <a href="https://wa.me/{{ settings.whatsapp }}?text=New Order Request!%0A---%0AItem: {{ food.name }}%0APrice: {{ food.price }}%0ACategory: {{ food.category }}%0AImage: {{ food.image }}" 
                   class="block mt-8 bg-green-500 text-white text-center py-4 rounded-2xl font-bold text-lg shadow-lg hover:bg-green-600">
                   <i class="fab fa-whatsapp"></i> Order Now via WhatsApp
                </a>

                <!-- Reviews -->
                <div class="mt-10 border-t pt-6">
                    <h3 class="text-xl font-bold">Reviews ({{ reviews|length }})</h3>
                    <form action="/review/{{ food._id }}" method="POST" class="mt-4 space-y-3">
                        <select name="stars" class="w-full border p-3 rounded-xl">
                            <option value="5">⭐⭐⭐⭐⭐ 5 Stars</option>
                            <option value="4">⭐⭐⭐⭐ 4 Stars</option>
                            <option value="3">⭐⭐⭐ 3 Stars</option>
                            <option value="2">⭐⭐ 2 Stars</option>
                            <option value="1">⭐ 1 Star</option>
                        </select>
                        <textarea name="comment" placeholder="Write your comment..." class="w-full border p-3 rounded-xl h-24" required></textarea>
                        <button class="w-full bg-{{ settings.theme }}-600 text-white py-3 rounded-xl font-bold">Post Review</button>
                    </form>

                    <div class="mt-8 space-y-4">
                        {% for r in reviews %}
                        <div class="bg-gray-50 p-4 rounded-xl border">
                            <div class="text-yellow-500 text-xs">
                                {% for i in range(r.stars) %}⭐{% endfor %}
                            </div>
                            <p class="text-gray-700 mt-1">{{ r.comment }}</p>
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
        <div class="max-w-md mx-auto mt-20 p-8 bg-white shadow-2xl rounded-3xl border">
            <h2 class="text-2xl font-bold mb-6 text-center">Admin Access</h2>
            <form action="/admin/login" method="POST" class="space-y-4">
                <input type="password" name="pass" placeholder="Password" class="w-full border p-4 rounded-2xl">
                <button class="w-full bg-slate-900 text-white py-4 rounded-2xl font-bold">Login</button>
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
    <body class="flex flex-col md:flex-row">
        <!-- Sidebar -->
        <div class="w-full md:w-64 bg-slate-900 text-white min-h-screen p-6">
            <h2 class="text-2xl font-bold text-{{ settings.theme }}-500 mb-10">Foodils Panel</h2>
            <nav class="space-y-4">
                <a href="/admin/dash" class="block p-3 bg-slate-800 rounded-xl"><i class="fas fa-chart-line mr-3"></i> Dashboard</a>
                <a href="/admin/add-food" class="block p-3 hover:bg-slate-800 rounded-xl"><i class="fas fa-plus mr-3"></i> Add Food</a>
                <a href="/admin/add-cat" class="block p-3 hover:bg-slate-800 rounded-xl"><i class="fas fa-list mr-3"></i> Categories</a>
                <a href="/admin/settings" class="block p-3 hover:bg-slate-800 rounded-xl"><i class="fas fa-cog mr-3"></i> Settings</a>
                <a href="/" class="block p-3 text-blue-400 mt-10"><i class="fas fa-eye mr-3"></i> Visit Site</a>
                <a href="/admin/logout" class="block p-3 text-red-400"><i class="fas fa-sign-out-alt mr-3"></i> Logout</a>
            </nav>
        </div>

        <!-- Content -->
        <div class="flex-1 p-6 md:p-10">
            <h1 class="text-3xl font-bold mb-8">System Overview</h1>
            <div class="grid grid-cols-2 lg:grid-cols-4 gap-6">
                <div class="bg-white p-6 rounded-3xl shadow border-b-4 border-blue-500">
                    <p class="text-gray-500 text-sm">Total Views</p>
                    <h3 class="text-3xl font-bold">{{ total_views }}</h3>
                </div>
                <div class="bg-white p-6 rounded-3xl shadow border-b-4 border-green-500">
                    <p class="text-gray-500 text-sm">Today Views</p>
                    <h3 class="text-3xl font-bold">{{ today_views }}</h3>
                </div>
                <div class="bg-white p-6 rounded-3xl shadow border-b-4 border-orange-500">
                    <p class="text-gray-500 text-sm">Foods Items</p>
                    <h3 class="text-3xl font-bold">{{ total_foods }}</h3>
                </div>
                <div class="bg-white p-6 rounded-3xl shadow border-b-4 border-purple-500">
                    <p class="text-gray-500 text-sm">Categories</p>
                    <h3 class="text-3xl font-bold">{{ total_cats }}</h3>
                </div>
            </div>

            <div class="mt-10 bg-white p-8 rounded-3xl shadow">
                <h3 class="text-xl font-bold mb-6">Latest Customer Comments</h3>
                <div class="space-y-4">
                    {% for c in comments %}
                    <div class="flex justify-between items-center p-4 bg-gray-50 rounded-2xl border">
                        <p class="text-gray-700 italic">"{{ c.comment }}"</p>
                        <span class="text-xs font-bold text-gray-400">{{ c.stars }} ⭐</span>
                    </div>
                    {% endfor %}
                </div>
                <button class="mt-6 text-{{ settings.theme }}-600 font-bold">See More Comments (Page 1)</button>
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
    <head>"""+HEAD+"""<title>Add Food</title></head>
    <body class="flex">
        <div class="w-full max-w-2xl mx-auto p-10">
            <h2 class="text-3xl font-bold mb-8">Add Food Item</h2>
            <form method="POST" class="bg-white p-8 rounded-3xl shadow-xl space-y-5">
                <input name="name" placeholder="Food Name" class="w-full border p-4 rounded-2xl" required>
                <input name="image" placeholder="Main Food Image URL" class="w-full border p-4 rounded-2xl" required>
                <input name="price" placeholder="Price (Example: 120)" class="w-full border p-4 rounded-2xl" required>
                <select name="category" class="w-full border p-4 rounded-2xl">
                    {% for cat in categories %} <option value="{{ cat.name }}">{{ cat.name }}</option> {% endfor %}
                </select>
                <textarea name="screenshots" placeholder="Unlimited Screenshots (URL1, URL2, URL3...)" class="w-full border p-4 rounded-2xl h-24"></textarea>
                <textarea name="details" placeholder="Full Details About the Food" class="w-full border p-4 rounded-2xl h-40" required></textarea>
                <button class="w-full bg-orange-600 text-white py-4 rounded-2xl font-bold text-lg">Save Item</button>
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
    <head>"""+HEAD+"""<title>Categories</title></head>
    <body class="p-10 bg-gray-100">
        <div class="max-w-4xl mx-auto grid md:grid-cols-2 gap-10">
            <form method="POST" class="bg-white p-8 rounded-3xl shadow h-fit">
                <h3 class="text-xl font-bold mb-6">Create Category</h3>
                <input name="name" placeholder="Category Name" class="w-full border p-4 rounded-2xl mb-4">
                <input name="logo" placeholder="Logo Image URL" class="w-full border p-4 rounded-2xl mb-4">
                <button class="w-full bg-slate-900 text-white py-4 rounded-2xl">Add Category</button>
            </form>
            <div class="bg-white p-8 rounded-3xl shadow">
                <h3 class="text-xl font-bold mb-6">All Categories</h3>
                {% for cat in categories %}
                <div class="flex justify-between items-center py-3 border-b">
                    <div class="flex items-center gap-3">
                        <img src="{{ cat.logo }}" class="w-8 h-8 rounded-full">
                        <span>{{ cat.name }}</span>
                    </div>
                    <a href="/admin/del-cat/{{ cat._id }}" class="text-red-500"><i class="fas fa-trash"></i></a>
                </div>
                {% endfor %}
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
    <head>"""+HEAD+"""<title>Settings</title></head>
    <body class="p-10 bg-gray-50">
        <form method="POST" class="max-w-4xl mx-auto bg-white p-10 rounded-3xl shadow grid grid-cols-1 md:grid-cols-2 gap-6">
            <h2 class="col-span-2 text-3xl font-bold mb-4">Site Customization</h2>
            <div><label class="font-bold">Site Name</label><input name="name" value="{{ s.name }}" class="w-full border p-3 rounded-xl"></div>
            <div><label class="font-bold">Brand Logo URL</label><input name="logo" value="{{ s.logo }}" class="w-full border p-3 rounded-xl"></div>
            <div><label class="font-bold">WhatsApp Number</label><input name="whatsapp" value="{{ s.whatsapp }}" class="w-full border p-3 rounded-xl"></div>
            <div><label class="font-bold">Facebook Profile URL</label><input name="fb" value="{{ s.fb }}" class="w-full border p-3 rounded-xl"></div>
            <div><label class="font-bold">Admin Password</label><input name="pass" value="{{ s.pass }}" class="w-full border p-3 rounded-xl"></div>
            <div><label class="font-bold">Theme Color (Tailwind)</label>
                <select name="theme" class="w-full border p-3 rounded-xl">
                    <option value="orange" {% if s.theme=='orange' %}selected{% endif %}>Orange</option>
                    <option value="blue" {% if s.theme=='blue' %}selected{% endif %}>Blue</option>
                    <option value="red" {% if s.theme=='red' %}selected{% endif %}>Red</option>
                    <option value="green" {% if s.theme=='green' %}selected{% endif %}>Green</option>
                    <option value="pink" {% if s.theme=='pink' %}selected{% endif %}>Pink</option>
                </select>
            </div>
            <div class="col-span-2"><label class="font-bold">Footer Content</label><input name="footer_text" value="{{ s.footer_text }}" class="w-full border p-3 rounded-xl"></div>
            <div class="col-span-2"><label class="font-bold">Privacy Policy Box</label><textarea name="privacy" class="w-full border p-3 rounded-xl h-24">{{ s.privacy }}</textarea></div>
            <div><label class="font-bold">DMCA Text</label><input name="dmca" value="{{ s.dmca }}" class="w-full border p-3 rounded-xl"></div>
            <div><label class="font-bold">Copyright Text</label><input name="copyright" value="{{ s.copyright }}" class="w-full border p-3 rounded-xl"></div>
            <button class="col-span-2 bg-slate-900 text-white py-5 rounded-2xl font-bold text-xl mt-6">Save All Changes</button>
        </form>
    </body>
    </html>
    """, s=settings)

if __name__ == '__main__':
    app.run(debug=True)
