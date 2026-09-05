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
    .cart-float { position: fixed; bottom: 20px; right: 20px; z-index: 100; }
</style>
<script>
    let cart = JSON.parse(localStorage.getItem('my_cart')) || [];
    function updateBadge() {
        let badges = document.querySelectorAll('.cart-count');
        badges.forEach(b => b.innerText = cart.length);
    }
    window.onload = updateBadge;
</script>
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
            <div class="flex items-center gap-4">
                <a href="/cart" class="relative text-gray-700 text-2xl">
                    <i class="fas fa-shopping-cart"></i>
                    <span class="cart-count absolute -top-2 -right-2 bg-red-500 text-white text-[10px] w-5 h-5 flex items-center justify-center rounded-full">0</span>
                </a>
                <a href="https://wa.me/{{ wa_clean }}" class="text-green-500 text-2xl md:text-3xl"><i class="fab fa-whatsapp"></i></a>
            </div>
        </nav>

        <div class="p-4 md:px-8">
            <div class="relative max-w-2xl mx-auto mt-4">
                <input type="text" id="catSearch" onkeyup="searchCat()" placeholder="খুঁজুন আপনার পছন্দের খাবার ক্যাটাগরি..." class="w-full p-4 pl-12 rounded-2xl border-none shadow-md outline-none focus:ring-2 focus:ring-{{ settings.theme }}-500">
                <i class="fas fa-search absolute left-4 top-5 text-gray-400"></i>
            </div>
        </div>

        <div class="p-4">
            <div class="bg-{{ settings.theme }}-600 rounded-[30px] p-8 md:p-16 text-white shadow-lg relative overflow-hidden text-center">
                <h2 class="text-2xl md:text-5xl font-black relative z-10 leading-tight">{{ settings.header_text }}</h2>
                <i class="fas fa-pizza-slice absolute -right-6 -bottom-6 text-8xl md:text-[200px] opacity-10 rotate-12"></i>
            </div>
        </div>

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
                </a>
                {% endfor %}
            </div>
        </div>

        <a href="/cart" class="cart-float bg-orange-600 text-white w-14 h-14 rounded-full flex items-center justify-center shadow-2xl">
            <i class="fas fa-shopping-cart"></i>
            <span class="cart-count absolute top-0 right-0 bg-red-600 text-[10px] w-5 h-5 rounded-full flex items-center justify-center">0</span>
        </a>

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
        <nav class="glass sticky top-0 z-50 px-4 py-3 flex items-center justify-between border-b">
            <div class="flex items-center gap-4">
                <a href="/" class="bg-gray-100 w-10 h-10 flex items-center justify-center rounded-full"><i class="fas fa-arrow-left"></i></a>
                <h1 class="text-xl font-bold">{{ name }}</h1>
            </div>
            <a href="/cart" class="relative text-2xl"><i class="fas fa-shopping-cart text-gray-700"></i><span class="cart-count absolute -top-2 -right-2 bg-red-500 text-white text-[10px] w-5 h-5 flex items-center justify-center rounded-full">0</span></a>
        </nav>

        <div class="p-4 md:p-8 grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4 md:gap-8">
            {% for food in foods %}
            <a href="/food/{{ food._id }}" class="bg-white rounded-2xl p-3 md:p-5 shadow-sm hover:shadow-xl transition-all border animate__animated animate__fadeIn">
                <img src="{{ food.image }}" class="rounded-xl object-cover w-full h-40 md:h-56">
                <h4 class="text-sm md:text-xl font-bold mt-4 text-gray-800 truncate">{{ food.name }}</h4>
                <div class="flex justify-between items-center mt-2">
                    <span class="text-{{ settings.theme }}-600 font-black md:text-xl">৳{{ food.price }}</span>
                    <i class="fas fa-plus-circle text-orange-500"></i>
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
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>"""+HEAD+"""<title>{{ food.name }}</title></head>
    <body class="bg-gray-50 pb-24">
        <div class="max-w-4xl mx-auto bg-white min-h-screen shadow-lg relative">
            <a href="/category/{{ food.category }}" class="absolute top-4 left-4 z-50 bg-white/80 p-3 rounded-2xl shadow-xl border"><i class="fas fa-chevron-left"></i></a>
            <div class="h-64 md:h-[500px]"><img src="{{ food.image }}" class="w-full h-full object-cover"></div>
            <div class="p-6 md:p-12 -mt-10 bg-white rounded-t-[40px] relative z-10">
                <h1 class="text-3xl md:text-6xl font-black text-gray-900">{{ food.name }}</h1>
                <p class="text-3xl md:text-4xl font-black text-orange-600 mt-4">৳{{ food.price }}</p>

                <div class="grid grid-cols-4 gap-3 my-8">
                    {% for ss in food.screenshots %} <img src="{{ ss }}" class="w-full aspect-square rounded-xl object-cover border"> {% endfor %}
                </div>

                <div class="bg-gray-50 p-6 rounded-[30px] border flex items-center justify-between mb-8">
                    <span class="font-bold">Quantity</span>
                    <div class="flex items-center gap-6">
                        <button onclick="changeQty(-1)" class="w-12 h-12 bg-white rounded-2xl border flex items-center justify-center"><i class="fas fa-minus"></i></button>
                        <span id="qty" class="text-2xl font-black">1</span>
                        <button onclick="changeQty(1)" class="w-12 h-12 bg-orange-600 text-white rounded-2xl flex items-center justify-center"><i class="fas fa-plus"></i></button>
                    </div>
                </div>

                {% if food.addons %}
                <div class="mb-8">
                    <h4 class="font-bold text-green-600 mb-4">Extras (Add-ons)</h4>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {% for opt in food.addons %}
                        <label class="flex items-center gap-4 p-4 bg-gray-50 rounded-2xl border cursor-pointer"><input type="checkbox" name="addon" value="{{ opt }}" class="w-6 h-6 accent-green-600"> <span class="font-bold">{{ opt }}</span></label>
                        {% endfor %}
                    </div>
                </div>
                {% endif %}

                {% if food.exclusions %}
                <div class="mb-8">
                    <h4 class="font-bold text-red-600 mb-4">Without (Exclusions)</h4>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {% for opt in food.exclusions %}
                        <label class="flex items-center gap-4 p-4 bg-gray-50 rounded-2xl border cursor-pointer"><input type="checkbox" name="exclusion" value="{{ opt }}" class="w-6 h-6 accent-red-600"> <span class="font-bold">{{ opt }}</span></label>
                        {% endfor %}
                    </div>
                </div>
                {% endif %}

                <button onclick="addToCart()" class="fixed bottom-4 left-4 right-4 max-w-4xl mx-auto bg-black text-white py-5 rounded-[25px] font-black text-xl shadow-2xl flex items-center justify-center gap-4">
                    <i class="fas fa-cart-plus"></i> Add To Cart
                </button>
            </div>
        </div>
        <script>
            let currentQty = 1;
            function changeQty(v) { currentQty = Math.max(1, currentQty + v); document.getElementById('qty').innerText = currentQty; }
            function addToCart() {
                let addons = Array.from(document.querySelectorAll('input[name="addon"]:checked')).map(e => e.value);
                let exclusions = Array.from(document.querySelectorAll('input[name="exclusion"]:checked')).map(e => e.value);
                let item = {
                    name: "{{ food.name }}", price: {{ food.price }}, qty: currentQty,
                    addons: addons, exclusions: exclusions, img: "{{ food.image }}"
                };
                cart.push(item);
                localStorage.setItem('my_cart', JSON.stringify(cart));
                updateBadge();
                alert('কার্টে যোগ হয়েছে!');
            }
        </script>
    </body>
    </html>
    """, food=food, settings=settings)

@app.route('/cart')
def cart_page():
    settings = get_site_settings()
    wa_num = settings['whatsapp'].replace('+', '').replace(' ', '').replace('-', '')
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>"""+HEAD+"""<title>My Cart</title></head>
    <body class="bg-white pb-32">
        <nav class="glass sticky top-0 z-50 px-4 py-3 border-b flex items-center gap-4">
            <a href="/" class="bg-gray-100 w-10 h-10 flex items-center justify-center rounded-full"><i class="fas fa-arrow-left"></i></a>
            <h1 class="text-xl font-bold">আমার কার্ট</h1>
        </nav>
        <div id="cartList" class="p-4 space-y-4"></div>
        <div class="fixed bottom-0 left-0 right-0 p-6 bg-white border-t shadow-2xl">
            <div class="flex justify-between text-xl font-black mb-4"><span>Total:</span> <span id="totalPrice">৳0</span></div>
            <button onclick="sendOrder()" class="w-full bg-green-500 text-white py-5 rounded-2xl font-black flex items-center justify-center gap-3"><i class="fab fa-whatsapp text-2xl"></i> Order Now</button>
        </div>
        <script>
            function renderCart() {
                let list = document.getElementById('cartList');
                let total = 0;
                list.innerHTML = cart.length ? '' : '<p class="text-center py-10 text-gray-400">কার্ট খালি</p>';
                cart.forEach((item, i) => {
                    total += item.price * item.qty;
                    list.innerHTML += `
                        <div class="flex gap-4 bg-gray-50 p-4 rounded-2xl border relative">
                            <img src="${item.img}" class="w-20 h-20 rounded-xl object-cover">
                            <div class="flex-1">
                                <h4 class="font-bold">${item.name}</h4>
                                <p class="text-orange-600">৳${item.price} x ${item.qty}</p>
                                <p class="text-[10px] text-gray-400">${item.addons.join(', ')}</p>
                            </div>
                            <button onclick="remove(${i})" class="text-red-500"><i class="fas fa-trash"></i></button>
                        </div>`;
                });
                document.getElementById('totalPrice').innerText = '৳' + total;
            }
            function remove(i) { cart.splice(i, 1); localStorage.setItem('my_cart', JSON.stringify(cart)); renderCart(); updateBadge(); }
            function sendOrder() {
                if(!cart.length) return alert('কার্ট খালি!');
                let msg = "*NEW ORDER*%0A------------------%0A";
                let total = 0;
                cart.forEach((item, i) => {
                    msg += `${i+1}. *${item.name}* (x${item.qty})%0APrice: ${item.price * item.qty}%0A`;
                    if(item.addons.length) msg += `Extras: ${item.addons.join(', ')}%0A`;
                    total += item.price * item.qty;
                    msg += `%0A`;
                });
                msg += `------------------%0A*Total: ৳${total}*`;
                window.location.href = `https://wa.me/{{ wa_num }}?text=${msg}`;
                localStorage.removeItem('my_cart');
            }
            renderCart();
        </script>
    </body>
    </html>
    """, wa_num=wa_num)

