from flask import Flask, render_template, request, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
import csv
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret_key")

# Template folder config (if needed)
# app = Flask(__name__, template_folder="path/to/frontend")

CSV_FILE = os.path.join(os.path.dirname(__file__), 'vector_db', 'users.csv')
users_db = {}

def load_users_from_csv():
    global users_db
    users_db = {}
    try:
        with open(CSV_FILE, 'r', newline='') as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) == 2:
                    users_db[row[0]] = {'password': row[1]}
    except FileNotFoundError:
        pass

def save_users_to_csv():
    os.makedirs(os.path.dirname(CSV_FILE), exist_ok=True)
    with open(CSV_FILE, 'w', newline='') as file:
        writer = csv.writer(file)
        for username, data in users_db.items():
            writer.writerow([username, data['password']])

load_users_from_csv()

@app.route('/')
def index():
    if session.get('logged_in'):
        return render_template('home.html', username=session.get('username'))
    return render_template('index.html')

@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if not username or not password:
            flash("Username and password are required.", "danger")
            return render_template('register.html')
        if username in users_db:
            flash("User already exists.", "warning")
            return render_template('register.html')
        users_db[username] = {'password': generate_password_hash(password)}
        save_users_to_csv()
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if not username or not password:
            flash("Username and password are required.", "danger")
            return render_template('login.html')
        user = users_db.get(username)
        if user and check_password_hash(user['password'], password):
            session['logged_in'] = True
            session['username'] = username
            flash(f"Welcome {username}!", "success")
            return redirect(url_for('index'))
        flash("Incorrect username or password.", "danger")
    return render_template('login.html')

@app.route('/logout/')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
