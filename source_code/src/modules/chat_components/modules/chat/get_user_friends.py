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



def get_user_friends(user_id):
    """Get all friends for a specific user"""
    try:
        init_friends_db()
        conn = sqlite3.connect(FRIENDS_DATABASE)
        cursor = conn.cursor()

        # Get friends where user is either user1 or user2
        cursor.execute('''
            SELECT
                friendship_id,
                CASE
                    WHEN user1_id = ? THEN user2_id
                    ELSE user1_id
                END as friend_id,
                CASE
                    WHEN user1_id = ? THEN user2_username
                    ELSE user1_username
                END as friend_username,
                friendship_date
            FROM friends
            WHERE user1_id = ? OR user2_id = ?
            ORDER BY friendship_date DESC
        ''', (user_id, user_id, user_id, user_id))

        friends = []
        for row in cursor.fetchall():
            friends.append({
                'friendship_id': row[0],
                'friend_id': row[1],
                'friend_username': row[2],
                'friendship_date': row[3]
            })

        conn.close()
        return friends

    except Exception as e:
        print(f"Error getting user friends: {e}")
        return []
