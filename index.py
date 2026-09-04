from flask import Flask, render_template_string, request, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)

# --- আপনার মংগোডিবি কানেকশন ---
MONGO_URI = "mongodb+srv://akash:akash@cluster0.hjyqogc.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['food_business'] # ডাটাবেস নাম

# কালেকশনগুলো
settings_col = db['settings']
foods_col = db['foods']
categories_col = db['categories']

# সাইট লোড হওয়ার সময় ডিফল্ট ডাটা চেক করা
def get_site_settings():
    conf = settings_col.find_one({"id": "config"})
    if not conf:
        default_conf = {
            "id": "config",
            "site_name": "My Restaurant",
            "site_logo": "https://cdn-icons-png.flaticon.com/512/706/706164.png",
            "dmca_text": "© 2024 All Rights Reserved",
            "fb_url": "https://facebook.com",
            "whatsapp_num": "01700000000"
        }
        settings_col.insert_one(default_conf)
        return default_conf
    return conf

# --- HTML CSS & JS (সব এক জায়গায়) ---
HEAD_HTML = """
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<script src="https://cdn.tailwindcss.com"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css"/>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@400;600&display=swap');
    body { font-family: 'Hind Siliguri', sans-serif; background: #f3f4f6; }
    .glass { background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(10px); }
    .sidebar-link:hover { background: #374151; border-radius: 8px; }
</style>
"""

# ইউজার প্যানেল টেমপ্লেট
USER_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <title>{{ settings.site_name }}</title>
    """ + HEAD_HTML + """
</head>
<body>
    <!-- Navbar -->
    <nav class="glass sticky top-0 z-50 shadow-sm p-3 flex items-center animate__animated animate__fadeInDown">
        <div class="flex-1">
            <img src="{{ settings.site_logo }}" class="w-10 h-10 rounded-full shadow-md">
        </div>
        <div class="flex-1 text-center">
            <h1 class="text-xl font-bold text-orange-600">{{ settings.site_name }}</h1>
        </div>
        <div class="flex-1 text-right">
            <a href="/admin" class="text-sm text-gray-500"><i class="fas fa-user-shield"></i> Admin</a>
        </div>
    </nav>

    <!-- Categories -->
    <div class="p-4 flex gap-2 overflow-x-auto no-scrollbar animate__animated animate__fadeIn">
        <a href="/" class="bg-orange-500 text-white px-4 py-2 rounded-full whitespace-nowrap">All Items</a>
        {% for cat in categories %}
        <a href="/?cat={{ cat.name }}" class="bg-white px-4 py-2 rounded-full shadow-sm whitespace-nowrap">{{ cat.name }}</a>
        {% endfor %}
    </div>

    <!-- Food Grid -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 p-4">
        {% for food in foods %}
        <div class="bg-white rounded-2xl shadow-md overflow-hidden animate__animated animate__zoomIn">
            <img src="{{ food.image }}" class="w-full h-40 object-cover">
            <div class="p-3 text-center">
                <h3 class="font-semibold text-gray-800">{{ food.name }}</h3>
                <p class="text-orange-600 font-bold">৳{{ food.price }}</p>
                <a href="https://wa.me/{{ settings.whatsapp_num }}?text=Hello, I want to order {{ food.name }}" 
                   class="mt-2 block bg-green-500 text-white py-2 rounded-xl text-sm font-bold">
                   <i class="fab fa-whatsapp"></i> Order Now
                </a>
            </div>
        </div>
        {% endfor %}
    </div>

    <!-- Footer -->
    <footer class="mt-10 p-6 bg-white text-center border-t">
        <p class="text-gray-500 text-sm">{{ settings.dmca_text }}</p>
        <div class="flex justify-center gap-5 mt-4">
            <a href="{{ settings.fb_url }}" class="text-blue-600 text-2xl"><i class="fab fa-facebook"></i></a>
            <a href="https://wa.me/{{ settings.whatsapp_num }}" class="text-green-500 text-2xl"><i class="fab fa-whatsapp"></i></a>
        </div>
    </footer>
