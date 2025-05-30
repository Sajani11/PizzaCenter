from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__, template_folder='templates')

# Load environment variables
app.secret_key = os.getenv('SECRET_KEY')
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')

# Configure file upload settings
app.config['UPLOAD_FOLDER'] = 'static/pizza_images'  # Folder where images will be stored
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}  # Allowed file types for images

mysql = MySQL(app)

# Check if a file is an allowed type
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Routes
@app.route('/')
def index():
    return render_template('index.html')

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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[3]
            flash('Login successful!')
            if user[3] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('menu'))
        
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('index'))

@app.route('/menu')
def menu():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM pizzas")
    pizzas = cur.fetchall()
    cur.close()
    return render_template('menu.html', pizzas=pizzas)

@app.route('/order', methods=['GET', 'POST'])
def order():
    pizza_id = request.args.get('pizza_id')  
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM pizzas WHERE id = %s", (pizza_id,))
    pizza = cur.fetchone()
    cur.close()

    
    price = pizza[3]  
    if price > 500:
        discount = 0.05  
        discounted_price = price - (price * discount)
    else:
        discount = 0  
        discounted_price = price
    return render_template('order_confirmation.html', pizza=pizza, price=discounted_price, discount=discount)



@app.route('/payment_confirmation/<int:order_id>')
def payment_confirmation(order_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
    order = cur.fetchone()
    cur.close()

    
    if order:
        return render_template('payment_confirmation.html', order=order)
    flash('Order not found.')
    return redirect(url_for('menu'))

@app.route('/admin')
def admin_dashboard():
    if 'role' not in session or session['role'] != 'admin':
        flash('Unauthorized access!')
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

@app.route('/add_pizza', methods=['GET', 'POST'])
def add_pizza():
    if 'role' not in session or session['role'] != 'admin':
        flash('Unauthorized access!')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        pizza_name = request.form['name']
        pizza_description = request.form['description']
        pizza_price = request.form['price']

        # Handle file upload
        if 'photo' not in request.files:
            flash('No photo part')
            return redirect(request.url)
        file = request.files['photo']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Insert pizza into the database
            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO pizzas (name, description, price, photo)
                VALUES (%s, %s, %s, %s)
            """, (pizza_name, pizza_description, pizza_price, file_path))
            mysql.connection.commit()
            cur.close()
            flash('Pizza added successfully with photo!')
            return redirect(url_for('menu'))
        else:
            flash('Invalid file type! Please upload a valid image.')

    return render_template('add_pizza.html')

if __name__ == '__main__':
    app.run(debug=True)
