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

get_users=Blueprint('get_users',__name__)

# Secret key for JWT encoding/decoding (in production, use environment variable)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'


@get_users.route('/user/<user_id>', methods=['GET'])
def get_user_info(user_id):
    """Get user information (for integration with chat API)"""
    try:
        user = get_user_from_database(user_id)
        if user:
            return jsonify({
                'user_id': user['user_id'],
                'username': user['username'],
                'exists': True
            }), 200
        else:
            return jsonify({
                'message': 'User not found',
                'exists': False
            }), 404
    except Exception as e:
        return jsonify({'message': 'Error fetching user information'}), 500
