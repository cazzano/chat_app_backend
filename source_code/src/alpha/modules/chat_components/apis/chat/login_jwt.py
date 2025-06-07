from flask import Flask, request, jsonify, Blueprint
import sqlite3
import requests
import jwt
from functools import wraps
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
from modules.chat.init_chat_db import init_chat_db
from modules.chat.token_verification_and_autorization import token_required
from modules.chat.users_credentials_verification_from_db import verify_user_credentials
from modules.chat.check_user_exist_from_db import check_user_exists


# Configuration
CHAT_DATABASE = 'chat.db'
USER_API_URL = 'http://localhost:5000'  # User registration API URL
AUTH_API_URL = 'http://localhost:3000'  # Authentication API URL
JWT_SECRET_KEY = 'your-secret-key-change-this-in-production'  # Should match auth_app.py


login_jwt=Blueprint('login_jwt',__name__)



@login_jwt.route('/login', methods=['POST'])
def login():
    """Login endpoint to authenticate user and get JWT token"""
    try:
        data = request.get_json()

        if not data or not data.get('user_id') or not data.get('password'):
            return jsonify({'error': 'User ID and password are required!'}), 400

        user_id = data['user_id']
        password = data['password']

        # Verify credentials against local database
        if verify_user_credentials(user_id, password):
            # Generate JWT token locally (same as auth service)
            token = jwt.encode({
                'user_id': user_id,
                'username': user_id,  # Using user_id as username for simplicity
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, JWT_SECRET_KEY, algorithm='HS256')

            return jsonify({
                'message': 'Login successful!',
                'token': token,
                'user_id': user_id,
                'expires_in': '24 hours'
            }), 200
        else:
            return jsonify({'error': 'Invalid user ID or password!'}), 401

    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'error': 'An error occurred during login'}), 500
