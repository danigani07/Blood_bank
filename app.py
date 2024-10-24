from flask import Flask, render_template, request, redirect, session, flash
import mysql.connector
from mysql.connector.pooling import MySQLConnectionPool
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Create database connection pool
connection_pool = MySQLConnectionPool(pool_name="mypool", pool_size=5, **Config.DB_CONFIG)

def get_db_connection():
    return connection_pool.get_connection()

# Home Route
@app.route('/')
def index():
    return render_template('index.html')

# User Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fullname = request.form['fullname']
        email = request.form['email']
        password = request.form['password']
        blood_type = request.form['blood_type']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM register WHERE email = %s", (email,))
        if cursor.fetchone():
            flash('Email already registered. Please log in.')
            return redirect('/login')

        cursor.execute("INSERT INTO register (fullname, email, password, blood_type) VALUES (%s, %s, %s, %s)",
                       (fullname, email, password, blood_type))
        conn.commit()
        session['user'] = {'email': email, 'fullname': fullname}
        return redirect('/confirmation')
    return render_template('register.html')

# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM register WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()
        if user:
            session['user'] = {'email': user[1], 'fullname': user[0]}
            return redirect('/dashboard')
        else:
            flash('Invalid credentials')
            return redirect('/login')
    return render_template('login.html')

# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user' in session:
        email = session['user']['email']
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT fullname, email, blood_type FROM register WHERE email = %s", (email,))
        user_data = cursor.fetchone()

        cursor.execute("SELECT * FROM request WHERE blood_type = %s AND status = 'pending'", (user_data[2],))
        requests = cursor.fetchall()

        return render_template('dashboard.html', user=user_data, requests=requests)
    else:
        return redirect('/login')

# Blood Request Submission
@app.route('/request-blood', methods=['GET', 'POST'])
def request_blood():
    if request.method == 'POST':
        location = request.form['location']
        blood_type = request.form['blood_type']
        urgency = request.form['urgency']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM register WHERE email = %s", (session['user']['email'],))
        requester_id = cursor.fetchone()[0]

        cursor.execute("INSERT INTO request (requester_id, location, blood_type, urgency, status) VALUES (%s, %s, %s, %s, 'pending')",
                       (requester_id, location, blood_type, urgency))
        conn.commit()
        flash('Request submitted successfully')
        return redirect('/dashboard')
    return render_template('request.html')

# Respond to a Request
@app.route('/respond/<int:requester_id>/<int:request_id>', methods=['GET', 'POST'])
def respond(requester_id, request_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM register WHERE id = %s", (requester_id,))
    requester_data = cursor.fetchone()

    cursor.execute("SELECT * FROM request WHERE id = %s", (request_id,))
    request_data = cursor.fetchone()

    return render_template('respond.html', requester=requester_data, request=request_data)

# Donation Confirmation
@app.route('/donate-blood/<int:request_id>/<int:requester_id>', methods=['POST'])
def donate_blood(request_id, requester_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE request SET status = 'donated' WHERE id = %s", (request_id,))
    conn.commit()
    flash('Donation confirmed')
    return redirect('/dashboard')

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
