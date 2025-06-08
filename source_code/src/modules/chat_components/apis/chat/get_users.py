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


get_users=Blueprint('get_users',__name__)


@get_users.route('/auth/users', methods=['GET'])
@token_required
def get_users_auth(current_user):
    """Get list of all users (JWT authenticated)"""
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
                    break
                user_conn.close()
                user_conn = None
            except:
                if user_conn:
                    user_conn.close()
                continue

        if not user_conn:
            return jsonify({
                'error': 'Could not find users database'
            }), 500

        cursor = user_conn.cursor()
        cursor.execute("SELECT user_id, email, full_name, created_at FROM users")
        users = []

        for row in cursor.fetchall():
            users.append({
                'user_id': row[0],
                'email': row[1],
                'full_name': row[2],
                'created_at': row[3]
            })

        user_conn.close()

        return jsonify({
            'users': users,
            'total_users': len(users)
        }), 200

    except Exception as e:
        return jsonify({
            'error': f'Failed to fetch users: {str(e)}'
        }), 500
