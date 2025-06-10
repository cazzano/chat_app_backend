from flask import Flask, request, jsonify
import jwt
import datetime
from functools import wraps
import sqlite3
from werkzeug.security import check_password_hash

app = Flask(__name__)

# Secret key for JWT encoding/decoding (in production, use environment variable)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'


def verify_user_credentials(user_id, password):
    """Verify user credentials against the user database"""
    try:
        user = get_user_from_database(user_id)
        if user and check_password_hash(user['password_hash'], password):
            return user
        return None
    except Exception as e:
        print(f"Error verifying credentials: {e}")
        return None
