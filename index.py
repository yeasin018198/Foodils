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
<script>
    let cart = JSON.parse(localStorage.getItem('my_cart')) || [];
    function updateCartBadge() {
        let counts = document.querySelectorAll('.cart-count-badge');
        counts.forEach(el => el.innerText = cart.length);
    }
    window.onload = updateCartBadge;
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
                    <span class="cart-count-badge absolute -top-2 -right-2 bg-red-500 text-white text-[10px] w-5 h-5 flex items-center justify-center rounded-full">0</span>
                </a>
                <a href="https://wa.me/{{ wa_clean }}" class="text-green-500 text-2xl md:text-3xl"><i class="fab fa-whatsapp"></i></a>
            </div>
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

        <!-- Categories -->
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

        <a href="/cart" class="fixed bottom-6 right-6 bg-{{ settings.theme }}-600 text-white w-16 h-16 rounded-full shadow-2xl flex items-center justify-center text-2xl z-50 animate__animated animate__bounceIn">
            <i class="fas fa-shopping-cart"></i>
            <span class="cart-count-badge absolute top-0 right-0 bg-red-600 text-xs w-6 h-6 flex items-center justify-center rounded-full border-2 border-white">0</span>
        </a>

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
        <nav class="glass sticky top-0 z-50 px-4 py-3 flex items-center justify-between border-b">
            <div class="flex items-center gap-4">
                <a href="/" class="bg-gray-100 w-10 h-10 flex items-center justify-center rounded-full"><i class="fas fa-arrow-left"></i></a>
                <h1 class="text-xl font-bold">{{ name }} আইটেমসমূহ</h1>
            </div>
            <a href="/cart" class="relative text-2xl text-gray-700">
                <i class="fas fa-shopping-cart"></i>
                <span class="cart-count-badge absolute -top-2 -right-2 bg-red-500 text-white text-[10px] w-5 h-5 flex items-center justify-center rounded-full">0</span>
            </a>
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
            <a href="/category/{{ food.category }}" class="absolute top-4 left-4 z-50 bg-white/80 p-3 rounded-2xl shadow-xl border">
                <i class="fas fa-chevron-left"></i> Back
            </a>

            <div class="h-64 md:h-[500px]"><img src="{{ food.image }}" class="w-full h-full object-cover"></div>
            
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

                <!-- Options -->
                {% if food.addons %}
                <div class="mb-8">
                    <h4 class="font-bold text-lg mb-4 text-green-600">Extras / কুল্লু সাই (Add-ons)</h4>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {% for opt in food.addons %}
                        <label class="flex items-center gap-4 p-4 bg-gray-50 rounded-2xl border cursor-pointer">
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
                        <label class="flex items-center gap-4 p-4 bg-gray-50 rounded-2xl border cursor-pointer">
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

                <button onclick="addToCart()" class="fixed bottom-4 left-4 right-4 max-w-4xl mx-auto bg-black text-white py-5 rounded-[25px] font-black text-xl shadow-2xl flex items-center justify-center gap-4">
                    <i class="fas fa-cart-plus text-3xl"></i> Add To Cart
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
                    id: "{{ food._id }}", name: "{{ food.name }}", price: {{ food.price }}, 
                    qty: currentQty, addons: addons, exclusions: exclusions, img: "{{ food.image }}"
                };
                cart.push(item);
                localStorage.setItem('my_cart', JSON.stringify(cart));
                updateCartBadge();
                alert('কার্টে যোগ করা হয়েছে!');
                window.location.href = "/category/{{ food.category }}";
            }
        </script>
    </body>
    </html>
    """, food=food, settings=settings)

@app.route('/cart')
def cart_view():
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
            <div class="flex justify-between text-xl font-black mb-4"><span>মোট বিল:</span> <span id="totalPrice">৳0</span></div>
            <button onclick="sendOrder()" class="w-full bg-green-500 text-white py-5 rounded-2xl font-black flex items-center justify-center gap-3 shadow-xl">
                <i class="fab fa-whatsapp text-2xl"></i> হোয়াটসঅ্যাপে অর্ডার দিন
            </button>
        </div>
        <script>
            function renderCart() {
                let list = document.getElementById('cartList');
                let total = 0;
                list.innerHTML = cart.length ? '' : '<div class="text-center py-20 text-gray-400"><i class="fas fa-shopping-basket text-5xl mb-4"></i><p>কার্ট খালি!</p></div>';
                cart.forEach((item, i) => {
                    total += item.price * item.qty;
                    list.innerHTML += `<div class="flex gap-4 bg-gray-50 p-4 rounded-2xl border relative">
                        <img src="${item.img}" class="w-20 h-20 rounded-xl object-cover">
                        <div class="flex-1"><h4 class="font-bold">${item.name}</h4><p class="text-orange-600 font-bold">৳${item.price} x ${item.qty}</p>
                        <p class="text-[10px] text-gray-400">${item.addons.join(', ')}</p></div>
                        <button onclick="remove(${i})" class="text-red-500 p-2"><i class="fas fa-trash-alt"></i></button></div>`;
                });
                document.getElementById('totalPrice').innerText = '৳' + total;
            }
            function remove(i) { cart.splice(i, 1); localStorage.setItem('my_cart', JSON.stringify(cart)); renderCart(); updateCartBadge(); }
            function sendOrder() {
                if(!cart.length) return alert('কার্ট খালি!');
                let msg = "*NEW ORDER*%0A------------------%0A";
                let total = 0;
                cart.forEach((item, i) => {
                    msg += `${i+1}. *${item.name}* (x${item.qty})%0A   ৳${item.price * item.qty}%0A`;
                    if(item.addons.length) msg += `   Extras: ${item.addons.join(', ')}%0A`;
                    if(item.exclusions.length) msg += `   Without: ${item.exclusions.join(', ')}%0A`;
                    total += item.price * item.qty;
                    msg += `%0A`;
                });
                msg += `------------------%0A*Total: ৳${total}*%0A_Delivery charge extra._`;
                window.location.href = `https://wa.me/{{ wa_num }}?text=${msg}`;
                localStorage.removeItem('my_cart');
            }
            renderCart();
        </script>
    </body>
    </html>
    """, wa_num=wa_num)

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
    total_foods = foods_col.count_documents({})
    total_cats = cats_col.count_documents({})
    total_views = views_col.count_documents({})
    
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>"""+HEAD+"""<title>Admin Dashboard</title></head>
    <body class="flex flex-col lg:flex-row min-h-screen bg-gray-50">
        <div class="w-full lg:w-80 bg-gray-900 text-white p-8">
            <h2 class="text-2xl font-bold mb-10">Foodils Admin</h2>
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
            <h2 class="text-3xl font-black mb-10">Statistics</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div class="bg-white p-8 rounded-[30px] border shadow-sm">
                    <p class="text-gray-400 font-bold uppercase text-xs">Total Views</p>
                    <h3 class="text-5xl font-black mt-2">{{ total_views }}</h3>
                </div>
                <div class="bg-white p-8 rounded-[30px] border shadow-sm">
                    <p class="text-gray-400 font-bold uppercase text-xs">Total Foods</p>
                    <h3 class="text-5xl font-black mt-2 text-orange-500">{{ total_foods }}</h3>
                </div>
                <div class="bg-white p-8 rounded-[30px] border shadow-sm">
                    <p class="text-gray-400 font-bold uppercase text-xs">Categories</p>
                    <h3 class="text-5xl font-black mt-2 text-blue-500">{{ total_cats }}</h3>
                </div>
            </div>
        </div>
    </body>
    </html>
    """, total_views=total_views, total_foods=total_foods, total_cats=total_cats)

@app.route('/admin/manage-foods')
def admin_manage_foods():
    if not session.get('admin_logged'): return redirect('/admin/dash')
    all_foods = list(foods_col.find())
    all_cats = list(cats_col.find())
    return render_template_string("""
    <head>"""+HEAD+"""<title>Manage Foods</title></head>
    <body class="bg-gray-50 p-6 md:p-12">
        <div class="max-w-6xl mx-auto">
            <div class="flex justify-between items-center mb-8">
                <h2 class="text-3xl font-black">সকল খাবারসমূহ</h2>
                <a href="/admin/dash" class="bg-gray-200 px-6 py-2 rounded-xl font-bold">Back</a>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
                <input type="text" id="foodSearch" onkeyup="filterFoods()" placeholder="খাবার খুঁজুন..." class="p-4 rounded-2xl border shadow-sm outline-none">
                <select id="catFilter" onchange="filterFoods()" class="p-4 rounded-2xl border shadow-sm outline-none">
                    <option value="">সকল ক্যাটাগরি</option>
                    {% for c in cats %} <option value="{{ c.name }}">{{ c.name }}</option> {% endfor %}
                </select>
            </div>

            <div id="foodGrid" class="grid grid-cols-1 md:grid-cols-3 gap-6">
                {% for f in foods %}
                <div class="food-item bg-white p-4 rounded-3xl border shadow-sm" data-name="{{ f.name.lower() }}" data-cat="{{ f.category }}">
                    <img src="{{ f.image }}" class="w-full h-32 object-cover rounded-2xl mb-4">
                    <h4 class="font-bold">{{ f.name }}</h4>
                    <p class="text-sm text-gray-400 mb-4">{{ f.category }} | ৳{{ f.price }}</p>
                    <div class="flex gap-2">
                        <a href="/admin/edit-food/{{ f._id }}" class="flex-1 bg-blue-100 text-blue-600 py-3 rounded-xl text-center font-bold">Edit</a>
                        <a href="/admin/del-food/{{ f._id }}" class="bg-red-100 text-red-600 px-4 py-3 rounded-xl" onclick="return confirm('Delete?')"><i class="fas fa-trash-alt"></i></a>
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
    
    categories = list(cats_col.find())
    all_options = list(options_col.find())
    return render_template_string("""
    <head>"""+HEAD+"""</head>
    <body class="p-8 bg-gray-50">
        <a href="/admin/dash" class="inline-block mb-6 bg-gray-200 px-6 py-2 rounded-xl font-bold">Back to Dash</a>
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
        <form method="POST" class="max-w-4xl mx-auto bg-white p-10 rounded-[40px] shadow-sm border space-y-6">
            <h2 class="text-3xl font-black mb-4">Edit Food</h2>
            <input name="name" value="{{ f.name }}" class="w-full border p-4 rounded-2xl outline-none" required>
            <input name="price" value="{{ f.price }}" class="w-full border p-4 rounded-2xl outline-none" required>
            <input name="image" value="{{ f.image }}" class="w-full border p-4 rounded-2xl outline-none" required>
            <select name="category" class="w-full border p-4 rounded-2xl">
                {% for c in cats %} <option value="{{ c.name }}" {% if c.name == f.category %}selected{% endif %}>{{ c.name }}</option> {% endfor %}
            </select>
            <textarea name="screenshots" class="w-full border p-4 rounded-2xl outline-none">{{ f.screenshots | join(',') }}</textarea>
            <textarea name="details" class="w-full border p-4 rounded-2xl h-32 outline-none" required>{{ f.details }}</textarea>
            <button class="w-full bg-blue-600 text-white py-6 rounded-3xl font-black text-xl">Update Food</button>
        </form>
    </body>
    """, f=food, cats=categories, all_options=all_options)

