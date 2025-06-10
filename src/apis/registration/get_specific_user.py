from flask import Flask, request, jsonify,Blueprint
import sqlite3
import os
from werkzeug.security import generate_password_hash
from modules.registration.automatically_make_user_id import get_next_user_id
from modules.registration.init_db import init_db


# Database configuration
DATABASE = 'users.db'

get_specific_user=Blueprint('get_specific_user',__name__)


@get_specific_user.route('/user/<user_id>', methods=['GET'])
def get_user(user_id):
    """Get specific user by user_id"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT user_id, username, created_at
            FROM users
            WHERE user_id = ?
        ''', (user_id,))

        user = cursor.fetchone()
        conn.close()

        if user:
            return jsonify({
                'user_id': user[0],
                'username': user[1],
                'created_at': user[2]
            }), 200
        else:
            return jsonify({
                'error': 'User not found'
            }), 404

    except Exception as e:
        return jsonify({
            'error': f'Failed to fetch user: {str(e)}'
        }), 500
