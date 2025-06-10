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


get_friend_requests = Blueprint('get_friend_requests', __name__)

@get_friend_requests.route('/auth/get_friend_requests', methods=['GET'])
@token_required
def get_friend_requests_auth(current_user):
    """Get all friend requests for the authenticated user (both sent and received)"""
    try:
        user_id = current_user['user_id']
        
        conn = sqlite3.connect(FR_REQUESTS_DATABASE)
        cursor = conn.cursor()
        
        # Get all friend requests where user is either sender or recipient
        cursor.execute('''
            SELECT 
                request_id,
                sender_user_id,
                sender_username,
                recipient_user_id,
                recipient_username,
                status,
                request_data,
                timestamp
            FROM friend_requests 
            WHERE sender_user_id = ? OR recipient_user_id = ?
            ORDER BY timestamp DESC
        ''', (user_id, user_id))
        
        requests_data = cursor.fetchall()
        conn.close()
        
        if not requests_data:
            return jsonify({
                'message': 'No friend requests found',
                'incoming_requests': [],
                'outgoing_requests': []
            }), 200
        
        incoming_requests = []
        outgoing_requests = []
        
        for req in requests_data:
            request_info = {
                'request_id': req[0],
                'sender_user_id': req[1],
                'sender_username': req[2],
                'recipient_user_id': req[3],
                'recipient_username': req[4],
                'status': req[5],
                'request_data': req[6],
                'timestamp': req[7]
            }
            
            # Categorize as incoming or outgoing based on current user
            if req[3] == user_id:  # recipient_user_id matches current user
                incoming_requests.append(request_info)
            elif req[1] == user_id:  # sender_user_id matches current user
                outgoing_requests.append(request_info)
        
        return jsonify({
            'message': 'Friend requests retrieved successfully',
            'user_id': user_id,
            'incoming_requests': incoming_requests,
            'outgoing_requests': outgoing_requests,
            'total_incoming': len(incoming_requests),
            'total_outgoing': len(outgoing_requests)
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Failed to retrieve friend requests: {str(e)}'
        }), 500


@get_friend_requests.route('/auth/get_incoming_friend_requests', methods=['GET'])
@token_required
def get_incoming_friend_requests_auth(current_user):
    """Get only incoming friend requests for the authenticated user"""
    try:
        user_id = current_user['user_id']
        
        conn = sqlite3.connect(FR_REQUESTS_DATABASE)
        cursor = conn.cursor()
        
        # Get incoming friend requests (where user is recipient)
        cursor.execute('''
            SELECT 
                request_id,
                sender_user_id,
                sender_username,
                recipient_user_id,
                recipient_username,
                status,
                request_data,
                timestamp
            FROM friend_requests 
            WHERE recipient_user_id = ?
            ORDER BY timestamp DESC
        ''', (user_id,))
        
        requests_data = cursor.fetchall()
        conn.close()
        
        incoming_requests = []
        for req in requests_data:
            incoming_requests.append({
                'request_id': req[0],
                'sender_user_id': req[1],
                'sender_username': req[2],
                'recipient_user_id': req[3],
                'recipient_username': req[4],
                'status': req[5],
                'request_data': req[6],
                'timestamp': req[7]
            })
        
        return jsonify({
            'message': 'Incoming friend requests retrieved successfully',
            'user_id': user_id,
            'incoming_requests': incoming_requests,
            'total_incoming': len(incoming_requests)
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Failed to retrieve incoming friend requests: {str(e)}'
        }), 500


@get_friend_requests.route('/auth/get_outgoing_friend_requests', methods=['GET'])
@token_required
def get_outgoing_friend_requests_auth(current_user):
    """Get only outgoing friend requests for the authenticated user"""
    try:
        user_id = current_user['user_id']
        
        conn = sqlite3.connect(FR_REQUESTS_DATABASE)
        cursor = conn.cursor()
        
        # Get outgoing friend requests (where user is sender)
        cursor.execute('''
            SELECT 
                request_id,
                sender_user_id,
                sender_username,
                recipient_user_id,
                recipient_username,
                status,
                request_data,
                timestamp
            FROM friend_requests 
            WHERE sender_user_id = ?
            ORDER BY timestamp DESC
        ''', (user_id,))
        
        requests_data = cursor.fetchall()
        conn.close()
        
        outgoing_requests = []
        for req in requests_data:
            outgoing_requests.append({
                'request_id': req[0],
                'sender_user_id': req[1],
                'sender_username': req[2],
                'recipient_user_id': req[3],
                'recipient_username': req[4],
                'status': req[5],
                'request_data': req[6],
                'timestamp': req[7]
            })
        
        return jsonify({
            'message': 'Outgoing friend requests retrieved successfully',
            'user_id': user_id,
            'outgoing_requests': outgoing_requests,
            'total_outgoing': len(outgoing_requests)
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Failed to retrieve outgoing friend requests: {str(e)}'
        }), 500


@get_friend_requests.route('/auth/get_pending_friend_requests', methods=['GET'])
@token_required
def get_pending_friend_requests_auth(current_user):
    """Get only pending friend requests for the authenticated user"""
    try:
        user_id = current_user['user_id']
        
        conn = sqlite3.connect(FR_REQUESTS_DATABASE)
        cursor = conn.cursor()
        
        # Get pending friend requests where user is either sender or recipient
        cursor.execute('''
            SELECT 
                request_id,
                sender_user_id,
                sender_username,
                recipient_user_id,
                recipient_username,
                status,
                request_data,
                timestamp
            FROM friend_requests 
            WHERE (sender_user_id = ? OR recipient_user_id = ?) AND status = 'pending'
            ORDER BY timestamp DESC
        ''', (user_id, user_id))
        
        requests_data = cursor.fetchall()
        conn.close()
        
        pending_incoming = []
        pending_outgoing = []
        
        for req in requests_data:
            request_info = {
                'request_id': req[0],
                'sender_user_id': req[1],
                'sender_username': req[2],
                'recipient_user_id': req[3],
                'recipient_username': req[4],
                'status': req[5],
                'request_data': req[6],
                'timestamp': req[7]
            }
            
            if req[3] == user_id:  # recipient_user_id matches current user
                pending_incoming.append(request_info)
            elif req[1] == user_id:  # sender_user_id matches current user
                pending_outgoing.append(request_info)
        
        return jsonify({
            'message': 'Pending friend requests retrieved successfully',
            'user_id': user_id,
            'pending_incoming': pending_incoming,
            'pending_outgoing': pending_outgoing,
            'total_pending_incoming': len(pending_incoming),
            'total_pending_outgoing': len(pending_outgoing)
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Failed to retrieve pending friend requests: {str(e)}'
        }), 500