@app.route('/admin/add-cat', methods=['GET', 'POST'])
def admin_add_cat():
    if not session.get('admin_logged'): return redirect('/admin/dash')
    if request.method == 'POST':
        cats_col.insert_one({"name": request.form.get('name'), "logo": request.form.get('logo')})
    categories = list(cats_col.find())
    return render_template_string("""
    <head>"""+HEAD+"""</head>
    <body class="p-8 bg-gray-50">
        <a href="/admin/dash" class="inline-block mb-6 bg-gray-200 px-6 py-2 rounded-xl font-bold">Back to Dash</a>
        <div class="max-w-4xl mx-auto grid md:grid-cols-2 gap-10">
            <form method="POST" class="bg-white p-8 rounded-3xl shadow-sm border">
                <h3 class="text-2xl font-black mb-6">Create Category</h3>
                <input name="name" placeholder="Name" class="w-full border p-4 rounded-2xl mb-4" required>
                <input name="logo" placeholder="Logo URL" class="w-full border p-4 rounded-2xl mb-6" required>
                <button class="w-full bg-black text-white py-4 rounded-2xl font-bold">Save</button>
            </form>
            <div class="bg-white p-8 rounded-3xl shadow-sm border">
                <h3 class="text-2xl font-black mb-6">Existing Cats</h3>
                {% for c in categories %}
                <div class="flex justify-between py-3 border-b items-center">
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
        <form method="POST" class="max-w-md mx-auto bg-white p-8 rounded-3xl border">
            <h3 class="text-xl font-black mb-4">Edit Category</h3>
            <input name="name" value="{{ c.name }}" class="w-full border p-4 rounded-xl mb-4">
            <input name="logo" value="{{ c.logo }}" class="w-full border p-4 rounded-xl mb-4">
            <button class="w-full bg-blue-600 text-white py-4 rounded-xl">Update</button>
        </form>
    </body>
    """, c=cat)

