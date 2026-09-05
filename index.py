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
    .glass { background: rgba(255, 255, 255, 0.9); backdrop-filter: blur(10px); }
    .cart-badge { position: absolute; top: -5px; right: -5px; background: red; color: white; border-radius: 50%; padding: 2px 6px; font-size: 10px; font-weight: bold; }
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
                <img src="{{ settings.logo }}" class="w-10 h-10 md:w-16 md:h-16 rounded-full border-2 border-{{ settings.theme }}-500 shadow-sm">
                <h1 class="text-xl md:text-3xl font-black text-{{ settings.theme }}-600 tracking-tighter">{{ settings.name }}</h1>
            </div>
            <div class="flex items-center gap-4">
                <a href="/cart" class="relative bg-gray-100 p-3 rounded-2xl">
                    <i class="fas fa-shopping-cart text-xl"></i>
                    <span id="cartCount" class="cart-badge animate__animated animate__bounceIn">0</span>
                </a>
            </div>
        </nav>

        <div class="p-4 md:p-8">
            <div class="bg-{{ settings.theme }}-600 rounded-[40px] p-8 md:p-20 text-white shadow-2xl relative overflow-hidden text-center mb-10">
                <h2 class="text-2xl md:text-6xl font-black relative z-10 leading-tight mb-4">{{ settings.header_text }}</h2>
                <p class="text-sm md:text-xl opacity-80 uppercase tracking-widest font-bold">বেস্ট কোয়ালিটি ফুড ডেলিভারি</p>
                <i class="fas fa-hamburger absolute -right-10 -bottom-10 text-[150px] md:text-[300px] opacity-10 rotate-12"></i>
            </div>

            <h2 class="text-2xl md:text-4xl font-black mb-8 flex items-center gap-3">
                <span class="w-2 h-10 bg-{{ settings.theme }}-600 rounded-full"></span> মেনু ক্যাটাগরি
            </h2>

            <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
                {% for cat in categories %}
                <a href="/category/{{ cat.name }}" class="bg-white p-6 rounded-[40px] shadow-sm border-2 border-gray-50 text-center hover:scale-105 transition-transform group">
                    <div class="w-24 h-24 md:w-40 md:h-40 rounded-full border-4 border-gray-50 overflow-hidden mx-auto mb-4 group-hover:border-{{ settings.theme }}-400">
                        <img src="{{ cat.logo }}" class="w-full h-full object-cover">
                    </div>
                    <h3 class="font-black text-lg md:text-2xl text-gray-800">{{ cat.name }}</h3>
                </a>
                {% endfor %}
            </div>
        </div>

        <footer class="bg-white border-t mt-20 p-10 md:p-24 text-center">
            <img src="{{ settings.logo }}" class="w-16 h-16 rounded-full mx-auto mb-4 border shadow-sm">
            <h2 class="font-bold text-2xl mb-4">{{ settings.name }}</h2>
            <p class="text-gray-400 text-sm max-w-md mx-auto">{{ settings.footer_text }}</p>
            <div class="flex justify-center gap-8 my-8 text-3xl">
                <a href="{{ settings.fb }}" class="text-blue-600"><i class="fab fa-facebook"></i></a>
                <a href="https://wa.me/{{ wa_clean }}" class="text-green-500"><i class="fab fa-whatsapp"></i></a>
            </div>
            <p class="text-[10px] text-gray-300">{{ settings.copyright }} | {{ settings.dmca }}</p>
        </footer>

        <script>
            function updateCartCount() {
                let cart = JSON.parse(localStorage.getItem('foodCart') || '[]');
                document.getElementById('cartCount').innerText = cart.length;
            }
            updateCartCount();
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
    <head>"""+HEAD+"""<title>{{ name }}</title></head>
    <body class="bg-gray-50">
        <nav class="glass sticky top-0 z-50 px-4 py-3 flex items-center gap-4 border-b">
            <a href="/" class="bg-white w-10 h-10 flex items-center justify-center rounded-xl shadow-sm"><i class="fas fa-chevron-left"></i></a>
            <h1 class="text-xl font-black">{{ name }} আইটেমসমূহ</h1>
        </nav>
        <div class="p-4 md:p-10 grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4 md:gap-8">
            {% for food in foods %}
            <a href="/food/{{ food._id }}" class="bg-white rounded-3xl p-3 md:p-5 shadow-sm border-2 border-transparent hover:border-{{ settings.theme }}-400 transition-all">
                <img src="{{ food.image }}" class="rounded-2xl object-cover w-full h-40 md:h-56">
                <h4 class="text-base md:text-2xl font-bold mt-4 text-gray-800 truncate px-1">{{ food.name }}</h4>
                <div class="flex justify-between items-center mt-2 px-1">
                    <span class="text-{{ settings.theme }}-600 font-black text-lg md:text-2xl">৳{{ food.price }}</span>
                    <i class="fas fa-plus-circle text-gray-200 text-2xl"></i>
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
    <body class="bg-gray-50 pb-20">
        <div class="max-w-4xl mx-auto bg-white min-h-screen shadow-2xl relative">
            <a href="/category/{{ food.category }}" class="absolute top-4 left-4 z-50 bg-white/80 p-3 rounded-2xl shadow-xl border"><i class="fas fa-chevron-left"></i> ব্যাক</a>
            <img src="{{ food.image }}" class="w-full h-80 md:h-[500px] object-cover">
            
            <div class="p-6 md:p-12 -mt-12 bg-white rounded-t-[50px] relative z-10">
                <h1 class="text-3xl md:text-6xl font-black tracking-tighter">{{ food.name }}</h1>
                <p class="text-2xl md:text-4xl font-black text-{{ settings.theme }}-600 mt-4">৳{{ food.price }}</p>

                <div class="grid grid-cols-4 md:grid-cols-6 gap-3 my-8">
                    {% for ss in food.screenshots %}
                    <img src="{{ ss }}" class="w-full aspect-square rounded-xl object-cover border">
                    {% endfor %}
                </div>

                <!-- Quantity -->
                <div class="bg-gray-50 p-6 rounded-3xl border flex items-center justify-between mb-8 shadow-inner">
                    <span class="font-bold text-lg">Quantity / পরিমাণ</span>
                    <div class="flex items-center gap-6">
                        <button onclick="changeQty(-1)" class="w-12 h-12 bg-white rounded-xl shadow-sm border flex items-center justify-center"><i class="fas fa-minus"></i></button>
                        <span id="qtyDisplay" class="text-2xl font-black">1</span>
                        <button onclick="changeQty(1)" class="w-12 h-12 bg-{{ settings.theme }}-600 text-white rounded-xl shadow-lg flex items-center justify-center"><i class="fas fa-plus"></i></button>
                    </div>
                </div>

                <!-- Extras (Kullu Shai) -->
                {% if food.addons %}
                <div class="mb-8">
                    <h4 class="font-black text-green-600 mb-4 uppercase tracking-widest text-xs">Extras (কুল্লু সাই)</h4>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {% for opt in food.addons %}
                        <label class="flex items-center gap-4 p-4 bg-gray-50 rounded-2xl border cursor-pointer hover:bg-green-50 transition-all font-bold">
                            <input type="checkbox" name="addon" value="{{ opt }}" class="w-6 h-6 accent-green-600"> {{ opt }}
                        </label>
                        {% endfor %}
                    </div>
                </div>
                {% endif %}

                {% if food.exclusions %}
                <div class="mb-8">
                    <h4 class="font-black text-red-600 mb-4 uppercase tracking-widest text-xs">Without (বিদুন / ছাড়া)</h4>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {% for opt in food.exclusions %}
                        <label class="flex items-center gap-4 p-4 bg-gray-50 rounded-2xl border cursor-pointer hover:bg-red-50 transition-all font-bold">
                            <input type="checkbox" name="exclusion" value="{{ opt }}" class="w-6 h-6 accent-red-600"> {{ opt }}
                        </label>
                        {% endfor %}
                    </div>
                </div>
                {% endif %}

                <div class="bg-gray-50 rounded-3xl p-6 border mb-10">
                    <h4 class="font-bold mb-4">খাবার সম্পর্কে তথ্য:</h4>
                    <p class="text-gray-600 leading-relaxed whitespace-pre-line">{{ food.details }}</p>
                </div>

                <button onclick="addToCart()" class="w-full bg-black text-white py-6 rounded-[30px] font-black text-xl md:text-2xl shadow-2xl flex items-center justify-center gap-3">
                    <i class="fas fa-cart-plus"></i> Add to Cart (কার্টে যোগ করুন)
                </button>
            </div>
        </div>

        <script>
            let qty = 1;
            function changeQty(n) { qty = Math.max(1, qty + n); document.getElementById('qtyDisplay').innerText = qty; }

            function addToCart() {
                let addons = Array.from(document.querySelectorAll('input[name="addon"]:checked')).map(e => e.value);
                let exclusions = Array.from(document.querySelectorAll('input[name="exclusion"]:checked')).map(e => e.value);
                
                let item = {
                    id: '{{ food._id }}',
                    name: '{{ food.name }}',
                    price: {{ food.price }},
                    qty: qty,
                    addons: addons,
                    exclusions: exclusions,
                    image: '{{ food.image }}'
                };
                
                let cart = JSON.parse(localStorage.getItem('foodCart') || '[]');
                cart.push(item);
                localStorage.setItem('foodCart', JSON.stringify(cart));
                alert("কার্টে যোগ করা হয়েছে!");
                window.location.href = '/';
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
    <head>"""+HEAD+"""<title>Your Cart</title></head>
    <body class="bg-gray-50 pb-20">
        <nav class="glass sticky top-0 z-50 px-4 py-3 flex items-center gap-4 border-b">
            <a href="/" class="bg-white w-10 h-10 flex items-center justify-center rounded-xl shadow-sm"><i class="fas fa-chevron-left"></i></a>
            <h1 class="text-xl font-black">আপনার শপিং কার্ট</h1>
        </nav>
        
        <div class="max-w-4xl mx-auto p-4 md:p-10">
            <div id="cartList" class="space-y-4 mb-10"></div>
            
            <div class="bg-white p-8 rounded-[40px] shadow-xl border-2">
                <div class="flex justify-between text-xl md:text-3xl font-black mb-6">
                    <span>সর্বমোট মূল্য:</span>
                    <span class="text-{{ settings.theme }}-600">৳<span id="totalPrice">0</span></span>
                </div>
                <p class="text-blue-500 text-xs md:text-sm font-bold mb-8 italic text-center">* ডেলিভারি চার্জ অফিসিয়াল ড্রাইভার সরাসরি বলে দিবে।</p>
                <button onclick="checkoutWA()" class="w-full bg-green-500 text-white py-6 rounded-[30px] font-black text-xl md:text-3xl shadow-2xl flex items-center justify-center gap-4">
                    <i class="fab fa-whatsapp"></i> অর্ডার সম্পন্ন করুন
                </button>
                <button onclick="clearCart()" class="w-full text-red-400 font-bold mt-6 text-sm underline">কার্ট খালি করুন</button>
            </div>
        </div>

        <script>
            let cart = JSON.parse(localStorage.getItem('foodCart') || '[]');
            let total = 0;

            function renderCart() {
                let html = '';
                total = 0;
                if(cart.length === 0) {
                    html = '<div class="text-center py-20 text-gray-400 font-bold">আপনার কার্ট খালি!</div>';
                }
                cart.forEach((item, index) => {
                    total += (item.price * item.qty);
                    html += `
                        <div class="bg-white p-5 rounded-3xl shadow-sm border flex items-center gap-4 animate__animated animate__fadeInUp">
                            <img src="${item.image}" class="w-20 h-20 rounded-2xl object-cover">
                            <div class="flex-1">
                                <h4 class="font-black text-lg">${item.name}</h4>
                                <p class="text-sm text-gray-400">Qty: ${item.qty} x ৳${item.price}</p>
                                <div class="text-[10px] text-gray-500 italic">
                                    ${item.addons.length ? 'Extras: ' + item.addons.join(', ') : ''}
                                    ${item.exclusions.length ? ' | Without: ' + item.exclusions.join(', ') : ''}
                                </div>
                            </div>
                            <button onclick="removeItem(${index})" class="text-red-500 p-2"><i class="fas fa-trash-alt"></i></button>
                        </div>
                    `;
                });
                document.getElementById('cartList').innerHTML = html;
                document.getElementById('totalPrice').innerText = total;
            }

            function removeItem(index) {
                cart.splice(index, 1);
                localStorage.setItem('foodCart', JSON.stringify(cart));
                renderCart();
            }

            function clearCart() { localStorage.removeItem('foodCart'); location.reload(); }

            function checkoutWA() {
                if(cart.length === 0) return alert("কার্ট খালি!");
                let text = `*NEW MULTI-ORDER REQUEST*%0A-----------------------%0A`;
                cart.forEach((item, i) => {
                    text += `${i+1}. *${item.name}*%0A   - Qty: ${item.qty}%0A`;
                    if(item.addons.length) text += `   - Extras: ${item.addons.join(', ')}%0A`;
                    if(item.exclusions.length) text += `   - Without: ${item.exclusions.join(', ')}%0A`;
                    text += `   - Subtotal: ৳${item.price * item.qty}%0A%0A`;
                });
                text += `-----------------------%0A*GRAND TOTAL: ৳${total}*%0A_Delivery charge inform by driver._`;
                window.location.href = `https://wa.me/{{ wa_num }}?text=${text}`;
            }

            renderCart();
        </script>
    </body>
    </html>
    """, settings=settings, wa_num=wa_num)

# --- ADMIN ROUTES ---

@app.route('/admin/dash')
def admin_dash():
    if not session.get('admin_logged'):
        return render_template_string("""
            <head>"""+HEAD+"""</head>
            <div class="max-w-md mx-auto mt-24 p-10 bg-white shadow-2xl rounded-[50px] border-4 text-center">
                <h2 class="text-3xl font-black mb-8 uppercase tracking-tighter">Admin Panel Login</h2>
                <form action="/admin/login" method="POST" class="space-y-6">
                    <input type="password" name="pass" placeholder="Enter Password" class="w-full bg-gray-100 p-5 rounded-2xl text-center outline-none focus:ring-4 focus:ring-black text-xl">
                    <button class="w-full bg-black text-white py-5 rounded-2xl font-black text-xl shadow-2xl">Unlock Access</button>
                </form>
            </div>
        """)
    
    settings = get_site_settings()
    total_foods = foods_col.count_documents({})
    total_cats = cats_col.count_documents({})
    total_views = views_col.count_documents({})
    all_foods = list(foods_col.find().sort("_id", -1))

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>"""+HEAD+"""<title>Admin Dashboard</title></head>
    <body class="flex flex-col lg:flex-row min-h-screen bg-gray-50">
        <!-- Sidebar -->
        <div class="w-full lg:w-80 bg-gray-900 text-white p-8">
            <h2 class="text-3xl font-black mb-16 tracking-tighter flex items-center gap-3"><img src="{{ settings.logo }}" class="w-10 h-10 rounded-full"> Control</h2>
            <nav class="space-y-4 font-bold">
                <a href="/admin/dash" class="flex items-center gap-4 p-5 bg-{{ settings.theme }}-600 rounded-3xl shadow-xl"><i class="fas fa-home"></i> ড্যাশবোর্ড</a>
                <a href="/admin/add-food" class="flex items-center gap-4 p-5 hover:bg-gray-800 rounded-3xl transition-all"><i class="fas fa-plus"></i> নতুন খাবার</a>
                <a href="/admin/manage-options" class="flex items-center gap-4 p-5 hover:bg-gray-800 rounded-3xl transition-all"><i class="fas fa-tasks"></i> কুল্লু সাই / বিদুন</a>
                <a href="/admin/add-cat" class="flex items-center gap-4 p-5 hover:bg-gray-800 rounded-3xl transition-all"><i class="fas fa-layer-group"></i> ক্যাটাগরি</a>
                <a href="/admin/settings" class="flex items-center gap-4 p-5 hover:bg-gray-800 rounded-3xl transition-all"><i class="fas fa-cogs"></i> সেটিংস</a>
                <a href="/" class="flex items-center gap-4 p-5 text-blue-400 border border-blue-400/20 rounded-3xl mt-10"><i class="fas fa-eye"></i> সাইট দেখুন</a>
                <a href="/admin/logout" class="flex items-center gap-4 p-5 text-red-400 mt-20"><i class="fas fa-power-off"></i> লগআউট</a>
            </nav>
        </div>

        <div class="flex-1 p-6 md:p-12 overflow-y-auto">
            <h1 class="text-4xl font-black mb-10 tracking-tighter">সিস্টেম ওভারভিউ</h1>
            <div class="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
                <div class="bg-white p-8 rounded-[40px] shadow-sm border-t-8 border-blue-500">
                    <p class="text-gray-400 text-xs font-black uppercase">Total Views</p>
                    <h3 class="text-4xl font-black mt-2">{{ total_views }}</h3>
                </div>
                <div class="bg-white p-8 rounded-[40px] shadow-sm border-t-8 border-orange-500">
                    <p class="text-gray-400 text-xs font-black uppercase">Items</p>
                    <h3 class="text-4xl font-black mt-2 text-orange-500">{{ total_foods }}</h3>
                </div>
                <div class="bg-white p-8 rounded-[40px] shadow-sm border-t-8 border-purple-500">
                    <p class="text-gray-400 text-xs font-black uppercase">Cats</p>
                    <h3 class="text-4xl font-black mt-2 text-purple-600">{{ total_cats }}</h3>
                </div>
            </div>

            <h3 class="text-2xl font-black mb-8">খাবার ম্যানেজ করুন</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {% for f in all_foods %}
                <div class="bg-white p-6 rounded-[35px] border-2 flex items-center justify-between">
                    <div class="flex items-center gap-4">
                        <img src="{{ f.image }}" class="w-16 h-16 rounded-2xl object-cover shadow-sm">
                        <span class="font-black text-lg">{{ f.name }}</span>
                    </div>
                    <a href="/admin/del-food/{{ f._id }}" class="text-red-500 text-2xl p-4"><i class="fas fa-trash-alt"></i></a>
                </div>
                {% endfor %}
            </div>
        </div>
    </body>
    </html>
    """, total_foods=total_foods, total_cats=total_cats, total_views=total_views, all_foods=all_foods, settings=settings)

