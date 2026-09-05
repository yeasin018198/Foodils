import os
import datetime
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = "secret_key_123"

# --- MongoDB Connection ---
MONGO_URI = "mongodb+srv://akash:akash@cluster0.hjyqogc.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['food_prodb']

# Collections
settings_col = db['settings']
foods_col = db['foods']
cats_col = db['categories']
reviews_col = db['reviews']
views_col = db['views']

# --- Helper Functions ---
def get_settings():
    conf = settings_col.find_one({"id": "config"})
    if not conf:
        default = {
            "id": "config", "name": "Foodils", "logo": "https://via.placeholder.com/50",
            "fb": "#", "whatsapp": "8801700000000", "dmca": "DMCA Text", 
            "pass": "admin123", "privacy": "Privacy Policy", "copyright": "© 2024",
            "theme": "orange", "header_text": "", "footer_text": ""
        }
        settings_col.insert_one(default)
        return default
    return conf

def track_view():
    ip = request.remote_addr
    now = datetime.datetime.now()
    six_hours_ago = now - datetime.timedelta(hours=6)
    existing = views_col.find_one({"ip": ip, "time": {"$gt": six_hours_ago}})
    if not existing:
        views_col.insert_one({"ip": ip, "time": now, "date": now.strftime("%Y-%m-%d")})

# --- CSS Themes (30 Themes System) ---
THEMES = {
    "orange": "orange-500", "blue": "blue-600", "red": "red-600", "green": "green-600", 
    "dark": "gray-900", "pink": "pink-500", "purple": "purple-600", "teal": "teal-500"
    # এভাবে ৩০টি কালার কম্বিনেশন টেইলউইন্ড দিয়ে কন্ট্রোল করা যাবে
}

# --- HTML TEMPLATES ---

COMMON_HEAD = """
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<script src="https://cdn.tailwindcss.com"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css"/>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@300;500;700&display=swap');
    body { font-family: 'Hind Siliguri', sans-serif; }
    .no-scrollbar::-webkit-scrollbar { display: none; }
</style>
"""

USER_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head> """ + COMMON_HEAD + """ <title>{{ settings.name }}</title></head>
<body class="bg-gray-50">
    <nav class="bg-white shadow-sm sticky top-0 z-50 p-3 flex justify-between items-center">
        <div class="flex items-center gap-2">
            <img src="{{ settings.logo }}" class="w-8 h-8 rounded-full">
            <span class="font-bold text-lg text-{{ settings.theme }}">{{ settings.name }}</span>
        </div>
        <a href="/admin/login" class="text-gray-400 text-xs">Admin</a>
    </nav>
    
    {{ content | safe }}

    <footer class="bg-white border-t mt-10 p-6 text-center">
        <p class="text-sm">{{ settings.footer_text }}</p>
        <p class="text-gray-500 text-xs mt-2">{{ settings.copyright }}</p>
    </footer>
</body>
</html>
"""

# --- ADMIN TEMPLATE ---
ADMIN_LAYOUT = """
<!DOCTYPE html>
<html>
<head> """ + COMMON_HEAD + """ <title>Admin Panel</title></head>
<body class="bg-gray-100 flex flex-col md:flex-row min-h-screen">
    <div class="w-full md:w-64 bg-slate-900 text-white p-5">
        <h2 class="text-xl font-bold mb-6 text-{{ settings.theme }}">Admin Dashboard</h2>
        <nav class="space-y-3">
            <a href="/admin/dash" class="block hover:text-orange-400"><i class="fas fa-home w-8"></i> Dashboard</a>
            <a href="/admin/add-food" class="block hover:text-orange-400"><i class="fas fa-plus w-8"></i> Add Food</a>
            <a href="/admin/add-cat" class="block hover:text-orange-400"><i class="fas fa-list w-8"></i> Add Category</a>
            <a href="/admin/settings" class="block hover:text-orange-400"><i class="fas fa-cog w-8"></i> Site Settings</a>
            <a href="/admin/logout" class="block text-red-400 pt-10"><i class="fas fa-sign-out-alt w-8"></i> Logout</a>
        </nav>
    </div>
    <div class="flex-1 p-5 md:p-10">{{ content | safe }}</div>
