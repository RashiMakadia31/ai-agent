from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import boto3
import os
import json

# === Flask Setup ===
template_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../frontend'))
app = Flask(__name__, template_folder=template_path)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-key-change-in-production')

# === S3 Config ===
S3_BUCKET = os.environ.get("S3_BUCKET_NAME", "your-bucket-name")
S3_USER_AUTH_FILE = os.environ.get("S3_USER_FILE", "users.json")

s3_client = boto3.client("s3")

# === In-Memory DB ===
users_db = {}  # username -> {'password': hashed_password}

# === Load credentials from S3 ===
def load_users_from_s3():
    global users_db
    users_db = {}
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=S3_USER_AUTH_FILE)
        users_db.update(json.loads(response['Body'].read().decode('utf-8')))
        print(f"✅ Loaded users: {list(users_db.keys())}")
    except s3_client.exceptions.NoSuchKey:
        print("⚠️ No users.json found. It will be created.")
    except Exception as e:
        print(f"❌ Error loading users: {e}")

# === Save credentials to S3 ===
def save_users_to_s3():
    try:
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=S3_USER_AUTH_FILE,
            Body=json.dumps(users_db)
        )
        print(f"✅ Saved users to S3: {list(users_db.keys())}")
    except Exception as e:
        print(f"❌ Error saving users: {e}")

# === Initialize on Start ===
load_users_from_s3()

# === Routes ===
@app.route('/')
def index():
    if session.get('logged_in'):
        return render_template('login.html', username=session.get('username'))
    return render_template('index.html', message="Hello!")

@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return render_template('register.html', message="Username and password are required.")

        if username in users_db:
            return render_template('register.html', message="User already exists.")

        hashed_password = generate_password_hash(password)
        users_db[username] = {'password': hashed_password}
        save_users_to_s3()

        return redirect(url_for('login', message="Registration successful! Please log in."))
    return render_template('register.html')

@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html', message=request.args.get('message'))

    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        return render_template('login.html', message="Username and password are required.")

    user = users_db.get(username)
    if user and check_password_hash(user['password'], password):
        session['logged_in'] = True
        session['username'] = username
        return redirect(url_for('index'))

    return render_template('login.html', message="Incorrect username or password.")

@app.route('/logout/')
def logout():
    session.clear()
    return redirect(url_for('login'))

# === Run ===
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
