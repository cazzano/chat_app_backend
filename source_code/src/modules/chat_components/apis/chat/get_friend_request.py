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

get_friend_request=Blueprint('get_friend_request',__name__)


@get_friend_request.route('/auth/get_friend_requests', methods=['GET'])
@token_required
def get_friend_requests_auth(current_user):
    """Get all friend requests for the authenticated user"""
    try:
        user_id = current_user['user_id']

        conn = sqlite3.connect(FR_REQUESTS_DATABASE)
        cursor = conn.cursor()

        # Get received friend requests (where user is recipient)
        cursor.execute('''
            SELECT request_id, sender_user_id, sender_username, request_data, status, timestamp
            FROM friend_requests
            WHERE recipient_user_id = ? AND status = 'pending'
            ORDER BY timestamp DESC
        ''', (user_id,))

        received_requests = []
        for row in cursor.fetchall():
            received_requests.append({
                'request_id': row[0],
                'sender_user_id': row[1],
                'sender_username': row[2],
                'request_data': eval(row[3]),  # Convert string back to dict
                'status': row[4],
                'timestamp': row[5]
            })

        # Get sent friend requests (where user is sender)
        cursor.execute('''
            SELECT request_id, recipient_user_id, recipient_username, request_data, status, timestamp
            FROM friend_requests
            WHERE sender_user_id = ?
            ORDER BY timestamp DESC
        ''', (user_id,))

        sent_requests = []
        for row in cursor.fetchall():
            sent_requests.append({
                'request_id': row[0],
                'recipient_user_id': row[1],
                'recipient_username': row[2],
                'request_data': eval(row[3]),  # Convert string back to dict
                'status': row[4],
                'timestamp': row[5]
            })

        conn.close()

        return jsonify({
            'received_requests': received_requests,
            'sent_requests': sent_requests,
            'total_received': len(received_requests),
            'total_sent': len(sent_requests)
        }), 200

    except Exception as e:
        return jsonify({
            'error': f'Failed to get friend requests: {str(e)}'
        }), 500