</body>
</html>
"""

# --- ROUTES ---

@app.route('/')
def home():
    track_view()
    settings = get_settings()
    cats = list(cats_col.find())
    
    # Logic for Slider (3 items per category)
    slider_items = []
    for c in cats:
        items = list(foods_col.find({"category": c['name']}).limit(3))
        slider_items.extend(items)

    html = f"""
    <!-- Category Icons -->
    <div class="flex gap-4 p-4 overflow-x-auto no-scrollbar bg-white shadow-sm">
        {% for cat in cats %}
        <a href="/category/{{{{ cat.name }}}}" class="flex flex-col items-center min-w-[70px]">
            <img src="{{{{ cat.logo }}}}" class="w-12 h-12 rounded-full border p-1 border-orange-200 shadow-sm">
            <span class="text-xs mt-1 font-medium">{{{{ cat.name }}}}</span>
        </a>
        {% endfor %}
    </div>

    <!-- Slider -->
    <div class="p-4">
        <div class="flex gap-4 overflow-x-auto no-scrollbar">
            {% for item in slider_items %}
            <div class="min-w-[280px] bg-white rounded-xl shadow-md overflow-hidden relative">
                <img src="{{{{ item.image }}}}" class="w-full h-40 object-cover">
                <div class="p-3">
                    <h3 class="font-bold">{{{{ item.name }}}}</h3>
                    <p class="text-orange-500">৳ {{{{ item.price }}}}</p>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>

    <!-- All Items -->
    <div class="p-4 grid grid-cols-2 md:grid-cols-4 gap-4">
        {% for food in foods %}
        <a href="/food/{{{{ food._id }}}}" class="bg-white rounded-lg shadow p-2 animate__animated animate__zoomIn">
            <img src="{{{{ food.image }}}}" class="w-full h-32 object-cover rounded">
            <h4 class="text-sm font-bold mt-2">{{{{ food.name }}}}</h4>
            <div class="flex justify-between items-center mt-1">
                <span class="text-orange-600 font-bold text-sm">৳ {{{{ food.price }}}}</span>
                <span class="text-[10px] bg-gray-100 px-2 rounded text-gray-500">{{{{ food.category }}}}</span>
            </div>
        </a>
        {% endfor %}
    </div>
    """
    foods = list(foods_col.find())
    return render_template_string(USER_LAYOUT, settings=settings, content=render_template_string(html, cats=cats, slider_items=slider_items, foods=foods))

@app.route('/food/<id>')
def food_detail(id):
    settings = get_settings()
    food = foods_col.find_one({"_id": ObjectId(id)})
    reviews = list(reviews_col.find({"food_id": id}).sort("_id", -1))
    
    html = f"""
    <div class="max-w-4xl mx-auto p-4">
        <img src="{{{{ food.image }}}}" class="w-full h-64 object-cover rounded-2xl shadow-lg">
        
        <!-- Screenshots -->
        <div class="flex gap-2 mt-4 overflow-x-auto no-scrollbar">
            {% for ss in food.screenshots %}
            <img src="{{{{ ss }}}}" class="w-24 h-24 rounded object-cover shadow border">
            {% endfor %}
        </div>

        <h1 class="text-3xl font-bold mt-6">{{{{ food.name }}}}</h1>
        <p class="text-orange-600 text-2xl font-bold">৳ {{{{ food.price }}}}</p>
        <p class="mt-4 text-gray-700 whitespace-pre-line">{{{{ food.details }}}}</p>

        <a href="https://wa.me/{{{{ settings.whatsapp }}}}?text=Order Item: {{{{ food.name }}}}%0APrice: {{{{ food.price }}}}%0ACategory: {{{{ food.category }}}}" 
           class="block mt-8 bg-green-500 text-white text-center py-4 rounded-xl font-bold text-lg shadow-lg">
           <i class="fab fa-whatsapp"></i> Order via WhatsApp
        </a>

        <!-- Review System -->
        <div class="mt-10 bg-white p-6 rounded-xl shadow-sm">
            <h3 class="text-xl font-bold mb-4">Reviews & Comments</h3>
            <form action="/add-review/{{{{ food._id }}}}" method="POST" class="mb-6">
                <select name="stars" class="border p-2 rounded mb-2">
                    <option value="5">⭐⭐⭐⭐⭐ 5 Star</option>
                    <option value="4">⭐⭐⭐⭐ 4 Star</option>
                    <option value="3">⭐⭐⭐ 3 Star</option>
                </select>
                <textarea name="comment" class="w-full border p-3 rounded" placeholder="Your comment..."></textarea>
                <button class="bg-{{{{ settings.theme }}}} text-white px-6 py-2 rounded mt-2">Submit</button>
            </form>

            {% for r in reviews %}
            <div class="border-b py-3">
                <p class="text-yellow-500">{"⭐" * r.stars | int}</p>
                <p class="text-gray-600">{{{{ r.comment }}}}</p>
            </div>
            {% endfor %}
        </div>
    </div>
    """
    return render_template_string(USER_LAYOUT, settings=settings, content=render_template_string(html, food=food, reviews=reviews, settings=settings))

@app.route('/add-review/<id>', methods=['POST'])
def add_review(id):
    reviews_col.insert_one({
        "food_id": id,
        "stars": int(request.form.get('stars')),
        "comment": request.form.get('comment'),
        "date": datetime.datetime.now()
    })
    return redirect(f'/food/{id}')

# --- ADMIN PANEL LOGIC ---

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    settings = get_settings()
    if request.method == 'POST':
        if request.form.get('pass') == settings['pass']:
            session['admin'] = True
            return redirect('/admin/dash')
    return render_template_string("""
    <div class="max-w-md mx-auto mt-20 p-8 bg-white shadow-xl rounded-2xl">
        <h2 class="text-2xl font-bold mb-6">Admin Login</h2>
        <form method="POST">
            <input type="password" name="pass" class="w-full border p-3 rounded mb-4" placeholder="Admin Password">
            <button class="w-full bg-slate-900 text-white py-3 rounded">Login</button>
        </form>
    </div>
    """)

@app.route('/admin/dash')
def admin_dash():
    if not session.get('admin'): return redirect('/admin/login')
    settings = get_settings()
    # Stats logic
    total_items = foods_col.count_documents({})
    total_cats = cats_col.count_documents({})
    total_views = views_col.count_documents({})
    
    # Filter by date (Today)
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    today_views = views_col.count_documents({"date": today_str})
    
    comments = list(reviews_col.find().sort("_id", -1).limit(10))
    
    html = f"""
    <div class="grid grid-cols-2 md:grid-cols-4 gap-6 mb-10">
        <div class="bg-blue-600 text-white p-6 rounded-2xl"><h4>Total Items</h4><h2 class="text-3xl font-bold">{total_items}</h2></div>
        <div class="bg-purple-600 text-white p-6 rounded-2xl"><h4>Categories</h4><h2 class="text-3xl font-bold">{total_cats}</h2></div>
        <div class="bg-orange-600 text-white p-6 rounded-2xl"><h4>Total Views</h4><h2 class="text-3xl font-bold">{total_views}</h2></div>
        <div class="bg-green-600 text-white p-6 rounded-2xl"><h4>Today Views</h4><h2 class="text-3xl font-bold">{today_views}</h2></div>
    </div>

    <div class="bg-white p-6 rounded-2xl shadow-sm">
        <h3 class="text-xl font-bold mb-4">Latest Comments</h3>
        {% for c in comments %}
        <div class="p-3 border-b">
            <p class="text-sm font-bold">Food ID: {{{{ c.food_id }}}}</p>
            <p class="text-gray-600 text-sm">{{{{ c.comment }}}}</p>
        </div>
        {% endfor %}
        <button class="mt-4 text-blue-600 font-bold">See More (Pagination)</button>
    </div>
    """
    return render_template_string(ADMIN_LAYOUT, settings=settings, content=render_template_string(html, comments=comments))

@app.route('/admin/add-food', methods=['GET', 'POST'])
def admin_add_food():
    if not session.get('admin'): return redirect('/admin/login')
    settings = get_settings()
    cats = list(cats_col.find())
    
    if request.method == 'POST':
        ss_urls = request.form.get('screenshots').split(',')
        foods_col.insert_one({
            "name": request.form.get('name'),
            "image": request.form.get('image'),
            "price": request.form.get('price'),
            "category": request.form.get('category'),
            "screenshots": [s.strip() for s in ss_urls],
            "details": request.form.get('details')
        })
        return redirect('/admin/dash')

    html = f"""
    <h2 class="text-2xl font-bold mb-6">Add Food Box</h2>
    <form method="POST" class="bg-white p-8 rounded-2xl shadow-lg space-y-4 max-w-2xl">
        <input name="name" placeholder="Food Name" class="w-full border p-3 rounded" required>
        <input name="image" placeholder="Main Image URL" class="w-full border p-3 rounded" required>
        <input name="price" placeholder="Price (৳)" class="w-full border p-3 rounded" required>
        <select name="category" class="w-full border p-3 rounded">
            {% for c in cats %} <option value="{{{{ c.name }}}}">{{{{ c.name }}}}</option> {% endfor %}
        </select>
        <textarea name="screenshots" placeholder="Screenshots URLs (comma separated)" class="w-full border p-3 rounded"></textarea>
        <textarea name="details" placeholder="Detailed Description" class="w-full border p-3 rounded h-32"></textarea>
        <button class="w-full bg-{{ settings.theme }} text-white py-3 rounded font-bold">Save Food Item</button>
    </form>
    """
    return render_template_string(ADMIN_LAYOUT, settings=settings, content=render_template_string(html, cats=cats))

@app.route('/admin/add-cat', methods=['GET', 'POST'])
def admin_add_cat():
    if not session.get('admin'): return redirect('/admin/login')
    settings = get_settings()
    if request.method == 'POST':
        cats_col.insert_one({"name": request.form.get('name'), "logo": request.form.get('logo')})
    
    all_cats = list(cats_col.find())
    html = f"""
    <div class="grid md:grid-cols-2 gap-10">
        <form method="POST" class="bg-white p-6 rounded-xl shadow h-fit">
            <h3 class="font-bold mb-4">Add Category</h3>
            <input name="name" placeholder="Category Name" class="w-full border p-2 mb-3">
            <input name="logo" placeholder="Category Logo URL" class="w-full border p-2 mb-3">
            <button class="bg-blue-600 text-white px-4 py-2 rounded">Save</button>
        </form>
        <div class="bg-white p-6 rounded-xl shadow">
            <h3 class="font-bold mb-4">All Categories</h3>
            {% for c in all_cats %}
            <div class="flex justify-between items-center border-b py-2">
                <span>{{{{ c.name }}}}</span>
                <a href="/admin/del-cat/{{{{ c._id }}}}" class="text-red-500">Delete</a>
            </div>
            {% endfor %}
        </div>
    </div>
    """
    return render_template_string(ADMIN_LAYOUT, settings=settings, content=render_template_string(html, all_cats=all_cats))

@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_site_settings():
    if not session.get('admin'): return redirect('/admin/login')
    settings = get_settings()
    if request.method == 'POST':
        data = {
            "name": request.form.get('name'), "logo": request.form.get('logo'),
            "fb": request.form.get('fb'), "whatsapp": request.form.get('whatsapp'),
            "dmca": request.form.get('dmca'), "pass": request.form.get('pass'),
            "privacy": request.form.get('privacy'), "copyright": request.form.get('copyright'),
            "theme": request.form.get('theme'), "footer_text": request.form.get('footer_text')
        }
        settings_col.update_one({"id": "config"}, {"$set": data})
        return redirect('/admin/settings')

    html = f"""
    <h2 class="text-2xl font-bold mb-6">Site Configuration</h2>
    <form method="POST" class="bg-white p-8 rounded-2xl shadow grid grid-cols-1 md:grid-cols-2 gap-4">
        <div><label>Site Name</label><input name="name" value="{{{{ settings.name }}}}" class="w-full border p-2"></div>
        <div><label>Brand Logo URL</label><input name="logo" value="{{{{ settings.logo }}}}" class="w-full border p-2"></div>
        <div><label>WhatsApp Num</label><input name="whatsapp" value="{{{{ settings.whatsapp }}}}" class="w-full border p-2"></div>
        <div><label>Facebook URL</label><input name="fb" value="{{{{ settings.fb }}}}" class="w-full border p-2"></div>
        <div><label>Admin Password</label><input name="pass" value="{{{{ settings.pass }}}}" class="w-full border p-2"></div>
        <div><label>Select Theme Color</label>
            <select name="theme" class="w-full border p-2">
                <option value="orange">Orange</option><option value="blue">Blue</option><option value="red">Red</option><option value="green">Green</option>
            </select>
        </div>
        <div class="col-span-2"><label>Footer Header Text</label><input name="footer_text" value="{{{{ settings.footer_text }}}}" class="w-full border p-2"></div>
        <div class="col-span-2"><label>Privacy Policy</label><textarea name="privacy" class="w-full border p-2">{{{{ settings.privacy }}}}</textarea></div>
        <div class="col-span-2"><label>DMCA & Copyright</label><input name="dmca" value="{{{{ settings.dmca }}}}" class="w-full border p-2"></div>
        <button class="col-span-2 bg-slate-900 text-white py-3 rounded">Save Settings</button>
    </form>
    """
    return render_template_string(ADMIN_LAYOUT, settings=settings, content=render_template_string(html, settings=settings))

@app.route('/admin/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