@app.route('/admin/add-food', methods=['GET', 'POST'])
def admin_add_food():
    if not session.get('admin_logged'): return redirect('/admin/dash')
    if request.method == 'POST':
        ss_list = [x.strip() for x in request.form.get('screenshots').split(',') if x.strip()]
        foods_col.insert_one({
            "name": request.form.get('name'), "price": int(request.form.get('price')), "image": request.form.get('image'),
            "category": request.form.get('category'), "details": request.form.get('details'), "screenshots": ss_list,
            "addons": request.form.getlist('addons'), "exclusions": request.form.getlist('exclusions')
        })
        return redirect('/admin/dash')
    
    categories = list(cats_col.find())
    all_options = list(options_col.find())
    return render_template_string("""
    <head>"""+HEAD+"""</head>
    <body class="p-6 md:p-16 bg-gray-50">
        <a href="/admin/dash" class="inline-block mb-10 bg-gray-200 px-8 py-3 rounded-2xl font-black text-xl shadow-sm"><i class="fas fa-arrow-left"></i> ব্যাক</a>
        <form method="POST" class="max-w-4xl mx-auto bg-white p-10 md:p-16 rounded-[60px] shadow-2xl border-4 space-y-8">
            <h2 class="text-4xl font-black mb-10 tracking-tighter uppercase">নতুন খাবার যুক্ত করুন</h2>
            <div class="grid md:grid-cols-2 gap-8">
                <input name="name" placeholder="খাবারের নাম" class="w-full border-none bg-gray-50 p-6 rounded-3xl outline-none text-xl" required>
                <input name="price" placeholder="দাম" class="w-full border-none bg-gray-50 p-6 rounded-3xl outline-none text-xl" required>
            </div>
            <input name="image" placeholder="Main Image URL" class="w-full border-none bg-gray-50 p-6 rounded-3xl outline-none text-xl" required>
            <select name="category" class="w-full border-none bg-gray-50 p-6 rounded-3xl outline-none text-xl">
                {% for c in categories %} <option value="{{ c.name }}">{{ c.name }}</option> {% endfor %}
            </select>
            <textarea name="screenshots" placeholder="Screenshots URLs (comma separated)" class="w-full border-none bg-gray-50 p-6 rounded-3xl outline-none text-xl h-24"></textarea>
            
            <div class="grid md:grid-cols-2 gap-10 border-t-2 pt-10">
                <div>
                    <h4 class="font-black text-green-600 mb-6 uppercase tracking-widest text-sm">Extras (কুল্লু সাই)</h4>
                    <div class="max-h-56 overflow-y-auto border-4 p-6 rounded-[35px] space-y-4">
                        {% for o in all_options if o.type == 'addon' %}
                        <label class="flex items-center gap-4 cursor-pointer font-bold"><input type="checkbox" name="addons" value="{{ o.name }}" class="w-6 h-6"> <span>{{ o.name }}</span></label>
                        {% endfor %}
                    </div>
                </div>
                <div>
                    <h4 class="font-black text-red-600 mb-6 uppercase tracking-widest text-sm">Without (বিদুন)</h4>
                    <div class="max-h-56 overflow-y-auto border-4 p-6 rounded-[35px] space-y-4">
                        {% for o in all_options if o.type == 'exclusion' %}
                        <label class="flex items-center gap-4 cursor-pointer font-bold"><input type="checkbox" name="exclusions" value="{{ o.name }}" class="w-6 h-6"> <span>{{ o.name }}</span></label>
                        {% endfor %}
                    </div>
                </div>
            </div>

            <textarea name="details" placeholder="খাবারের বর্ণনা..." class="w-full border-none bg-gray-50 p-6 rounded-[40px] h-48 outline-none text-xl" required></textarea>
            <button class="w-full bg-black text-white py-7 rounded-[40px] font-black text-3xl shadow-2xl hover:scale-105 transition-transform">পাবলিশ খাবার</button>
        </form>
    </body>
    """, categories=categories, all_options=all_options)

