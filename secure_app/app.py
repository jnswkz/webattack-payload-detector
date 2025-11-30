"""
Secure Flask Application - Uses ML Model for Attack Detection
WARNING: SQL queries are STILL vulnerable! The model just detects and blocks attacks.
This demonstrates how ML can protect vulnerable applications.
"""
from flask import Flask, request, render_template, redirect, url_for, session, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = 'super_secret_key_123'  # Intentionally weak (not fixed)

DETECTION_API = 'http://127.0.0.1:8000/predict'  # SQLi detection API


def check_for_attack(text):
    """
    Send text to the SQLi detection API.
    Returns (is_attack, probability, label) or (False, 0, 'Unknown') if API unavailable.
    """
    if not text or not text.strip():
        return False, 0, 'Normal'
    
    try:
        payload = {"text": text}
        
        print(f"[DETECTION] Checking input: {text[:50]}...")
        response = requests.post(DETECTION_API, json=payload, timeout=2)
        
        if response.status_code == 200:
            result = response.json()
            is_attack = result.get('label') == 'SQLi'
            probability = result.get('probability', 0)
            label = result.get('label', 'Unknown')
            print(f"[DETECTION] Result: {label} (probability: {probability:.4f})")
            return is_attack, probability, label
        return False, 0, 'API Error'
    except Exception as e:
        print(f"[DETECTION] API Error: {e}")
        return False, 0, 'API Unavailable'


def get_db():
    """Get database connection to Azure PostgreSQL"""
    conn = psycopg2.connect(
        host=os.getenv('PGHOST'),
        user=os.getenv('PGUSER'),
        password=os.getenv('PGPASSWORD'),
        dbname=os.getenv('PGDATABASE'),
        port=os.getenv('PGPORT', 5432),
        sslmode='require'
    )
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
    But protected by ML attack detection.
    """
    error = None
    attack_blocked = False
    
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        # Check username and password for SQLi attacks
        for field_name, field_value in [('username', username), ('password', password)]:
            is_attack, probability, label = check_for_attack(field_value)
            if is_attack:
                attack_blocked = True
                error = f'🚨 SQL INJECTION DETECTED in {field_name}! Request blocked. (Confidence: {probability:.1%})'
                print(f"[BLOCKED] SQLi in {field_name}: '{field_value}' (confidence: {probability:.1%})")
                return render_template('login.html', error=error, attack_blocked=attack_blocked)
        
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # VULNERABLE: Direct string concatenation - SQL Injection! (NOT FIXED)
        query = f"SELECT * FROM users WHERE userName = '{username}' AND password = '{password}'"
        print(f"[DEBUG] Executing query: {query}")
        
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
    
    return render_template('login.html', error=error, attack_blocked=attack_blocked)


@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect(url_for('index'))


@app.route('/products')
def products():
    """
    VULNERABLE PRODUCT SEARCH - SQL Injection possible!
    But protected by ML attack detection.
    """
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    attack_blocked = False
    
    # Check search and category for SQLi attacks
    for field_name, field_value in [('search', search), ('category', category)]:
        if field_value:
            is_attack, probability, label = check_for_attack(field_value)
            if is_attack:
                attack_blocked = True
                print(f"[BLOCKED] SQLi in {field_name}: '{field_value}' (confidence: {probability:.1%})")
                return render_template('products.html', 
                                     products=[], 
                                     search=search, 
                                     category=category,
                                     attack_blocked=True,
                                     attack_probability=probability)
    
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # VULNERABLE: Direct string concatenation - SQL Injection! (NOT FIXED)
    if search:
        query = f"SELECT * FROM products WHERE productName LIKE '%{search}%' OR descriptions LIKE '%{search}%'"
    elif category:
        query = f"SELECT * FROM products WHERE productType = '{category}'"
    else:
        query = "SELECT * FROM products"
    
    print(f"[DEBUG] Executing query: {query}")
    
    try:
        cursor.execute(query)
        products_list = cursor.fetchall()
    except Exception as e:
        products_list = []
        print(f"[ERROR] {str(e)}")
    
    conn.close()
    
    return render_template('products.html', products=products_list, search=search, category=category, attack_blocked=False)


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """
    VULNERABLE PRODUCT DETAIL - SQL Injection possible via product_id manipulation
    """
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # VULNERABLE: Even though product_id is typed as int, the route can be bypassed (NOT FIXED)
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
    But protected by ML attack detection.
    """
    # Check for attack using ML model
    is_attack, probability, label = check_for_attack(request)
    
    if is_attack:
        return jsonify({
            'error': 'Attack detected',
            'blocked': True,
            'confidence': probability
        }), 403
    
    query_param = request.args.get('q', '')
    
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # VULNERABLE: Direct string concatenation (NOT FIXED)
    query = f"SELECT productID, productName, price FROM products WHERE productName LIKE '%{query_param}%'"
    print(f"[DEBUG] API Query: {query}")
    
    try:
        cursor.execute(query)
        results = cursor.fetchall()
    except Exception as e:
        results = {'error': str(e)}
    
    conn.close()
    
    return jsonify(results)


if __name__ == '__main__':
    # Database already initialized on Azure PostgreSQL
    init_db()
    print("=" * 60)
    print("SECURE APP - Protected by ML Attack Detection")
    print("=" * 60)
    print("NOTE: SQL queries are STILL VULNERABLE!")
    print("The ML model detects and blocks attack attempts.")
    print("=" * 60)
    print("\nMake sure the detection API is running:")
    print("  uv run python backend/model.py")
    print("=" * 60)
    app.run(debug=True, port=5003)
