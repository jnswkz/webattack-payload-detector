"""
Vulnerable Flask Application for SQL Injection Demonstration
WARNING: This application is intentionally vulnerable for testing purposes only.
DO NOT use in production!
"""
from flask import Flask, request, render_template, redirect, url_for, session, jsonify
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'super_secret_key_123'  # Intentionally weak

DATABASE = 'vulnerable_app/shop.db'


def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database with sample data"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT,
            is_admin INTEGER DEFAULT 0
        )
    ''')
    
    # Create products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL,
            category TEXT,
            stock INTEGER DEFAULT 0
        )
    ''')
    
    # Insert sample users (plaintext passwords - intentionally insecure)
    sample_users = [
        ('admin', 'admin123', 'admin@shop.com', 1),
        ('user1', 'password1', 'user1@shop.com', 0),
        ('john', 'john2024', 'john@email.com', 0),
        ('alice', 'alice_pass', 'alice@email.com', 0),
    ]
    
    for user in sample_users:
        try:
            cursor.execute('INSERT INTO users (username, password, email, is_admin) VALUES (?, ?, ?, ?)', user)
        except sqlite3.IntegrityError:
            pass
    
    # Insert sample products
    sample_products = [
        ('Laptop Pro 15', 'High performance laptop with 16GB RAM', 1299.99, 'Electronics', 50),
        ('Wireless Mouse', 'Ergonomic wireless mouse with USB receiver', 29.99, 'Electronics', 200),
        ('USB-C Hub', '7-in-1 USB-C hub with HDMI output', 49.99, 'Electronics', 150),
        ('Mechanical Keyboard', 'RGB mechanical keyboard with blue switches', 89.99, 'Electronics', 75),
        ('Monitor 27"', '4K UHD monitor with HDR support', 399.99, 'Electronics', 30),
        ('Headphones BT', 'Noise cancelling bluetooth headphones', 199.99, 'Electronics', 100),
        ('Webcam HD', '1080p webcam with microphone', 79.99, 'Electronics', 80),
        ('Phone Stand', 'Adjustable aluminum phone stand', 19.99, 'Accessories', 300),
        ('Laptop Bag', 'Water resistant laptop bag 15.6"', 39.99, 'Accessories', 120),
        ('Screen Protector', 'Tempered glass screen protector', 9.99, 'Accessories', 500),
    ]
    
    for product in sample_products:
        try:
            cursor.execute('INSERT INTO products (name, description, price, category, stock) VALUES (?, ?, ?, ?, ?)', product)
        except:
            pass
    
    conn.commit()
    conn.close()


@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    VULNERABLE LOGIN - SQL Injection possible!
    Example payloads:
    - Username: admin' --
    - Username: ' OR '1'='1
    - Username: admin' OR '1'='1' --
    """
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        conn = get_db()
        cursor = conn.cursor()
        
        # VULNERABLE: Direct string concatenation - SQL Injection!
        query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
        print(f"[DEBUG] Executing query: {query}")  # For demonstration
        
        try:
            cursor.execute(query)
            user = cursor.fetchone()
            
            if user:
                session['logged_in'] = True
                session['username'] = user['username']
                session['is_admin'] = user['is_admin']
                conn.close()
                return redirect(url_for('products'))
            else:
                error = 'Invalid credentials'
        except Exception as e:
            error = f'Database error: {str(e)}'
        
        conn.close()
    
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect(url_for('index'))


@app.route('/products')
def products():
    """
    VULNERABLE PRODUCT SEARCH - SQL Injection possible!
    Example payloads:
    - Search: ' OR '1'='1
    - Search: ' UNION SELECT id, username, password, email, is_admin FROM users --
    - Search: laptop' OR '1'='1' --
    """
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    
    conn = get_db()
    cursor = conn.cursor()
    
    # VULNERABLE: Direct string concatenation - SQL Injection!
    if search:
        query = f"SELECT * FROM products WHERE name LIKE '%{search}%' OR description LIKE '%{search}%'"
    elif category:
        query = f"SELECT * FROM products WHERE category = '{category}'"
    else:
        query = "SELECT * FROM products"
    
    print(f"[DEBUG] Executing query: {query}")  # For demonstration
    
    try:
        cursor.execute(query)
        products_list = cursor.fetchall()
    except Exception as e:
        products_list = []
        print(f"[ERROR] {str(e)}")
    
    conn.close()
    
    return render_template('products.html', products=products_list, search=search, category=category)


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """
    VULNERABLE PRODUCT DETAIL - SQL Injection possible via product_id manipulation
    """
    conn = get_db()
    cursor = conn.cursor()
    
    # VULNERABLE: Even though product_id is typed as int, the route can be bypassed
    query = f"SELECT * FROM products WHERE id = {product_id}"
    print(f"[DEBUG] Executing query: {query}")
    
    try:
        cursor.execute(query)
        product = cursor.fetchone()
    except Exception as e:
        product = None
        print(f"[ERROR] {str(e)}")
    
    conn.close()
    
    return render_template('product_detail.html', product=product)


@app.route('/api/search')
def api_search():
    """
    VULNERABLE API ENDPOINT - SQL Injection possible!
    """
    query_param = request.args.get('q', '')
    
    conn = get_db()
    cursor = conn.cursor()
    
    # VULNERABLE: Direct string concatenation
    query = f"SELECT id, name, price FROM products WHERE name LIKE '%{query_param}%'"
    print(f"[DEBUG] API Query: {query}")
    
    try:
        cursor.execute(query)
        results = [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        results = {'error': str(e)}
    
    conn.close()
    
    return jsonify(results)


if __name__ == '__main__':
    # Initialize database
    os.makedirs('vulnerable_app', exist_ok=True)
    init_db()
    print("=" * 60)
    print("WARNING: This is a VULNERABLE application for testing only!")
    print("DO NOT deploy to production!")
    print("=" * 60)
    print("\nSQL Injection Examples:")
    print("  Login: admin' --")
    print("  Login: ' OR '1'='1")
    print("  Search: ' OR '1'='1' --")
    print("  Search: ' UNION SELECT 1,username,password,email,is_admin,1 FROM users --")
    print("=" * 60)
    app.run(debug=True, port=5001)
