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



def remove_friendship(user1_id, user2_id):
    """Remove friendship from friends database"""
    try:
        conn = sqlite3.connect(FRIENDS_DATABASE)
        cursor = conn.cursor()

        # Remove friendship (check both directions)
        cursor.execute('''
            DELETE FROM friends
            WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)
        ''', (user1_id, user2_id, user2_id, user1_id))

        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted_count > 0

    except Exception as e:
        print(f"Error removing friendship: {e}")
        return False
