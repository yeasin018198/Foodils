import os
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret_key_123"

# MongoDB Connection
MONGO_URI = os.environ.get("MONGODB_URI", "mongodb+srv://akash:akash@cluster0.hjyqogc.mongodb.net/?appName=Cluster0")
client = MongoClient(MONGO_URI)
db = client.food_db
products = db.products
orders = db.orders

# --- UI ডিজাইনের জন্য CSS/HTML (Tailwind) ---
BASE_HTML = """
<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Premium Food Express</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://accounts.google.com/gsi/client" async defer></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        .food-card:hover { transform: translateY(-5px); transition: 0.3s; }
        .discount-badge { position: absolute; top: 10px; left: 10px; background: #ef4444; color: white; padding: 2px 8px; border-radius: 5px; font-size: 12px; }
    </style>
</head>
<body class="bg-gray-50">
    <!-- Navbar -->
    <nav class="bg-white shadow-sm sticky top-0 z-50">
        <div class="container mx-auto px-4 py-3 flex justify-between items-center">
            <div class="flex items-center gap-2">
                <div class="bg-orange-500 p-2 rounded-lg text-white"><i class="fa fa-utensils"></i></div>
                <span class="text-xl font-black text-gray-800">FOOD<span class="text-orange-500">EXPRESS</span></span>
            </div>
            <div class="flex items-center gap-4">
                {% if session.user %}
                    <div class="text-right hidden md:block">
                        <p class="text-xs text-gray-500">স্বাগতম</p>
                        <p class="text-sm font-bold">{{ session.user.name }}</p>
                    </div>
                    <a href="/logout" class="text-red-500 border border-red-500 px-3 py-1 rounded-md text-sm hover:bg-red-50">লগ আউট</a>
                {% else %}
                    <div id="g_id_onload" data-client_id="{{ google_id }}" data-callback="handleCredentialResponse"></div>
                    <div class="g_id_signin" data-type="standard"></div>
                {% endif %}
                <a href="/admin" class="text-gray-400 hover:text-orange-500"><i class="fa fa-cog"></i></a>
            </div>
        </div>
    </nav>

    <div class="container mx-auto px-4 py-6">
        {% block content %}{% endblock %}
    </div>

    <script>
        function handleCredentialResponse(response) {
            fetch('/api/google-login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ token: response.credential })
            }).then(() => window.location.reload());
        }

        function placeOrder(productId, name) {
            const variant = document.getElementById(`variant-${productId}`).value;
            const price = document.getElementById(`variant-${productId}`).options[document.getElementById(`variant-${productId}`).selectedIndex].getAttribute('data-price');
            
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition((pos) => {
                    fetch('/api/checkout', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            p_id: productId, p_name: name, variant: variant, price: price,
                            lat: pos.coords.latitude, lng: pos.coords.longitude
                        })
                    }).then(res => res.json()).then(data => {
                        alert("অর্ডার সফল হয়েছে! ক্যাশ অন ডেলিভারি (COD)");
                        window.location.href = "/";
                    });
                });
            }
        }
    </script>
</body>
</html>
"""

# --- Routes ---

@app.route('/')
def home():
    selected_cat = request.args.get('category', 'All')
    if selected_cat == 'All':
        food_items = list(products.find())
    else:
        food_items = list(products.find({"category": selected_cat}))
    
    categories = ["All", "Burger", "Pizza", "Drinks", "Dessert", "Chicken"]
    google_id = os.environ.get("GOOGLE_CLIENT_ID", "YOUR_ID")

    content = """
    <!-- Hero Banner -->
    <div class="bg-gradient-to-r from-orange-400 to-orange-600 rounded-2xl p-8 mb-8 text-white">
        <h1 class="text-3xl font-bold">আজকের অফার! 🔥</h1>
        <p>সব খাবারে ২০% পর্যন্ত ছাড় এবং ফ্রি লাইভ ডেলিভারি ট্র্যাকিং।</p>
    </div>

    <!-- Category Tabs -->
    <div class="flex gap-4 mb-8 overflow-x-auto pb-2">
        {% for cat in categories %}
        <a href="/?category={{cat}}" class="px-6 py-2 rounded-full border {{ 'bg-orange-500 text-white border-orange-500' if selected_cat == cat else 'bg-white text-gray-600' }} shadow-sm whitespace-nowrap">
            {{cat}}
        </a>
        {% endfor %}
    </div>

    <!-- Food Grid -->
    <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">
        {% for item in foods %}
        <div class="food-card bg-white rounded-2xl shadow-sm border overflow-hidden relative">
            {% if item.discount %}
            <div class="discount-badge">{{ item.discount }}% OFF</div>
            {% endif %}
            <img src="{{ item.image }}" class="w-full h-48 object-cover">
            <div class="p-4">
                <div class="flex justify-between items-center mb-1">
                    <span class="text-xs font-bold text-orange-500 uppercase">{{ item.category }}</span>
                    <span class="text-xs text-gray-500"><i class="fa fa-star text-yellow-400"></i> {{ item.rating }}</span>
                </div>
                <h3 class="font-bold text-lg text-gray-800">{{ item.name }}</h3>
                <p class="text-xs text-gray-500 mb-4">{{ item.desc }}</p>
                
                <!-- Variant Selector -->
                <label class="text-xs font-bold text-gray-400 uppercase">Select Size/Type</p>
                <select id="variant-{{ item._id }}" class="w-full border p-2 rounded-lg mt-1 text-sm bg-gray-50">
                    {% for v in item.variants %}
                    <option value="{{ v.name }}" data-price="{{ v.price }}">{{ v.name }} - {{ v.price }}৳</option>
                    {% endfor %}
                </select>

                <button onclick="placeOrder('{{ item._id }}', '{{ item.name }}')" class="w-full bg-orange-500 text-white mt-4 py-3 rounded-xl font-bold hover:bg-orange-600 transition flex items-center justify-center gap-2">
                    <i class="fa fa-shopping-basket"></i> Order Now (COD)
                </button>
            </div>
        </div>
        {% endfor %}
    </div>
    """
    return render_template_string(BASE_HTML + content, foods=food_items, categories=categories, selected_cat=selected_cat, google_id=google_id)