# --- ADMIN PANEL ---

@app.route('/admin/dash')
def admin_dash():
    if not session.get('admin_logged'): return render_template_string("""
        <head>"""+HEAD+"""</head>
        <body class="flex items-center justify-center min-h-screen bg-gray-100">
            <form action="/admin/login" method="POST" class="bg-white p-10 rounded-[40px] shadow-xl w-full max-w-sm text-center">
                <h2 class="text-2xl font-black mb-6">Admin Login</h2>
                <input type="password" name="pass" placeholder="Password" class="w-full p-4 bg-gray-100 rounded-2xl mb-4 outline-none text-center">
                <button class="w-full bg-black text-white py-4 rounded-2xl font-bold">Login</button>
            </form>
        </body>
    """)
    total_foods = foods_col.count_documents({})
    total_cats = cats_col.count_documents({})
    total_views = views_col.count_documents({})
    return render_template_string("""
    <head>"""+HEAD+"""<title>Dashboard</title></head>
    <body class="flex flex-col lg:flex-row min-h-screen bg-gray-50">
        <div class="w-full lg:w-72 bg-gray-900 text-white p-6 space-y-4">
            <h2 class="text-2xl font-bold mb-8">Admin</h2>
            <a href="/admin/dash" class="block p-4 bg-orange-600 rounded-xl">Dashboard</a>
            <a href="/admin/manage-foods" class="block p-4 hover:bg-gray-800 rounded-xl">Manage Foods</a>
            <a href="/admin/add-cat" class="block p-4 hover:bg-gray-800 rounded-xl">Categories</a>
            <a href="/admin/manage-options" class="block p-4 hover:bg-gray-800 rounded-xl">Options</a>
            <a href="/admin/settings" class="block p-4 hover:bg-gray-800 rounded-xl">Settings</a>
            <a href="/admin/logout" class="block p-4 text-red-400">Logout</a>
        </div>
        <div class="flex-1 p-8">
            <h2 class="text-3xl font-black mb-10">Statistics</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div class="bg-white p-8 rounded-3xl shadow-sm border">
                    <p class="text-gray-400 uppercase text-xs font-bold">Total Views</p>
                    <h3 class="text-5xl font-black">{{ total_views }}</h3>
                </div>
                <div class="bg-white p-8 rounded-3xl shadow-sm border">
                    <p class="text-gray-400 uppercase text-xs font-bold">Foods</p>
                    <h3 class="text-5xl font-black text-orange-500">{{ total_foods }}</h3>
                </div>
                <div class="bg-white p-8 rounded-3xl shadow-sm border">
                    <p class="text-gray-400 uppercase text-xs font-bold">Categories</p>
                    <h3 class="text-5xl font-black text-blue-500">{{ total_cats }}</h3>
                </div>
            </div>
        </div>
    </body>
    """, total_foods=total_foods, total_cats=total_cats, total_views=total_views)

