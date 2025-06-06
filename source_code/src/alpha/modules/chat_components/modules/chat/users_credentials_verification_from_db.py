from flask import Flask, request, jsonify
import sqlite3
import requests
import jwt
from functools import wraps
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta


app = Flask(__name__)

# Configuration
CHAT_DATABASE = 'chat.db'
USER_API_URL = 'http://localhost:5000'  # User registration API URL
AUTH_API_URL = 'http://localhost:3000'  # Authentication API URL
JWT_SECRET_KEY = 'your-secret-key-change-this-in-production'  # Should match auth_app.py


def verify_user_credentials(user_id, password):
    """Verify user credentials against the user registration database (Legacy)"""
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
            return False

        cursor = user_conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()

        print(f"Database query result for user {user_id}: {'Found' if result else 'Not found'}")

        user_conn.close()

        if result:
            password_match = check_password_hash(result[0], password)
            print(f"Password verification for {user_id}: {'Success' if password_match else 'Failed'}")
            return password_match
        return False

    except Exception as e:
        print(f"Error verifying credentials: {e}")
        return False
