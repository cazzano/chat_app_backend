from flask import Flask, request, jsonify, Blueprint
import sqlite3
import requests
import jwt
from functools import wraps
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
from modules.chat.token_verification_and_autorization import token_required
from modules.chat.init_friends_db import init_friends_db


# Configuration
CHAT_DATABASE = 'chat.db'
FR_REQUESTS_DATABASE = 'fr_requests.db'
FRIENDS_DATABASE = 'friends.db'
USER_API_URL = 'http://localhost:5000'  # User registration API URL
AUTH_API_URL = 'http://localhost:3000'  # Authentication API URL
JWT_SECRET_KEY = 'your-secret-key-change-this-in-production'  # Should match auth_app.py



def add_friendship(user1_id, user1_username, user2_id, user2_username):
    """Add friendship to friends database"""
    try:
        init_friends_db()
        conn = sqlite3.connect(FRIENDS_DATABASE)
        cursor = conn.cursor()

        # Check if friendship already exists (in either direction)
        cursor.execute('''
            SELECT friendship_id FROM friends
            WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)
        ''', (user1_id, user2_id, user2_id, user1_id))

        if cursor.fetchone():
            conn.close()
            return False, "Friendship already exists"

        # Add friendship (always store in alphabetical order by user_id for consistency)
        if user1_id < user2_id:
            cursor.execute('''
                INSERT INTO friends (user1_id, user1_username, user2_id, user2_username)
                VALUES (?, ?, ?, ?)
            ''', (user1_id, user1_username, user2_id, user2_username))
        else:
            cursor.execute('''
                INSERT INTO friends (user1_id, user1_username, user2_id, user2_username)
                VALUES (?, ?, ?, ?)
            ''', (user2_id, user2_username, user1_id, user1_username))

        friendship_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return True, friendship_id

    except Exception as e:
        print(f"Error adding friendship: {e}")
        return False, str(e)
