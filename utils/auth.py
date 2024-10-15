from werkzeug.security import generate_password_hash, check_password_hash
from flask import session
from datetime import timedelta

# Simulated user database
users = {}

def login_user(username, password, remember_me):
    user = users.get(username)
    if user and check_password_hash(user['password'], password):
        session['username'] = username

        if remember_me:
            session.permanent = True  # Sets a long expiration time
            session.permanent_session_lifetime = timedelta(days=7)

        return True, "Login successful!"
    return False, "Invalid username or password."

def signup_user(username, password, confirm_password):
    if not username or not password or not confirm_password:
        return False, "All fields are required."

    if password != confirm_password:
        return False, "Passwords do not match."

    if username in users:
        return False, "Username already exists."

    users[username] = {'password': generate_password_hash(password)}
    return True, "Account created successfully. Please login."

def logout_user():
    session.pop('username', None)
