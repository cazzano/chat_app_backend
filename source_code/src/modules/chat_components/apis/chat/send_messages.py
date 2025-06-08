from flask import Flask, request, jsonify, Blueprint
import sqlite3
import requests
import jwt
from functools import wraps
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
from modules.chat.check_user_exist_from_db import check_user_exists
from modules.chat.token_verification_and_autorization import token_required


send_messages=Blueprint('send_messages',__name__)

# Configuration
CHAT_DATABASE = 'chat.db'
USER_API_URL = 'http://localhost:5000'  # User registration API URL
AUTH_API_URL = 'http://localhost:3000'  # Authentication API URL
JWT_SECRET_KEY = 'your-secret-key-change-this-in-production'  # Should match auth_app.py



@send_messages.route('/auth/send_message', methods=['POST'])
@token_required
def send_message_auth(current_user):
    """Send a message using JWT authentication"""
    try:
        data = request.get_json()
        if not data or 'message' not in data or 'recipient_user_id' not in data:
            return jsonify({
                'error': 'Message content and recipient_user_id are required'
            }), 400

        message = data['message']
        recipient_user_id = data['recipient_user_id']
        sender_user_id = current_user['user_id']

        # Check if recipient exists
        if not check_user_exists(recipient_user_id):
            return jsonify({
                'error': 'Recipient user not found'
            }), 404

        # Check if sender is trying to send to themselves
        if sender_user_id == recipient_user_id:
            return jsonify({
                'error': 'Cannot send message to yourself'
            }), 400

        # Store message in chat database
        conn = sqlite3.connect(CHAT_DATABASE)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO messages (sender_user_id, recipient_user_id, message)
            VALUES (?, ?, ?)
        ''', (sender_user_id, recipient_user_id, message))

        message_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return jsonify({
            'message': 'Message sent successfully',
            'message_id': message_id,
            'sender': sender_user_id,
            'recipient': recipient_user_id,
            'timestamp': datetime.now().isoformat()
        }), 201

    except Exception as e:
        return jsonify({
            'error': f'Failed to send message: {str(e)}'
        }), 500
