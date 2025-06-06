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


# Configuration
CHAT_DATABASE = 'chat.db'
USER_API_URL = 'http://localhost:5000'  # User registration API URL
AUTH_API_URL = 'http://localhost:3000'  # Authentication API URL
JWT_SECRET_KEY = 'your-secret-key-change-this-in-production'  # Should match auth_app.py


mark_as_read=Blueprint('mark_as_read',__name__)

@mark_as_read.route('/auth/mark_read/<message_id>', methods=['PUT'])
@token_required
def mark_message_read_auth(current_user, message_id):
    """Mark a message as read using JWT authentication"""
    try:
        user_id = current_user['user_id']

        conn = sqlite3.connect(CHAT_DATABASE)
        cursor = conn.cursor()

        # Check if message exists and user is the recipient
        cursor.execute('''
            SELECT recipient_user_id FROM messages WHERE id = ?
        ''', (message_id,))

        result = cursor.fetchone()
        if not result:
            conn.close()
            return jsonify({
                'error': 'Message not found'
            }), 404

        if result[0] != user_id:
            conn.close()
            return jsonify({
                'error': 'You can only mark your received messages as read'
            }), 403

        # Mark message as read
        cursor.execute('''
            UPDATE messages SET is_read = TRUE WHERE id = ?
        ''', (message_id,))

        conn.commit()
        conn.close()

        return jsonify({
            'message': 'Message marked as read'
        }), 200

    except Exception as e:
        return jsonify({
            'error': f'Failed to mark message as read: {str(e)}'
        }), 500