@app.route('/admin/manage-foods')
def admin_manage_foods():
    if not session.get('admin_logged'): return redirect('/admin/dash')
    all_foods = list(foods_col.find())
    all_cats = list(cats_col.find())
    return render_template_string("""
    <head>"""+HEAD+"""<title>Manage Foods</title></head>
    <body class="p-8 bg-gray-50">
        <div class="flex justify-between items-center mb-10">
            <h2 class="text-3xl font-black">Food Management</h2>
            <a href="/admin/add-food" class="bg-black text-white px-6 py-2 rounded-xl">+ Add New</a>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
            <input type="text" id="fSearch" onkeyup="filterFoods()" placeholder="Search food..." class="p-4 rounded-2xl border shadow-sm outline-none">
            <select id="fCat" onchange="filterFoods()" class="p-4 rounded-2xl border shadow-sm outline-none">
                <option value="">All Categories</option>
                {% for c in cats %} <option value="{{ c.name }}">{{ c.name }}</option> {% endfor %}
            </select>
        </div>
        <div id="foodGrid" class="grid grid-cols-1 md:grid-cols-3 gap-6">
            {% for f in foods %}
            <div class="food-card-admin bg-white p-4 rounded-3xl border shadow-sm" data-name="{{ f.name.lower() }}" data-cat="{{ f.category }}">
                <img src="{{ f.image }}" class="w-full h-32 object-cover rounded-2xl mb-4">
                <h4 class="font-bold">{{ f.name }}</h4>
                <p class="text-sm text-gray-400 mb-4">{{ f.category }} | ৳{{ f.price }}</p>
                <div class="flex gap-2">
                    <a href="/admin/edit-food/{{ f._id }}" class="flex-1 bg-blue-100 text-blue-600 py-2 rounded-lg text-center font-bold">Edit</a>
                    <a href="/admin/del-food/{{ f._id }}" class="bg-red-100 text-red-600 px-4 py-2 rounded-lg" onclick="return confirm('Delete?')"><i class="fas fa-trash"></i></a>
                </div>
            </div>
            {% endfor %}
        </div>
        <script>
            function filterFoods() {
                let s = document.getElementById('fSearch').value.toLowerCase();
                let c = document.getElementById('fCat').value;
                let cards = document.getElementsByClassName('food-card-admin');
                for(let card of cards) {
                    let nameMatch = card.dataset.name.includes(s);
                    let catMatch = c === "" || card.dataset.cat === c;
                    card.style.display = (nameMatch && catMatch) ? "block" : "none";
                }
            }
        </script>
    </body>
    """, foods=all_foods, cats=all_cats)

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
    return render_template_string("""
    <head>"""+HEAD+"""</head>
    <body class="p-8 bg-gray-50">
        <form method="POST" class="max-w-2xl mx-auto bg-white p-8 rounded-3xl shadow-sm border space-y-4">
            <h2 class="text-2xl font-black mb-4">Add Food</h2>
            <input name="name" placeholder="Food Name" class="w-full border p-4 rounded-xl" required>
            <input name="price" placeholder="Price" class="w-full border p-4 rounded-xl" required>
            <input name="image" placeholder="Image URL" class="w-full border p-4 rounded-xl" required>
            <select name="category" class="w-full border p-4 rounded-xl">
                {% for c in cats %} <option value="{{ c.name }}">{{ c.name }}</option> {% endfor %}
            </select>
            <textarea name="screenshots" placeholder="Screenshots (comma separated)" class="w-full border p-4 rounded-xl"></textarea>
            <div class="grid grid-cols-2 gap-4">
                <div class="border p-4 rounded-xl">
                    <p class="font-bold mb-2">Addons</p>
                    {% for o in opts if o.type == 'addon' %} <label class="block"><input type="checkbox" name="addons" value="{{ o.name }}"> {{ o.name }}</label> {% endfor %}
                </div>
                <div class="border p-4 rounded-xl">
                    <p class="font-bold mb-2">Exclusions</p>
                    {% for o in opts if o.type == 'exclusion' %} <label class="block"><input type="checkbox" name="exclusions" value="{{ o.name }}"> {{ o.name }}</label> {% endfor %}
                </div>
            </div>
            <textarea name="details" placeholder="Details" class="w-full border p-4 rounded-xl h-32"></textarea>
            <button class="w-full bg-black text-white py-4 rounded-xl font-bold">Publish</button>
        </form>
    </body>
    """, cats=list(cats_col.find()), opts=list(options_col.find()))

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
    return render_template_string("""
    <head>"""+HEAD+"""</head>
    <body class="p-8 bg-gray-50">
        <form method="POST" class="max-w-2xl mx-auto bg-white p-8 rounded-3xl shadow-sm border space-y-4">
            <h2 class="text-2xl font-black mb-4">Edit Food</h2>
            <input name="name" value="{{ f.name }}" class="w-full border p-4 rounded-xl" required>
            <input name="price" value="{{ f.price }}" class="w-full border p-4 rounded-xl" required>
            <input name="image" value="{{ f.image }}" class="w-full border p-4 rounded-xl" required>
            <select name="category" class="w-full border p-4 rounded-xl">
                {% for c in cats %} <option value="{{ c.name }}" {% if c.name == f.category %}selected{% endif %}>{{ c.name }}</option> {% endfor %}
            </select>
            <textarea name="screenshots" class="w-full border p-4 rounded-xl">{{ f.screenshots | join(',') }}</textarea>
            <textarea name="details" class="w-full border p-4 rounded-xl h-32">{{ f.details }}</textarea>
            <button class="w-full bg-blue-600 text-white py-4 rounded-xl font-bold">Update Food</button>
        </form>
    </body>
    """, f=food, cats=list(cats_col.find()))

