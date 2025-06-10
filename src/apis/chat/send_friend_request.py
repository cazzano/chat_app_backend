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



send_friend_request = Blueprint('send_friend_request', __name__)

@send_friend_request.route('/auth/send_friend_request', methods=['POST'])
@token_required
def send_friend_request_auth(current_user):
    """Send a friend request using JWT authentication"""
    try:
        # Initialize database if not exists
        init_friend_requests_db()
        
        data = request.get_json()
        if not data or 'username' not in data:
            return jsonify({
                'error': 'Username is required'
            }), 400

        target_username = data['username']
        sender_user_id = current_user['user_id']

        # Get sender's username
        sender_username = get_username_by_user_id(sender_user_id)
        if not sender_username:
            return jsonify({
                'error': 'Sender user not found'
            }), 404

        # Get recipient's user_id by username
        recipient_info = get_user_by_username(target_username)
        if not recipient_info:
            return jsonify({
                'error': 'Username not found'
            }), 404

        recipient_user_id = recipient_info['user_id']
        recipient_username = recipient_info['username']

        # Check if sender is trying to send friend request to themselves
        if sender_user_id == recipient_user_id:
            return jsonify({
                'error': 'Cannot send friend request to yourself'
            }), 400

        # Check if they are already friends
        if check_if_already_friends(sender_user_id, recipient_user_id):
            return jsonify({
                'error': f'You are already friends with {recipient_username}'
            }), 409

        # Check if friend request already exists
        existing_request = check_existing_friend_request(sender_user_id, recipient_user_id)
        if existing_request:
            status = existing_request[1]
            if status == 'pending':
                return jsonify({
                    'error': 'Friend request already pending between these users'
                }), 409

        # Create friend request JSON data
        friend_request_data = {
            f"friend_request_from_{sender_username}": "accept_or_reject"
        }

        # Store friend request in database
        conn = sqlite3.connect(FR_REQUESTS_DATABASE)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO friend_requests 
            (sender_user_id, sender_username, recipient_user_id, recipient_username, request_data, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
        ''', (sender_user_id, sender_username, recipient_user_id, recipient_username, str(friend_request_data)))

        request_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return jsonify({
            'message': 'Friend request sent successfully',
            'request_id': request_id,
            'sender': sender_username,
            'recipient': recipient_username,
            'request_data': friend_request_data,
            'timestamp': datetime.now().isoformat()
        }), 201

    except Exception as e:
        return jsonify({
            'error': f'Failed to send friend request: {str(e)}'
        }), 500


