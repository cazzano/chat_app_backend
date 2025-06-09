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
FR_REQUESTS_DATABASE = 'fr_requests.db'
FRIENDS_DATABASE = 'friends.db'
USER_API_URL = 'http://localhost:5000'  # User registration API URL
AUTH_API_URL = 'http://localhost:3000'  # Authentication API URL
JWT_SECRET_KEY = 'your-secret-key-change-this-in-production'  # Should match auth_app.py



def check_existing_friend_request(sender_user_id, recipient_user_id):
    """Check if a friend request already exists between two users"""
    try:
        conn = sqlite3.connect(FR_REQUESTS_DATABASE)
        cursor = conn.cursor()

        # Check for existing request in either direction
        cursor.execute('''
            SELECT request_id, status FROM friend_requests
            WHERE (sender_user_id = ? AND recipient_user_id = ?)
               OR (sender_user_id = ? AND recipient_user_id = ?)
        ''', (sender_user_id, recipient_user_id, recipient_user_id, sender_user_id))

        result = cursor.fetchone()
        conn.close()

        return result

    except Exception as e:
        print(f"Error checking existing friend request: {e}")
        return None