@app.route('/admin/manage-options', methods=['GET', 'POST'])
def admin_options():
    if not session.get('admin_logged'): return redirect('/admin/dash')
    if request.method == 'POST':
        options_col.insert_one({"name": request.form.get('name'), "type": request.form.get('type')})
    all_opts = list(options_col.find().sort("_id", -1))
    return render_template_string("""
    <head>"""+HEAD+"""</head>
    <body class="p-6 md:p-16 bg-gray-50">
        <a href="/admin/dash" class="inline-block mb-10 bg-gray-200 px-8 py-3 rounded-2xl font-black text-xl shadow-sm"><i class="fas fa-arrow-left"></i> ব্যাক</a>
        <div class="max-w-5xl mx-auto">
            <h2 class="text-4xl font-black mb-10 tracking-tighter">কুল্লু সাই / বিদুন আইটেম তৈরি</h2>
            <form method="POST" class="bg-white p-8 rounded-[40px] shadow-sm border-2 flex flex-col md:flex-row gap-6 mb-16">
                <input name="name" placeholder="অপশন নাম (যেমন: বিদুন জুবিন)" class="flex-1 border-none bg-gray-50 p-5 rounded-2xl outline-none text-xl" required>
                <select name="type" class="border-none bg-gray-50 p-5 rounded-2xl outline-none text-xl">
                    <option value="addon">Extras (কুল্লু সাই)</option>
                    <option value="exclusion">Without (বিদুন / ছাড়া)</option>
                </select>
                <button class="bg-black text-white px-10 py-5 rounded-2xl font-black text-xl">যোগ করুন</button>
            </form>
            <div class="grid md:grid-cols-2 gap-10">
                <div class="bg-white p-10 rounded-[50px] border-4 shadow-sm text-center">
                    <h3 class="font-black text-green-600 mb-8 text-2xl uppercase tracking-tighter">Add-ons লিস্ট</h3>
                    {% for o in all_opts if o.type == 'addon' %}
                    <div class="flex justify-between py-5 border-b-2 font-bold text-lg"><span>{{ o.name }}</span> <a href="/admin/del-opt/{{ o._id }}" class="text-red-400"><i class="fas fa-times"></i></a></div>
                    {% endfor %}
                </div>
                <div class="bg-white p-10 rounded-[50px] border-4 shadow-sm text-center">
                    <h3 class="font-black text-red-600 mb-8 text-2xl uppercase tracking-tighter">Exclusions লিস্ট</h3>
                    {% for o in all_opts if o.type == 'exclusion' %}
                    <div class="flex justify-between py-5 border-b-2 font-bold text-lg"><span>{{ o.name }}</span> <a href="/admin/del-opt/{{ o._id }}" class="text-red-400"><i class="fas fa-times"></i></a></div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </body>
    """, all_opts=all_opts)

