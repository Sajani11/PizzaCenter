from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

mysql = MySQL(app)


# --- Helper: check allowed image types ---
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


# --- Home Page ---
@app.route('/')
def home():
    return render_template('home.html')


# --- Register ---
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

        flash('Registration successful. Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


# --- Login ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_input = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", [username])
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user[2], password_input):
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[3]

            flash('Login successful!', 'success')
            return redirect(url_for('admin_dashboard' if user[3] == 'admin' else 'menu'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')


# --- Logout ---
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))


# --- Menu Page (Users Only) ---
@app.route('/menu')
def menu():
    if 'user_id' not in session or session['role'] != 'user':
        flash('Login as user to access menu.', 'warning')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM pizzas")
    pizzas = cur.fetchall()
    cur.close()

    return render_template('menu.html', pizzas=pizzas)


# --- Place Order ---
@app.route('/order/<int:pizza_id>', methods=['GET', 'POST'])
def order(pizza_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM pizzas WHERE id = %s", (pizza_id,))
    pizza = cur.fetchone()

    if request.method == 'POST':
        quantity = int(request.form['quantity'])
        pizza_type = request.form['pizza_type']
        pizza_size = request.form['pizza_size']
        address = request.form['address']
        payment_method = request.form['payment_method']
        total_price = pizza[3] * quantity
        order_time = datetime.now()
        delivery_time = order_time + timedelta(minutes=30)

        cur.execute("""
            INSERT INTO orders 
            (user_id, pizza_id, quantity, pizza_type, pizza_size, total_price, address, delivery_time, payment_method, status) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (session['user_id'], pizza_id, quantity, pizza_type, pizza_size, total_price, address, delivery_time, payment_method, 'pending'))
        mysql.connection.commit()
        order_id = cur.lastrowid
        cur.close()

        flash('Order placed successfully!', 'success')
        return redirect(url_for('order_confirmation', order_id=order_id))

    return render_template('order.html', pizza=pizza)


# --- Order Confirmation ---
@app.route('/order_confirmation/<int:order_id>')
def order_confirmation(order_id):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT orders.id, pizzas.name, orders.total_price, orders.status, orders.pizza_type, orders.pizza_size, orders.address, orders.delivery_time, orders.payment_method
        FROM orders
        JOIN pizzas ON orders.pizza_id = pizzas.id
        WHERE orders.id = %s
    """, (order_id,))
    order = cur.fetchone()
    cur.close()

    return render_template('confirm_order.html', order=order)


# --- Admin Dashboard ---
@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Admin access required.', 'danger')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT orders.id, users.username, pizzas.name, orders.quantity, orders.total_price, orders.payment_method, orders.status
        FROM orders 
        JOIN users ON orders.user_id = users.id 
        JOIN pizzas ON orders.pizza_id = pizzas.id
    """)
    orders = cur.fetchall()
    cur.close()

    return render_template('admin_dashboard.html', orders=orders)


# --- Add Pizza (Admin Only) ---
@app.route('/add_pizza', methods=['GET', 'POST'])
def add_pizza():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Admin login required.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        file = request.files['image']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            image_path = f"{app.config['UPLOAD_FOLDER']}/{filename}"

            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO pizzas (name, description, price, image_url) VALUES (%s, %s, %s, %s)",
                        (name, description, price, image_path))
            mysql.connection.commit()
            cur.close()

            flash('Pizza added successfully!', 'success')
            return redirect(url_for('admin_dashboard'))

    return render_template('add_pizza.html')


# --- Mark Order as Completed (Admin) ---
@app.route('/mark_as_completed/<int:order_id>')
def mark_as_completed(order_id):
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Admin access required.', 'danger')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("UPDATE orders SET status = 'completed' WHERE id = %s", (order_id,))
    mysql.connection.commit()
    cur.close()

    flash('Order marked as completed.', 'success')
    return redirect(url_for('admin_dashboard'))


if __name__ == '__main__':
    app.run(debug=True)