@app.route('/api/google-login', methods=['POST'])
def google_login():
    session['user'] = {"name": "Test User", "email": "user@gmail.com"}
    return jsonify({"success": True})

@app.route('/api/checkout', methods=['POST'])
def checkout():
    data = request.json
    order = {
        "user": session.get('user', {"name": "Guest"}),
        "product": data['p_name'],
        "variant": data['variant'],
        "total": data['price'],
        "lat": data['lat'],
        "lng": data['lng'],
        "status": "Pending",
        "time": datetime.now()
    }
    orders.insert_one(order)
    return jsonify({"success": True})

# --- Admin Section ---

@app.route('/admin')
def admin_login_page():
    return render_template_string(BASE_HTML + """
        <div class="max-w-md mx-auto bg-white p-8 rounded-2xl shadow-lg mt-10">
            <h2 class="text-2xl font-bold mb-6">Admin Panel</h2>
            <form action="/admin/dashboard" method="POST">
                <input type="password" name="pass" placeholder="Password" class="w-full border p-3 rounded-xl mb-4 focus:ring-2 ring-orange-500 outline-none">
                <button class="w-full bg-gray-800 text-white py-3 rounded-xl">Login</button>
            </form>
        </div>
    """)

@app.route('/admin/dashboard', methods=['POST', 'GET'])
def admin_dashboard():
    # এখানে পাসওয়ার্ড চেক করতে হবে (সহজ রাখার জন্য স্কিপ করা হলো)
    all_orders = list(orders.find().sort("time", -1))
    
    content = """
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-10">
        <div class="bg-blue-500 text-white p-6 rounded-2xl">
            <p class="text-sm opacity-80">Total Orders</p>
            <h2 class="text-3xl font-bold">{{ orders|length }}</h2>
        </div>
        <div class="bg-green-500 text-white p-6 rounded-2xl">
            <p class="text-sm opacity-80">Payment Method</p>
            <h2 class="text-3xl font-bold">COD</h2>
        </div>
    </div>

    <div class="bg-white rounded-2xl shadow-sm border overflow-hidden">
        <div class="p-4 border-b font-bold text-gray-700 bg-gray-50">Recent Orders (Live Locations)</div>
        <table class="w-full text-left border-collapse">
            <thead>
                <tr class="text-sm text-gray-400 bg-gray-50">
                    <th class="p-4">Customer</th>
                    <th class="p-4">Food & Variant</th>
                    <th class="p-4">Location</th>
                    <th class="p-4">Action</th>
                </tr>
            </thead>
            <tbody>
                {% for o in orders %}
                <tr class="border-b hover:bg-gray-50 transition">
                    <td class="p-4 font-bold">{{ o.user.name }}</td>
                    <td class="p-4">{{ o.product }} ({{ o.variant }}) - <span class="text-orange-500 font-bold">{{ o.total }}৳</span></td>
                    <td class="p-4">
                        <a href="https://www.google.com/maps?q={{o.lat}},{{o.lng}}" target="_blank" class="text-blue-500 flex items-center gap-1">
                            <i class="fa fa-map-marker-alt"></i> View on Map
                        </a>
                    </td>
                    <td class="p-4"><span class="bg-orange-100 text-orange-600 px-3 py-1 rounded-full text-xs font-bold">{{ o.status }}</span></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    """
    return render_template_string(BASE_HTML + content, orders=all_orders)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)