@app.route('/admin/add-cat', methods=['GET', 'POST'])
def admin_add_cat():
    if not session.get('admin_logged'): return redirect('/admin/dash')
    if request.method == 'POST':
        cats_col.insert_one({"name": request.form.get('name'), "logo": request.form.get('logo')})
    categories = list(cats_col.find())
    return render_template_string("""
    <head>"""+HEAD+"""</head>
    <body class="p-8 bg-gray-50">
        <div class="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-10">
            <form method="POST" class="bg-white p-8 rounded-3xl border h-fit">
                <h3 class="text-xl font-black mb-4">Create Category</h3>
                <input name="name" placeholder="Name" class="w-full border p-4 rounded-xl mb-4" required>
                <input name="logo" placeholder="Logo URL" class="w-full border p-4 rounded-xl mb-4" required>
                <button class="w-full bg-black text-white py-4 rounded-xl">Save</button>
            </form>
            <div class="bg-white p-8 rounded-3xl border">
                {% for c in cats %}
                <div class="flex justify-between py-3 border-b">
                    <span>{{ c.name }}</span>
                    <div class="flex gap-4">
                        <a href="/admin/edit-cat/{{ c._id }}" class="text-blue-500"><i class="fas fa-edit"></i></a>
                        <a href="/admin/del-cat/{{ c._id }}" class="text-red-500"><i class="fas fa-trash"></i></a>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </body>
    """, cats=categories)

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
        <form method="POST" class="max-w-md mx-auto bg-white p-8 rounded-3xl border">
            <h3 class="font-black mb-4">Edit Category</h3>
            <input name="name" value="{{ c.name }}" class="w-full border p-4 rounded-xl mb-4">
            <input name="logo" value="{{ c.logo }}" class="w-full border p-4 rounded-xl mb-4">
            <button class="w-full bg-blue-600 text-white py-4 rounded-xl">Update</button>
        </form>
    </body>
    """, c=cat)

@app.route('/admin/manage-options', methods=['GET', 'POST'])
def admin_manage_options():
    if not session.get('admin_logged'): return redirect('/admin/dash')
    if request.method == 'POST':
        options_col.insert_one({"name": request.form.get('name'), "type": request.form.get('type')})
    all_opts = list(options_col.find())
    return render_template_string("""
    <head>"""+HEAD+"""</head>
    <body class="p-8 bg-gray-50">
        <form method="POST" class="max-w-4xl mx-auto bg-white p-6 rounded-3xl border flex gap-4 mb-10">
            <input name="name" placeholder="Option Name" class="flex-1 border p-4 rounded-xl outline-none" required>
            <select name="type" class="border p-4 rounded-xl">
                <option value="addon">Add-on</option>
                <option value="exclusion">Exclusion</option>
            </select>
            <button class="bg-black text-white px-8 rounded-xl">Add</button>
        </form>
        <div class="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-8">
            <div class="bg-white p-6 rounded-3xl border">
                <h3 class="font-bold text-green-600 mb-4">Addons</h3>
                {% for o in opts if o.type == 'addon' %}
                <div class="flex justify-between py-2 border-b"><span>{{ o.name }}</span> <a href="/admin/del-opt/{{ o._id }}" class="text-red-400"><i class="fas fa-trash"></i></a></div>
                {% endfor %}
            </div>
            <div class="bg-white p-6 rounded-3xl border">
                <h3 class="font-bold text-red-600 mb-4">Exclusions</h3>
                {% for o in opts if o.type == 'exclusion' %}
                <div class="flex justify-between py-2 border-b"><span>{{ o.name }}</span> <a href="/admin/del-opt/{{ o._id }}" class="text-red-400"><i class="fas fa-trash"></i></a></div>
                {% endfor %}
            </div>
        </div>
    </body>
    """, opts=all_opts)

@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    if not session.get('admin_logged'): return redirect('/admin/dash')
    s = get_site_settings()
    if request.method == 'POST':
        settings_col.update_one({"id": "config"}, {"$set": {
            "name": request.form.get('name'), "logo": request.form.get('logo'),
            "whatsapp": request.form.get('whatsapp'), "pass": request.form.get('pass'),
            "header_text": request.form.get('header_text'), "footer_text": request.form.get('footer_text')
        }})
        return redirect('/admin/dash')
    return render_template_string("""
    <head>"""+HEAD+"""</head>
    <body class="p-8 bg-gray-50">
        <form method="POST" class="max-w-2xl mx-auto bg-white p-10 rounded-[40px] shadow-sm border space-y-4">
            <h2 class="text-2xl font-black mb-4">Settings</h2>
            <input name="name" value="{{ s.name }}" class="w-full border p-4 rounded-xl">
            <input name="logo" value="{{ s.logo }}" class="w-full border p-4 rounded-xl">
            <input name="whatsapp" value="{{ s.whatsapp }}" class="w-full border p-4 rounded-xl">
            <input name="pass" value="{{ s.pass }}" class="w-full border p-4 rounded-xl">
            <input name="header_text" value="{{ s.header_text }}" class="w-full border p-4 rounded-xl">
            <button class="w-full bg-black text-white py-4 rounded-xl font-bold">Apply Changes</button>
        </form>
    </body>
    """, s=s)

@app.route('/admin/login', methods=['POST'])
def admin_login_post():
    settings = get_site_settings()
    if request.form.get('pass') == settings['pass']: session['admin_logged'] = True
    return redirect('/admin/dash')

@app.route('/admin/logout')
def admin_logout(): session.clear(); return redirect('/')

@app.route('/admin/del-food/<id>')
def del_food(id):
    if not session.get('admin_logged'): return redirect('/admin/dash')
    foods_col.delete_one({"_id": ObjectId(id)})
    return redirect('/admin/manage-foods')

@app.route('/admin/del-cat/<id>')
def del_cat(id):
    if not session.get('admin_logged'): return redirect('/admin/dash')
    cats_col.delete_one({"_id": ObjectId(id)})
    return redirect('/admin/add-cat')

@app.route('/admin/del-opt/<id>')
def del_opt(id):
    if not session.get('admin_logged'): return redirect('/admin/dash')
    options_col.delete_one({"_id": ObjectId(id)})
    return redirect('/admin/manage-options')

if __name__ == '__main__':
    app.run(debug=True)
