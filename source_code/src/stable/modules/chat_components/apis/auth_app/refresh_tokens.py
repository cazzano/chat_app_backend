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


refresh_tokens=Blueprint('refresh_tokens',__name__)

# Secret key for JWT encoding/decoding (in production, use environment variable)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'


@refresh_tokens.route('/refresh-token', methods=['POST'])
@token_required
def refresh_token(current_user):
    """Refresh JWT token"""
    try:
        # Generate new token
        new_token = jwt.encode({
            'user_id': current_user['user_id'],
            'username': current_user['username'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm='HS256')

        return jsonify({
            'message': 'Token refreshed successfully!',
            'token': new_token,
            'user_id': current_user['user_id'],
            'username': current_user['username'],
            'expires_in': '24 hours'
        }), 200

    except Exception as e:
        return jsonify({'message': 'An error occurred during token refresh'}), 500
