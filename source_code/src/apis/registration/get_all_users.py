from flask import Flask, request, jsonify,Blueprint
import sqlite3
import os
from werkzeug.security import generate_password_hash
from modules.registration.automatically_make_user_id import get_next_user_id
from modules.registration.init_db import init_db


# Database configuration
DATABASE = 'users.db'


get_whole_users=Blueprint('get_whole_users',__name__)


@get_whole_users.route('/users', methods=['GET'])
def get_all_users():
    """Get all registered users (for testing purposes)"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT user_id, username, created_at
            FROM users
            ORDER BY id ASC
        ''')

        users = []
        for row in cursor.fetchall():
            users.append({
                'user_id': row[0],
                'username': row[1],
                'created_at': row[2]
            })

        conn.close()

        return jsonify({
            'users': users,
            'total_users': len(users)
        }), 200

    except Exception as e:
        return jsonify({
            'error': f'Failed to fetch users: {str(e)}'
        }), 500
