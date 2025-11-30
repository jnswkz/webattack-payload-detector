"""
Vulnerable Flask Application for SQL Injection Demonstration
WARNING: This application is intentionally vulnerable for testing purposes only.
DO NOT use in production!
"""
from flask import Flask, request, render_template, redirect, url_for, session, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = 'super_secret_key_123'  # Intentionally weak

# PostgreSQL connection from .env
DB_CONFIG = {
    'host': os.getenv('PGHOST'),
    'user': os.getenv('PGUSER'),
    'password': os.getenv('PGPASSWORD'),
    'database': os.getenv('PGDATABASE'),
    'port': os.getenv('PGPORT', 5432)
}


def get_db():
    """Get database connection"""
    conn = psycopg2.connect(**DB_CONFIG)
    return conn


def init_db():
    """Database is already initialized via init.sql on Azure PostgreSQL"""
    pass


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
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # VULNERABLE: Direct string concatenation - SQL Injection!
        query = f"SELECT * FROM users WHERE userName = '{username}' AND password = '{password}'"
        print(f"[DEBUG] Executing query: {query}")  # For demonstration
        
        try:
            cursor.execute(query)
            user = cursor.fetchone()
            
            if user:
                session['logged_in'] = True
                session['username'] = user['username']
                session['is_admin'] = (user['userid'] == '00001')  # admin check by userID
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
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # VULNERABLE: Direct string concatenation - SQL Injection!
    if search:
        query = f"SELECT * FROM products WHERE productName LIKE '%{search}%'"
    elif category:
        query = f"SELECT * FROM products WHERE productType = '{category}'"
    else:
        query = "SELECT * FROM products"
    
    print(f"[DEBUG] Executing query: {query}")  # For demonstration
    
    error_msg = None
    try:
        cursor.execute(query)
        products_list = cursor.fetchall()
    except Exception as e:
        products_list = []
        error_msg = str(e)
        print(f"[ERROR] {str(e)}")
    
    conn.close()
    
    return render_template('products.html', products=products_list, search=search, category=category, error=error_msg)


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """
    VULNERABLE PRODUCT DETAIL - SQL Injection possible via product_id manipulation
    """
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # VULNERABLE: Even though product_id is typed as int, the route can be bypassed
    query = f"SELECT * FROM products WHERE productID = '{product_id}'"
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
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # VULNERABLE: Direct string concatenation
    query = f"SELECT productID, productName, price FROM products WHERE productName LIKE '%{query_param}%'"
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
    print("  Search: ' UNION SELECT 1,userName,password,email,balance,1 FROM users --")
    print("=" * 60)
    app.run(debug=True, port=5001)
