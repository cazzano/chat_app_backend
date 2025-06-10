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



get_messages=Blueprint('get_messages',__name__)


# Configuration
CHAT_DATABASE = 'chat.db'
USER_API_URL = 'http://localhost:5000'  # User registration API URL
AUTH_API_URL = 'http://localhost:3000'  # Authentication API URL
JWT_SECRET_KEY = 'your-secret-key-change-this-in-production'  # Should match auth_app.py


@get_messages.route('/auth/messages', methods=['GET'])
@token_required
def get_messages_auth(current_user):
    """Get messages for authenticated user"""
    try:
        user_id = current_user['user_id']

        conn = sqlite3.connect(CHAT_DATABASE)
        cursor = conn.cursor()

        # Get all messages where user is either sender or recipient
        cursor.execute('''
            SELECT id, sender_user_id, recipient_user_id, message, timestamp, is_read
            FROM messages
            WHERE sender_user_id = ? OR recipient_user_id = ?
            ORDER BY timestamp DESC
        ''', (user_id, user_id))

        messages = []
        for row in cursor.fetchall():
            messages.append({
                'message_id': row[0],
                'sender': row[1],
                'recipient': row[2],
                'message': row[3],
                'timestamp': row[4],
                'is_read': bool(row[5]),
                'direction': 'sent' if row[1] == user_id else 'received'
            })

        conn.close()

        return jsonify({
            'messages': messages,
            'total_messages': len(messages)
        }), 200

    except Exception as e:
        return jsonify({
            'error': f'Failed to fetch messages: {str(e)}'
        }), 500
