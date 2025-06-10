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


def init_friend_requests_db():
    """Initialize the friend requests database"""
    try:
        conn = sqlite3.connect(FR_REQUESTS_DATABASE)
        cursor = conn.cursor()

        # Create friend_requests table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS friend_requests (
                request_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_user_id TEXT NOT NULL,
                sender_username TEXT NOT NULL,
                recipient_user_id TEXT NOT NULL,
                recipient_username TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                request_data TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sender_user_id) REFERENCES users(user_id),
                FOREIGN KEY (recipient_user_id) REFERENCES users(user_id),
                UNIQUE(sender_user_id, recipient_user_id)
            )
        ''')

        conn.commit()
        conn.close()
        print("Friend requests database initialized successfully")

    except Exception as e:
        print(f"Error initializing friend requests database: {e}")