</body>
</html>
"""

# এডমিন প্যানেল টেমপ্লেট
ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Admin Panel</title>
    """ + HEAD_HTML + """
</head>
<body class="flex flex-col md:flex-row">
    <!-- Sidebar -->
    <div class="w-full md:w-64 bg-slate-900 text-white min-h-screen p-5">
        <h2 class="text-2xl font-bold text-orange-400 mb-8 border-b border-gray-700 pb-2">Admin Panel</h2>
        <nav class="space-y-2">
            <a href="/admin" class="block p-3 sidebar-link"><i class="fas fa-chart-line mr-2"></i> Dashboard</a>
            <a href="/admin/add-food" class="block p-3 sidebar-link"><i class="fas fa-utensils mr-2"></i> Add Food</a>
            <a href="/admin/add-category" class="block p-3 sidebar-link"><i class="fas fa-tags mr-2"></i> Add Category</a>
            <a href="/admin/settings" class="block p-3 sidebar-link"><i class="fas fa-tools mr-2"></i> Site Settings</a>
            <a href="/" class="block p-3 sidebar-link text-blue-400"><i class="fas fa-external-link-alt mr-2"></i> View Site</a>
        </nav>
    </div>

    <!-- Main Content -->
    <div class="flex-1 p-6 md:p-10">
        {% if page == 'dashboard' %}
        <h1 class="text-3xl font-bold mb-6">Dashboard Overview</h1>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 text-white">
            <div class="bg-blue-600 p-8 rounded-2xl shadow-lg">
                <p class="text-lg">Total Foods</p>
                <h2 class="text-4xl font-bold">{{ f_count }}</h2>
            </div>
            <div class="bg-purple-600 p-8 rounded-2xl shadow-lg">
                <p class="text-lg">Categories</p>
                <h2 class="text-4xl font-bold">{{ c_count }}</h2>
            </div>
        </div>

        {% elif page == 'add-food' %}
        <h1 class="text-3xl font-bold mb-6">Add New Food Item</h1>
        <form action="/admin/add-food" method="POST" class="max-w-lg bg-white p-6 rounded-2xl shadow-lg space-y-4">
            <input type="text" name="name" placeholder="Food Name" class="w-full border p-3 rounded-lg" required>
            <input type="number" name="price" placeholder="Price" class="w-full border p-3 rounded-lg" required>
            <input type="text" name="image" placeholder="Image URL" class="w-full border p-3 rounded-lg" required>
            <button class="w-full bg-orange-500 text-white py-3 rounded-lg font-bold">Save Food</button>
        </form>

        {% elif page == 'add-category' %}
        <h1 class="text-3xl font-bold mb-6">Manage Categories</h1>
        <form action="/admin/add-category" method="POST" class="max-w-lg bg-white p-6 rounded-2xl shadow-lg flex gap-2">
            <input type="text" name="cat_name" placeholder="Category Name" class="flex-1 border p-3 rounded-lg" required>
            <button class="bg-blue-600 text-white px-6 py-3 rounded-lg font-bold">Add</button>
        </form>

        {% elif page == 'settings' %}
        <h1 class="text-3xl font-bold mb-6">Site Configuration</h1>
        <form action="/admin/settings" method="POST" class="max-w-xl bg-white p-6 rounded-2xl shadow-lg space-y-4">
            <div><label class="text-sm font-bold">Site Name</label><input type="text" name="site_name" value="{{ settings.site_name }}" class="w-full border p-3 rounded-lg"></div>
            <div><label class="text-sm font-bold">Logo URL</label><input type="text" name="site_logo" value="{{ settings.site_logo }}" class="w-full border p-3 rounded-lg"></div>
            <div><label class="text-sm font-bold">DMCA/Footer Text</label><input type="text" name="dmca_text" value="{{ settings.dmca_text }}" class="w-full border p-3 rounded-lg"></div>
            <div><label class="text-sm font-bold">Facebook URL</label><input type="text" name="fb_url" value="{{ settings.fb_url }}" class="w-full border p-3 rounded-lg"></div>
            <div><label class="text-sm font-bold">WhatsApp Number (Ex: 88017...)</label><input type="text" name="whatsapp_num" value="{{ settings.whatsapp_num }}" class="w-full border p-3 rounded-lg"></div>
            <button class="w-full bg-slate-900 text-white py-3 rounded-lg font-bold">Update All Settings</button>
        </form>
        {% endif %}
    </div>
</body>
</html>
"""

# --- ROUTES ---

@app.route('/')
def index():
    settings = get_site_settings()
    foods = list(foods_col.find())
    categories = list(categories_col.find())
    return render_template_string(USER_TEMPLATE, settings=settings, foods=foods, categories=categories)

@app.route('/admin')
def admin_home():
    f_count = foods_col.count_documents({})
    c_count = categories_col.count_documents({})
    return render_template_string(ADMIN_TEMPLATE, page='dashboard', f_count=f_count, c_count=c_count)

@app.route('/admin/add-food', methods=['GET', 'POST'])
def admin_add_food():
    if request.method == 'POST':
        foods_col.insert_one({
            "name": request.form.get('name'),
            "price": request.form.get('price'),
            "image": request.form.get('image')
        })
        return redirect('/admin')
    return render_template_string(ADMIN_TEMPLATE, page='add-food')

@app.route('/admin/add-category', methods=['GET', 'POST'])
def admin_add_cat():
    if request.method == 'POST':
        categories_col.insert_one({"name": request.form.get('cat_name')})
        return redirect('/admin')
    return render_template_string(ADMIN_TEMPLATE, page='add-category')

@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    if request.method == 'POST':
        updated_data = {
            "site_name": request.form.get('site_name'),
            "site_logo": request.form.get('site_logo'),
            "dmca_text": request.form.get('dmca_text'),
            "fb_url": request.form.get('fb_url'),
            "whatsapp_num": request.form.get('whatsapp_num'),
        }
        settings_col.update_one({"id": "config"}, {"$set": updated_data})
        return redirect('/admin/settings')
    
    settings = get_site_settings()
    return render_template_string(ADMIN_TEMPLATE, page='settings', settings=settings)

if __name__ == '__main__':
    app.run(debug=True)
