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

protected=Blueprint('protected',__name__)

# Secret key for JWT encoding/decoding (in production, use environment variable)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'


@protected.route('/protected', methods=['GET'])
@token_required
def protected_route(current_user):
    """Example protected route"""
    return jsonify({
        'message': f'Hello {current_user["username"]}! This is a protected route.',
        'user_id': current_user['user_id'],
        'data': 'This is sensitive information only for authenticated users.'
    }), 200
