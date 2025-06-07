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

documentation=Blueprint('documentation',__name__)

# Secret key for JWT encoding/decoding (in production, use environment variable)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'


@documentation.route('/', methods=['GET'])
def home():
    """Home endpoint with API documentation"""
    return jsonify({
        'message': 'Flask JWT Authentication API - Database Integrated',
        'endpoints': {
            'POST /login': 'Login with user_id and password to get JWT token',
            'GET /verify-token': 'Verify if JWT token is valid (requires Authorization header)',
            'GET /protected': 'Example protected route (requires Authorization header)',
            'POST /refresh-token': 'Refresh JWT token (requires Authorization header)',
            'GET /user/<user_id>': 'Get user information',
            'POST /validate-user': 'Validate user credentials'
        },
        'usage': {
            'login': {
                'method': 'POST',
                'url': '/login',
                'body': {
                    'user_id': 'your_user_id',
                    'password': 'your_password'
                }
            },
            'protected_access': {
                'method': 'GET',
                'url': '/protected',
                'headers': {
                    'Authorization': 'Bearer <your-jwt-token>'
                }
            }
        }
    }), 200
