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
