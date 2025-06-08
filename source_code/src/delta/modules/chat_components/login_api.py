from flask import Flask, request, jsonify, Blueprint
import sqlite3
import requests
import jwt
from functools import wraps
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta


# Configuration
CHAT_DATABASE = 'chat.db'
USER_API_URL = 'http://localhost:5000'  # User registration API URL
AUTH_API_URL = 'http://localhost:3000'  # Authentication API URL
JWT_SECRET_KEY = 'your-secret-key-change-this-in-production'  # Should match auth_app.py


login_jwt = Blueprint('login_jwt', __name__)


def verify_user_credentials_by_username(username, password):
    """Verify user credentials by username and return user_id if successful"""
    try:
        # Try different possible paths for the users database
        possible_paths = ['users.db', '../users.db', './users.db']
        user_conn = None

        for path in possible_paths:
            try:
                user_conn = sqlite3.connect(path)
                cursor = user_conn.cursor()
                # Test if the table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
                if cursor.fetchone():
                    print(f"Found users database at: {path}")
                    break
                user_conn.close()
                user_conn = None
            except:
                if user_conn:
                    user_conn.close()
                continue

        if not user_conn:
            print("Could not find users database")
            return None, False

        cursor = user_conn.cursor()
        # Query by username to get both user_id and password_hash
        cursor.execute("SELECT user_id, password_hash FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()

        print(f"Database query result for username {username}: {'Found' if result else 'Not found'}")

        user_conn.close()

        if result:
            user_id, stored_password_hash = result
            password_match = check_password_hash(stored_password_hash, password)
            print(f"Password verification for {username}: {'Success' if password_match else 'Failed'}")
            
            if password_match:
                return user_id, True
            else:
                return None, False
        return None, False

    except Exception as e:
        print(f"Error verifying credentials: {e}")
        return None, False


@login_jwt.route('/login', methods=['POST'])
def login():
    """Login endpoint to authenticate user with username and get JWT token"""
    try:
        data = request.get_json()

        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Username and password are required!'}), 400

        username = data['username']
        password = data['password']

        # Verify credentials against local database using username
        user_id, is_valid = verify_user_credentials_by_username(username, password)
        
        if is_valid and user_id:
            # Generate JWT token with user_id (to maintain compatibility with send_message)
            token = jwt.encode({
                'user_id': user_id,  # Keep user_id for send_message compatibility
                'username': username,  # Include username for reference
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, JWT_SECRET_KEY, algorithm='HS256')

            return jsonify({
                'message': 'Login successful!',
                'token': token,
                'user_id': user_id,  # Return user_id for client reference
                'username': username,  # Return username for client reference
                'expires_in': '24 hours'
            }), 200
        else:
            return jsonify({'error': 'Invalid username or password!'}), 401

    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'error': 'An error occurred during login'}), 500
