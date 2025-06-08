from flask import Flask, request, jsonify, Blueprint
import sqlite3
import requests
import jwt
from functools import wraps
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
from modules.chat.token_verification_and_autorization import token_required
from modules.chat.search_user_by_username import search_user_by_username

search_user = Blueprint('search_user', __name__)

# Configuration
CHAT_DATABASE = 'chat.db'
USER_API_URL = 'http://localhost:5000'  # User registration API URL
AUTH_API_URL = 'http://localhost:3000'  # Authentication API URL
JWT_SECRET_KEY = 'your-secret-key-change-this-in-production'  # Should match auth_app.py



@search_user.route('/auth/search_user', methods=['GET'])
@token_required
def search_user_auth(current_user):
    """Search for a user by username using JWT authentication"""
    try:
        # Get username from header
        username = request.headers.get('username')
        
        if not username:
            return jsonify({
                'error': 'Username is required in header'
            }), 400

        # Search for the user in the database
        user_data = search_user_by_username(username)
        
        if not user_data:
            return jsonify({
                'error': 'User not found',
                'searched_username': username
            }), 404

        return jsonify({
            'message': 'User found successfully',
            'user_data': {
                'user_id': user_data['user_id'],
                'username': user_data['username']
            },
            'searched_by': current_user['username'],
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        return jsonify({
            'error': f'Failed to search user: {str(e)}'
        }), 500


@search_user.route('/auth/search_user_by_id', methods=['GET'])
@token_required
def search_user_by_id_auth(current_user):
    """Search for a user by user_id using JWT authentication (bonus endpoint)"""
    try:
        # Get user_id from header
        search_user_id = request.headers.get('user_id')
        
        if not search_user_id:
            return jsonify({
                'error': 'user_id is required in header'
            }), 400

        # Try different possible paths for the users database
        possible_paths = ['users.db', '../users.db', './users.db']
        user_conn = None

        for path in possible_paths:
            try:
                user_conn = sqlite3.connect(path)
                cursor = user_conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
                if cursor.fetchone():
                    break
                user_conn.close()
                user_conn = None
            except:
                if user_conn:
                    user_conn.close()
                continue

        if not user_conn:
            return jsonify({'error': 'Could not access users database'}), 500

        cursor = user_conn.cursor()
        cursor.execute("SELECT user_id, username FROM users WHERE user_id = ?", (search_user_id,))
        result = cursor.fetchone()
        user_conn.close()

        if not result:
            return jsonify({
                'error': 'User not found',
                'searched_user_id': search_user_id
            }), 404

        return jsonify({
            'message': 'User found successfully',
            'user_data': {
                'user_id': result[0],
                'username': result[1]
            },
            'searched_by': current_user['username'],
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        return jsonify({
            'error': f'Failed to search user: {str(e)}'
        }), 500
