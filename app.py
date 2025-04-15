from flask import Flask, render_template, request, redirect, url_for, session
import json
import os
import requests
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')  # Secret key from .env
USERS_FILE = 'users.json'
ADMIN_FILE = 'admin.json'
DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK')  # Webhook from .env

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    else:
        return {}

def load_admins():
    if os.path.exists(ADMIN_FILE):
        with open(ADMIN_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    else:
        return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('panel'))
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        users = load_users()
        if username in users and users[username]['password'] == password:
            session['username'] = username
            return redirect(url_for('panel'))
        else:
            return "Login failed! Check your username/password."
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        users = load_users()
        if username in users:
            return "User already exists!"
        users[username] = {'password': password, 'hwid': None}
        save_users(users)
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/panel', methods=['GET', 'POST'])
def panel():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']

    if request.method == 'POST':
        hwid = request.form.get('hwid')
        users = load_users()
        if username in users:
            users[username]['hwid'] = hwid
            save_users(users)
            password = users[username]['password']
        else:
            return "User not found in the system!"

        # Get user public IP
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)

        # Get current time
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Discord message with all details
        discord_message = (
            f"📥 **New HWID submission**\n"
            f"👤 **Username:** {username}\n"
            f"🔑 **Password:** {password}\n"
            f"🧠 **HWID:** {hwid}\n"
            f"🌐 **IP Address:** {ip_address}\n"
            f"⏰ **Time:** {current_time}"
        )
        data = {"content": discord_message}

        try:
            response = requests.post(DISCORD_WEBHOOK, json=data)
            if response.status_code == 204:
                print("Webhook sent successfully.")
            else:
                print("Error sending webhook:", response.text)
        except Exception as e:
            print("Webhook exception:", e)

        return "HWID saved and Discord notification sent!"
    
    return render_template('panel.html', username=username)

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('admin_username', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
 app.run(host='0.0.0.0', port=1020)