@app.route('/admin/add-cat', methods=['GET', 'POST'])
def admin_add_cat():
    if not session.get('admin_logged'): return redirect('/admin/dash')
    if request.method == 'POST':
        cats_col.insert_one({"name": request.form.get('name'), "logo": request.form.get('logo')})
    categories = list(cats_col.find().sort("_id", -1))
    return render_template_string("""
    <head>"""+HEAD+"""</head>
    <body class="p-6 md:p-16 bg-gray-100">
        <a href="/admin/dash" class="inline-block mb-10 bg-gray-200 px-8 py-3 rounded-2xl font-black text-xl shadow-sm"><i class="fas fa-arrow-left"></i> ব্যাক</a>
        <div class="max-w-6xl mx-auto grid md:grid-cols-2 gap-12">
            <form method="POST" class="bg-white p-10 rounded-[50px] shadow-xl border-4 h-fit">
                <h3 class="text-3xl font-black mb-10">ক্যাটাগরি তৈরি</h3>
                <input name="name" placeholder="ক্যাটাগরি নাম" class="w-full border-none bg-gray-50 p-6 rounded-3xl mb-6 outline-none" required>
                <input name="logo" placeholder="Logo Icon URL" class="w-full border-none bg-gray-50 p-6 rounded-3xl mb-8 outline-none" required>
                <button class="w-full bg-gray-900 text-white py-6 rounded-3xl font-black text-xl shadow-xl">সেভ ক্যাটাগরি</button>
            </form>
            <div class="bg-white p-10 rounded-[50px] shadow-xl border-4">
                <h3 class="text-3xl font-black mb-10 text-gray-400">বিদ্যমান ক্যাটাগরি</h3>
                <div class="space-y-6">
                    {% for cat in categories %}
                    <div class="flex justify-between items-center p-6 bg-gray-50 rounded-[35px] border-2 shadow-sm">
                        <div class="flex items-center gap-6">
                            <img src="{{ cat.logo }}" class="w-16 h-16 rounded-full object-cover border-4 border-white shadow-md">
                            <span class="font-black text-xl">{{ cat.name }}</span>
                        </div>
                        <a href="/admin/del-cat/{{ cat._id }}" class="text-red-500 text-2xl p-4"><i class="fas fa-trash-alt"></i></a>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </body>
    """, categories=categories)

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
        <a href="/admin/dash" class="inline-block mb-10 bg-gray-200 px-8 py-3 rounded-2xl font-black text-xl shadow-sm"><i class="fas fa-arrow-left"></i> ব্যাক</a>
        <form method="POST" class="max-w-5xl mx-auto bg-white p-10 md:p-20 rounded-[70px] shadow-2xl grid grid-cols-1 md:grid-cols-2 gap-10 border-4">
            <h2 class="col-span-full text-4xl font-black mb-6 tracking-tighter">সিস্টেম সেটিংস</h2>
            <div class="space-y-2"><label class="text-xs font-black text-gray-400 px-4 uppercase tracking-widest">সাইটের নাম</label><input name="name" value="{{ s.name }}" class="w-full border-none bg-gray-50 p-6 rounded-3xl outline-none text-xl"></div>
            <div class="space-y-2"><label class="text-xs font-black text-gray-400 px-4 uppercase tracking-widest">লোগো URL</label><input name="logo" value="{{ s.logo }}" class="w-full border-none bg-gray-50 p-6 rounded-3xl outline-none text-xl"></div>
            <div class="space-y-2"><label class="text-xs font-black text-gray-400 px-4 uppercase tracking-widest">WhatsApp নম্বর</label><input name="whatsapp" value="{{ s.whatsapp }}" class="w-full border-none bg-gray-50 p-6 rounded-3xl outline-none text-xl"></div>
            <div class="space-y-2"><label class="text-xs font-black text-gray-400 px-4 uppercase tracking-widest">অ্যাডমিন পাসওয়ার্ড</label><input name="pass" value="{{ s.pass }}" class="w-full border-none bg-gray-50 p-6 rounded-3xl outline-none text-xl"></div>
            
            <div class="col-span-full space-y-2"><label class="text-xs font-black text-gray-400 px-4 uppercase tracking-widest">হেডার টেক্সট</label><input name="header_text" value="{{ s.header_text }}" class="w-full border-none bg-gray-50 p-6 rounded-3xl outline-none text-xl"></div>
            <div class="col-span-full space-y-2"><label class="text-xs font-black text-gray-400 px-4 uppercase tracking-widest">প্রাইভেসি পলিসি</label><textarea name="privacy" class="w-full border-none bg-gray-50 p-6 rounded-[40px] h-48 outline-none text-xl">{{ s.privacy }}</textarea></div>
            <div class="col-span-full space-y-2"><label class="text-xs font-black text-gray-400 px-4 uppercase tracking-widest">ফুটার টেক্সট</label><input name="footer_text" value="{{ s.footer_text }}" class="w-full border-none bg-gray-50 p-6 rounded-3xl outline-none text-xl"></div>
            
            <div class="space-y-2"><label class="text-xs font-black text-gray-400 px-4 uppercase tracking-widest">DMCA টেক্সট</label><input name="dmca" value="{{ s.dmca }}" class="w-full border-none bg-gray-50 p-6 rounded-3xl outline-none text-xl"></div>
            <div class="space-y-2"><label class="text-xs font-black text-gray-400 px-4 uppercase tracking-widest">Copyright টেক্সট</label><input name="copyright" value="{{ s.copyright }}" class="w-full border-none bg-gray-50 p-6 rounded-3xl outline-none text-xl"></div>
            <button class="col-span-full bg-black text-white py-8 rounded-[40px] font-black text-3xl shadow-2xl mt-10">আপডেট সেটিংস</button>
        </form>
    </body>
    """, s=settings)

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
