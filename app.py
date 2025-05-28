from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
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

mysql = MySQL(app)


# Routes
@app.route('/')
def index():
    print("Index page hit") 
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
        flash('Registration successful! Please login.')
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
        flash('Invalid credentials!')
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

@app.route('/order/<int:pizza_id>', methods=['GET', 'POST'])
def order(pizza_id):
    if 'user_id' not in session:
        flash('Please log in to order.')
        return redirect(url_for('login'))
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM pizzas WHERE id = %s", (pizza_id,))
    pizza = cur.fetchone()
    if request.method == 'POST':
        user_id = session['user_id']
        cur.execute("INSERT INTO orders (user_id, pizza_id, status) VALUES (%s, %s, %s)", (user_id, pizza_id, 'pending'))
        mysql.connection.commit()
        flash('Order placed successfully!')
        return redirect(url_for('menu'))
    return render_template('order.html', pizza=pizza)

@app.route('/admin')
def admin_dashboard():
    if 'role' not in session or session['role'] != 'admin':
        flash('Unauthorized access!')
        return redirect(url_for('login'))
    cur = mysql.connection.cursor()
    cur.execute("SELECT o.id, u.username, p.name, o.status FROM orders o JOIN users u ON o.user_id = u.id JOIN pizzas p ON o.pizza_id = p.id")
    orders = cur.fetchall()
    cur.close()
    return render_template('admin_dashboard.html', orders=orders)

if __name__ == '__main__':
    app.run(debug=True)
