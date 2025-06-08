from flask import Flask, request, jsonify,Blueprint
import sqlite3
import requests
import json
from datetime import datetime
from modules.save_token.init_db import init_db
from modules.save_token.get_db import get_db_connection

save_token_=Blueprint('save_token_',__name__)


@save_token_.route('/save_token', methods=['POST'])
def save_token():
    """
    Fetch token from login API and save to database
    Expected JSON body: {"username": "cazzano", "password": "pass123"}
    """
    try:
        # Get username and password from request
        data = request.get_json()
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({'error': 'Username and password are required'}), 400

        username = data['username']
        password = data['password']

        # Fetch token from login API
        login_url = 'http://localhost:2000/login'
        login_payload = {
            'username': username,
            'password': password
        }

        headers = {'Content-Type': 'application/json'}

        # Make request to login API
        response = requests.post(login_url, json=login_payload, headers=headers)

        if response.status_code != 200:
            return jsonify({'error': 'Login failed', 'details': response.text}), response.status_code

        # Parse response
        login_data = response.json()

        # Extract required fields
        token = login_data.get('token')
        username = login_data.get('username')
        user_id = login_data.get('user_id')

        if not all([token, username, user_id]):
            return jsonify({'error': 'Missing required fields in login response'}), 400

        # Save to database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert or update token information
        cursor.execute('''
            INSERT OR REPLACE INTO tokens (user_id, username, token, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, username, token))

        conn.commit()
        conn.close()

        return jsonify({
            'message': 'Token saved successfully',
            'user_id': user_id,
            'username': username,
            'saved_at': datetime.now().isoformat()
        }), 200

    except requests.exceptions.RequestException as e:
        return jsonify({'error': 'Failed to connect to login API', 'details': str(e)}), 500
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500
