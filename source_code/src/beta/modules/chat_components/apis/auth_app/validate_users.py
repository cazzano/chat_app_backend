from flask import Flask, request, jsonify,Blueprint
import jwt
import datetime
from functools import wraps
import sqlite3
from werkzeug.security import check_password_hash
from modules.auth_app.get_user_from_db import get_user_from_database
from modules.auth_app.token_reguired import token_required
from modules.auth_app.verify_user_credentials import verify_user_credentials

app = Flask(__name__)

validate_users=Blueprint('validate_users',__name__)

# Secret key for JWT encoding/decoding (in production, use environment variable)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'


@validate_users.route('/validate-user', methods=['POST'])
def validate_user():
    """Validate user credentials (for chat API integration)"""
    try:
        data = request.get_json()
        if not data or not data.get('user_id') or not data.get('password'):
            return jsonify({'valid': False, 'message': 'User ID and password required'}), 400

        user = verify_user_credentials(data['user_id'], data['password'])
        if user:
            return jsonify({
                'valid': True,
                'user_id': user['user_id'],
                'username': user['username']
            }), 200
        else:
            return jsonify({'valid': False, 'message': 'Invalid credentials'}), 401

    except Exception as e:
        return jsonify({'valid': False, 'message': 'Validation error'}), 500
