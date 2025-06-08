from flask import Flask, request, jsonify,Blueprint
import jwt
import datetime
from functools import wraps
import sqlite3
from werkzeug.security import check_password_hash
from modules.auth_app.get_user_from_db import get_user_from_database
from modules.auth_app.token_reguired import token_required
from modules.auth_app.verify_user_credentials import verify_user_credentials
from apis.auth_app.login_jwt import login_jwt

app = Flask(__name__)

app.register_blueprint(login_jwt)


# Secret key for JWT encoding/decoding (in production, use environment variable)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'

@app.route('/debug/users', methods=['GET'])
def debug_users():
    """Debug endpoint to list all users"""
    try:
        # Try different possible paths for the users database
        possible_paths = ['users.db', '../users.db', './users.db']
        user_conn = None

        for path in possible_paths:
            try:
                user_conn = sqlite3.connect(path)
                cursor = user_conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
                if cursor.fetchone():
                    cursor.execute("SELECT user_id, username FROM users")
                    users = cursor.fetchall()
                    user_conn.close()
                    
                    return jsonify({
                        'database_path': path,
                        'users': [{'user_id': u[0], 'username': u[1]} for u in users]
                    }), 200
                    
                user_conn.close()
            except Exception as e:
                if user_conn:
                    user_conn.close()
                continue

        return jsonify({'error': 'Could not find users database'}), 404

    except Exception as e:
        return jsonify({'error': f'Debug failed: {str(e)}'}), 500

if __name__ == '__main__':
    print("Flask JWT Authentication App - Database Integrated")
    print("=" * 50)
    print("Available endpoints:")
    print("- POST /login - Login to get JWT token")
    print("- GET /verify-token - Verify token validity")
    print("- GET /protected - Protected route example")
    print("- POST /refresh-token - Refresh your token")
    print("- GET /user/<user_id> - Get user information")
    print("- POST /validate-user - Validate credentials")
    print("- GET /debug/users - List all users (debug)")
    print("=" * 50)
    print("Now integrated with users.db database!")
    print("Use your database user_id and password to login.")
    print("=" * 50)

    app.run(debug=True, host='0.0.0.0', port=3000)
