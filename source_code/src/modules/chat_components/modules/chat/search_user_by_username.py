from flask import Flask, request, jsonify, Blueprint
import sqlite3
import requests
import jwt
from functools import wraps
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
from modules.chat.token_verification_and_autorization import token_required

# Configuration
CHAT_DATABASE = 'chat.db'
USER_API_URL = 'http://localhost:5000'  # User registration API URL
AUTH_API_URL = 'http://localhost:3000'  # Authentication API URL
JWT_SECRET_KEY = 'your-secret-key-change-this-in-production'  # Should match auth_app.py


def search_user_by_username(username):
    """Search for a user by username in the users database"""
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
            return None

        cursor = user_conn.cursor()
        # Search for user by username (assuming there's a username column)
        # If your users table uses 'user_id' as username, modify the query accordingly
        cursor.execute("SELECT user_id, username FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()

        print(f"Database query result for username {username}: {'Found' if result else 'Not found'}")

        user_conn.close()

        if result:
            return {
                'user_id': result[0],
                'username': result[1]
            }
        return None

    except Exception as e:
        print(f"Error searching user by username: {e}")
        return None
