from flask import Flask, request, jsonify, Blueprint
import sqlite3
import requests
import jwt
from functools import wraps
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
from modules.chat.token_verification_and_autorization import token_required
from modules.chat.init_friends_db import init_friends_db
from modules.chat.init_request_db import init_friend_requests_db
from modules.chat.remove_friendship import remove_friendship
from modules.chat.get_user_friends import get_user_friends
from modules.chat.get_user_by_username import get_user_by_username
from modules.chat.add_friendship import add_friendship
from modules.chat.check_existing_friend_request import check_existing_friend_request
from modules.chat.check_if_already_friends import check_if_already_friends
from modules.chat.get_user_by_userid import get_username_by_user_id


# Configuration
CHAT_DATABASE = 'chat.db'
FR_REQUESTS_DATABASE = 'fr_requests.db'
FRIENDS_DATABASE = 'friends.db'
USER_API_URL = 'http://localhost:5000'  # User registration API URL
AUTH_API_URL = 'http://localhost:3000'  # Authentication API URL
JWT_SECRET_KEY = 'your-secret-key-change-this-in-production'  # Should match auth_app.py

get_friends=Blueprint('get_friends',__name__)


def init_friends_db():
    """Initialize the friends database"""
    try:
        conn = sqlite3.connect(FRIENDS_DATABASE)
        cursor = conn.cursor()

        # Create friends table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS friends (
                friendship_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id TEXT NOT NULL,
                user1_username TEXT NOT NULL,
                user2_id TEXT NOT NULL,
                user2_username TEXT NOT NULL,
                friendship_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user1_id) REFERENCES users(user_id),
                FOREIGN KEY (user2_id) REFERENCES users(user_id),
                UNIQUE(user1_id, user2_id),
                UNIQUE(user2_id, user1_id)
            )
        ''')

        conn.commit()
        conn.close()
        print("Friends database initialized successfully")

    except Exception as e:
        print(f"Error initializing friends database: {e}")


@get_friends.route('/auth/get_friends', methods=['GET'])
@token_required
def get_friends_auth(current_user):
    """Get all friends for the authenticated user"""
    try:
        user_id = current_user['user_id']
        username = get_username_by_user_id(user_id)

        if not username:
            return jsonify({
                'error': 'User not found'
            }), 404

        # Get user's friends
        friends = get_user_friends(user_id)

        return jsonify({
            'user_id': user_id,
            'username': username,
            'friends': friends,
            'total_friends': len(friends)
        }), 200

    except Exception as e:
        return jsonify({
            'error': f'Failed to get friends: {str(e)}'
        }), 500
