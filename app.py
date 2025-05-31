from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, template_folder='templates')

# App configuration
app.secret_key = os.getenv('SECRET_KEY')
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')

# File upload config
app.config['UPLOAD_FOLDER'] = 'static/pizza_images'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Initialize MySQL
mysql = MySQL(app)

# Helper to validate uploaded file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Home route
@app.route('/')
def index():
    return render_template('index.html')

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        role = 'user'

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", (username, password, role))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('login'))
    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()

        if user:
            stored_password = user[2]
            is_valid = check_password_hash(stored_password, password)

            if is_valid:
                session['user_id'] = user[0]
                session['username'] = user[1]
                session['role'] = user[3]
                flash('Login successful!', 'success')

                if user[3] == 'admin':
                    return redirect(url_for('admin_dashboard'))
                else:
                  return redirect(url_for('menu'))            
    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# Menu route
@app.route('/menu')
def menu():
    if 'username' not in session:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM pizzas")
    pizzas = cur.fetchall()
    cur.close()

    return render_template('menu.html', pizzas=pizzas)

# Order route
@app.route('/order/<int:pizza_id>', methods=['GET', 'POST'])
def order(pizza_id):
    if 'user_id' not in session:
        flash('Please log in to place an order.', 'warning')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM pizzas WHERE id = %s", (pizza_id,))
    pizza = cur.fetchone()

    if not pizza:
        flash('Pizza not found.', 'danger')
        return redirect(url_for('menu'))

    if request.method == 'POST':
        quantity = int(request.form['quantity'])
        payment_method = request.form['payment_method']
        total_price = quantity * pizza[3]  
        cur.execute("""
            INSERT INTO orders (user_id, pizza_id, quantity, payment_method, total_price, status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (session['user_id'], pizza_id, quantity, payment_method, total_price, 'pending'))
        mysql.connection.commit()

        order_id = cur.lastrowid

        cur.execute("""
            SELECT o.id, u.username, p.name, o.quantity, p.price, o.total_price, o.payment_method
            FROM orders o
            JOIN users u ON o.user_id = u.id
            JOIN pizzas p ON o.pizza_id = p.id
            WHERE o.id = %s
        """, (order_id,))
        order_details = cur.fetchone()
        cur.close()
        return render_template('order_confirmation.html', order=order_details)

    cur.close()
    return render_template('order.html', pizza=pizza, payment_method='cash')  

# Payment confirmation route
@app.route('/payment_confirmation/<int:order_id>')
def payment_confirmation(order_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
    order = cur.fetchone()
    cur.close()

    if order:
        return render_template('payment_confirmation.html', order=order)

    flash('Order not found.', 'danger')
    return redirect(url_for('menu'))

# Admin dashboard
@app.route('/admin')
def admin_dashboard():
    if session.get('role') != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT o.id, u.username, p.name, o.status, o.payment_method
        FROM orders o
        JOIN users u ON o.user_id = u.id
        JOIN pizzas p ON o.pizza_id = p.id
    """)
    orders = cur.fetchall()
    cur.close()

    return render_template('admin_dashboard.html', orders=orders)

# Add pizza (admin only)

@app.route('/add_pizza', methods=['GET', 'POST'])
def add_pizza():
    if session.get('role') != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))
    image_url = None
    if request.method == 'POST':
        pizza_name = request.form['name']
        pizza_description = request.form['description']
        pizza_price = request.form['price']

        # Check if image source is file or URL
        image_source = request.form.get('image_source')

        if image_source == 'file':
            # Image upload
            file = request.files.get('photo')
            if not file or not allowed_file(file.filename):
                flash('Invalid or missing image file.', 'danger')
                return redirect(request.url)

            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            image_url = file_path  # Use file path as image URL
        elif image_source == 'url':
            # Image URL
            image_url = request.form['image_url']
            if not image_url:
                flash('Please provide a valid image URL.', 'danger')
                return redirect(request.url)

       
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO pizzas (name, description, price, image_url)
            VALUES (%s, %s, %s, %s)
        """, (pizza_name, pizza_description, pizza_price, image_url))
        mysql.connection.commit()
        cur.close()

        flash('Pizza added successfully!', 'success')
        return redirect(url_for('menu'))

    return render_template('add_pizza.html')



if __name__ == '__main__':
    app.run(debug=True)