@app.route('/admin/manage-options', methods=['GET', 'POST'])
def admin_options():
    if not session.get('admin_logged'): return redirect('/admin/dash')
    if request.method == 'POST':
        options_col.insert_one({"name": request.form.get('name'), "type": request.form.get('type')})
    all_opts = list(options_col.find())
    return render_template_string("""
    <head>"""+HEAD+"""</head>
    <body class="p-8 bg-gray-50">
        <a href="/admin/dash" class="inline-block mb-6 bg-gray-200 px-6 py-2 rounded-xl font-bold">Back to Dash</a>
        <div class="max-w-4xl mx-auto">
            <h2 class="text-3xl font-black mb-8">মেইন অপশনসমূহ</h2>
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
                    <div class="flex justify-between py-2 border-b"><span>{{ o.name }}</span> <a href="/admin/del-opt/{{ o._id }}" class="text-red-400"><i class="fas fa-trash-alt"></i></a></div>
                    {% endfor %}
                </div>
                <div class="bg-white p-8 rounded-3xl border">
                    <h3 class="font-bold text-red-600 mb-4">Without List</h3>
                    {% for o in all_opts if o.type == 'exclusion' %}
                    <div class="flex justify-between py-2 border-b"><span>{{ o.name }}</span> <a href="/admin/del-opt/{{ o._id }}" class="text-red-400"><i class="fas fa-trash-alt"></i></a></div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </body>
    """, all_opts=all_opts)

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
        <a href="/admin/dash" class="inline-block mb-6 bg-gray-200 px-6 py-2 rounded-xl font-bold">Back to Dash</a>
        <form method="POST" class="max-w-4xl mx-auto bg-white p-10 rounded-[60px] shadow-sm grid grid-cols-1 md:grid-cols-2 gap-8 border">
            <h2 class="col-span-full text-4xl font-black mb-4">Settings</h2>
            
            <div class="flex flex-col gap-2">
                <label class="font-bold text-gray-600">Site Name</label>
                <input name="name" value="{{ s.name }}" placeholder="Site Name" class="w-full border p-4 rounded-2xl outline-none">
            </div>

            <div class="flex flex-col gap-2">
                <label class="font-bold text-gray-600">Logo URL</label>
                <input name="logo" value="{{ s.logo }}" placeholder="Logo URL" class="w-full border p-4 rounded-2xl outline-none">
            </div>

            <div class="flex flex-col gap-2">
                <label class="font-bold text-gray-600">WhatsApp Number</label>
                <input name="whatsapp" value="{{ s.whatsapp }}" placeholder="WhatsApp" class="w-full border p-4 rounded-2xl outline-none">
            </div>

            <div class="flex flex-col gap-2">
                <label class="font-bold text-gray-600">Facebook Link</label>
                <input name="fb" value="{{ s.fb }}" placeholder="Facebook Link" class="w-full border p-4 rounded-2xl outline-none">
            </div>

            <div class="flex flex-col gap-2">
                <label class="font-bold text-gray-600">Admin Password</label>
                <input name="pass" value="{{ s.pass }}" placeholder="Admin Pass" class="w-full border p-4 rounded-2xl outline-none">
            </div>

            <div class="flex flex-col gap-2">
                <label class="font-bold text-gray-600">Theme Color (e.g. orange, red, blue)</label>
                <input name="theme" value="{{ s.theme }}" placeholder="orange" class="w-full border p-4 rounded-2xl outline-none">
            </div>

            <div class="flex flex-col gap-2 col-span-full">
                <label class="font-bold text-gray-600">Header Text</label>
                <input name="header_text" value="{{ s.header_text }}" placeholder="Header Text" class="w-full border p-4 rounded-2xl outline-none">
            </div>

            <div class="flex flex-col gap-2 col-span-full">
                <label class="font-bold text-gray-600">Footer Text</label>
                <textarea name="footer_text" placeholder="Footer Text" class="w-full border p-4 rounded-2xl outline-none h-24">{{ s.footer_text }}</textarea>
            </div>

            <div class="flex flex-col gap-2">
                <label class="font-bold text-gray-600">DMCA Text</label>
                <input name="dmca" value="{{ s.dmca }}" placeholder="DMCA Protected" class="w-full border p-4 rounded-2xl outline-none">
            </div>

            <div class="flex flex-col gap-2">
                <label class="font-bold text-gray-600">Copyright Text</label>
                <input name="copyright" value="{{ s.copyright }}" placeholder="© 2024 Your Brand" class="w-full border p-4 rounded-2xl outline-none">
            </div>

            <div class="flex flex-col gap-2 col-span-full">
                <label class="font-bold text-gray-600">Privacy Policy Content</label>
                <textarea name="privacy" placeholder="Privacy Policy Content" class="w-full border p-4 rounded-2xl outline-none h-32">{{ s.privacy }}</textarea>
            </div>

            <button class="col-span-full bg-black text-white py-6 rounded-3xl font-black text-2xl hover:bg-gray-800 transition-all">Apply All Changes</button>
        </form>
    </body>
    """, s=settings)

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

@app.route('/admin/login', methods=['POST'])
def admin_login_post():
    settings = get_site_settings()
    if request.form.get('pass') == settings['pass']: session['admin_logged'] = True
    return redirect('/admin/dash')

@app.route('/admin/logout')
def admin_logout(): session.clear(); return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
