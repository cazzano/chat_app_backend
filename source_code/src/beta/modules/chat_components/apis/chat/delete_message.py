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



delete_message=Blueprint('delete_message',__name__)

@delete_message.route('/auth/delete_message/<message_id>', methods=['DELETE'])
@token_required
def delete_message_auth(current_user, message_id):
    """Delete a message (only sender can delete)"""
    try:
        user_id = current_user['user_id']

        conn = sqlite3.connect(CHAT_DATABASE)
        cursor = conn.cursor()

        # Check if message exists and user is the sender
        cursor.execute('''
            SELECT sender_user_id FROM messages WHERE id = ?
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
                'error': 'You can only delete messages you sent'
            }), 403

        # Delete the message
        cursor.execute('''
            DELETE FROM messages WHERE id = ?
        ''', (message_id,))

        conn.commit()
        conn.close()

        return jsonify({
            'message': 'Message deleted successfully'
        }), 200

    except Exception as e:
        return jsonify({
            'error': f'Failed to delete message: {str(e)}'
        }), 500
