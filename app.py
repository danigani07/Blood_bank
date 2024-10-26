from flask import Flask, render_template, request, redirect, session, flash
from mysql.connector import pooling
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import os

# Configuration class
class Config:
    SECRET_KEY = 'password'  # Replace with your actual secret key
    MYSQL_HOST = 'bloodbank-db.clacek8ey7ty.us-east-1.rds.amazonaws.com'
    MYSQL_USER = 'admin'  # Your MySQL username
    MYSQL_PASSWORD = 'bloodbank12345'  # Your MySQL password
    MYSQL_DB = 'bloodbank_db'  # Your MySQL database name

    # Add a DB_CONFIG attribute to hold database connection parameters
    DB_CONFIG = {
        'host': MYSQL_HOST,
        'user': MYSQL_USER,
        'password': MYSQL_PASSWORD,
        'database': MYSQL_DB
    }

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

# Create a connection pool
connection_pool = pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=5,
    host=Config.MYSQL_HOST,
    user=Config.MYSQL_USER,
    password=Config.MYSQL_PASSWORD,
    database=Config.MYSQL_DB
)

def get_db_connection():
    return connection_pool.get_connection()

# Testing the Database Connection
@app.route('/test-db-connection')
def test_db_connection():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DATABASE();")
        db = cursor.fetchone()
        cursor.close()
        conn.close()
        return f"Connected to database: {db[0]}"
    except Exception as e:
        return str(e)

# Home Route
@app.route('/')
def index():
    return render_template('index.html')

# User Registration Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fullname = request.form['fullname']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        blood_type = request.form['blood_type']

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if the email already exists
        cursor.execute("SELECT * FROM register WHERE email = %s", (email,))
        if cursor.fetchone():
            flash('Email already exists! Please log in.', 'error')
            return redirect('/login')

        # Insert the new user into the database
        cursor.execute("INSERT INTO register (fullname, email, password, blood_type) VALUES (%s, %s, %s, %s)",
                       (fullname, email, password, blood_type))
        conn.commit()
        cursor.close()
        conn.close()

        flash('Registration successful! You can now log in.', 'success')
        return redirect('/login')

    return render_template('register.html')

# User Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check credentials
        cursor.execute("SELECT * FROM register WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user[3], password):  # user[3] is the password field
            session['user'] = {'email': user[2], 'fullname': user[1]}  # user[2] is the email, user[1] is fullname
            return redirect('/dashboard')

        flash('Invalid email or password!', 'error')

    return render_template('login.html')

# User Dashboard Route
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    email = session['user']['email']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT fullname, blood_type FROM register WHERE email = %s", (email,))
    user_data = cursor.fetchone()
    cursor.execute("SELECT * FROM request WHERE blood_type = %s AND status = 'pending'", (user_data[1],))  # blood_type
    blood_requests = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('dashboard.html', user=user_data, requests=blood_requests)

# Route for submitting a blood request
@app.route('/request', methods=['GET', 'POST'])
def request_blood():
    if 'user' not in session:
        return redirect('/login')

    if request.method == 'POST':
        location = request.form['location']
        blood_type = request.form['blood_type']
        urgency = request.form['urgency']

        conn = get_db_connection()
        cursor = conn.cursor()

        # Get requester_id based on user's email
        cursor.execute("SELECT id FROM register WHERE email = %s", (session['user']['email'],))
        requester_id = cursor.fetchone()[0]

        cursor.execute("INSERT INTO request (requester_id, location, blood_type, urgency) VALUES (%s, %s, %s, %s)",
                       (requester_id, location, blood_type, urgency))
        conn.commit()
        cursor.close()
        conn.close()

        flash('Blood request submitted successfully!', 'success')
        return redirect('/dashboard')

    return render_template('request.html')

# Route for responding to a request
@app.route('/respond/<int:requester_id>/<int:request_id>')
def respond(requester_id, request_id):
    # Logic to fetch request details and show confirmation page
    return render_template('respond.html', requester_id=requester_id, request_id=request_id)

# Route for confirming a donation
@app.route('/donate-blood/<int:request_id>/<int:requester_id>', methods=['POST'])
def donate_blood(request_id, requester_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE request SET status = 'donated' WHERE id = %s", (request_id,))
    conn.commit()
    cursor.close()
    conn.close()

    flash('Thank you for your donation!', 'success')
    return redirect('/dashboard')

# Logout Route
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
