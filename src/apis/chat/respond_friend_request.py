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

respond_friend_request=Blueprint('respond_friend_request',__name__)



@respond_friend_request.route('/auth/respond_friend_request', methods=['POST'])
@token_required
def respond_friend_request_auth(current_user):
    """Accept or reject a friend request using friend's username"""
    try:
        data = request.get_json()
        if not data or 'username' not in data or 'action' not in data:
            return jsonify({
                'error': 'Username and action (accept/reject) are required'
            }), 400

        friend_username = data['username']
        action = data['action'].lower()
        user_id = current_user['user_id']

        if action not in ['accept', 'reject']:
            return jsonify({
                'error': 'Action must be either "accept" or "reject"'
            }), 400

        # Get current user's username
        current_user_username = get_username_by_user_id(user_id)
        if not current_user_username:
            return jsonify({
                'error': 'Current user not found'
            }), 404

        # Get friend's user_id by username
        friend_info = get_user_by_username(friend_username)
        if not friend_info:
            return jsonify({
                'error': 'Friend username not found'
            }), 404

        friend_user_id = friend_info['user_id']

        conn = sqlite3.connect(FR_REQUESTS_DATABASE)
        cursor = conn.cursor()

        # Check if the request exists where friend is sender and current user is recipient
        cursor.execute('''
            SELECT request_id, sender_user_id, sender_username, recipient_user_id, status
            FROM friend_requests
            WHERE sender_user_id = ? AND recipient_user_id = ? AND status IN ('pending', 'rejected')
        ''', (friend_user_id, user_id))

        result = cursor.fetchone()
        if not result:
            conn.close()
            return jsonify({
                'error': 'No friend request found from this user (must be pending or previously rejected)'
            }), 404

        request_id = result[0]
        sender_username = result[2]
        current_status = result[4]

        # Check if already accepted
        if current_status == 'accepted':
            conn.close()
            return jsonify({
                'error': f'You are already friends with {sender_username}'
            }), 409

        # Update the request status
        new_status = 'accepted' if action == 'accept' else 'rejected'
        cursor.execute('''
            UPDATE friend_requests
            SET status = ?, timestamp = CURRENT_TIMESTAMP
            WHERE request_id = ?
        ''', (new_status, request_id))

        conn.commit()
        conn.close()

        # Handle friendship database based on action
        friendship_result = None
        if action == 'accept':
            # Add friendship to friends.db - This will make both users friends with each other
            success, result = add_friendship(user_id, current_user_username, friend_user_id, sender_username)
            if success:
                friendship_result = f"Friendship added to database (ID: {result})"
            else:
                friendship_result = f"Friendship already exists: {result}"
        else:  # action == 'reject'
            # Remove friendship from friends.db (in case it was previously accepted)
            if remove_friendship(user_id, friend_user_id):
                friendship_result = "Friendship removed from database"
            else:
                friendship_result = "No existing friendship to remove"

        # Get updated friend counts for both users
        user_friends_count = len(get_user_friends(user_id))
        friend_friends_count = len(get_user_friends(friend_user_id))

        # Create appropriate response message
        if current_status == 'rejected' and action == 'accept':
            message = f'Previously rejected friend request from {sender_username} has been accepted! You are now friends.'
        elif current_status == 'pending' and action == 'accept':
            message = f'Friend request from {sender_username} accepted successfully! You are now friends.'
        elif current_status == 'pending' and action == 'reject':
            message = f'Friend request from {sender_username} rejected successfully'
        else:  # rejected -> rejected
            message = f'Friend request from {sender_username} rejected again'

        return jsonify({
            'message': message,
            'request_id': request_id,
            'friend_username': friend_username,
            'action': action,
            'previous_status': current_status,
            'new_status': new_status,
            'friendship_result': friendship_result,
            'your_friends_count': user_friends_count,
            'their_friends_count': friend_friends_count
        }), 200

    except Exception as e:
        return jsonify({
            'error': f'Failed to respond to friend request: {str(e)}'
        }), 500
