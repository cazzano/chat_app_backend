from flask import Flask, request, jsonify,Blueprint
import sqlite3
import os
from werkzeug.security import generate_password_hash
from modules.registration.automatically_make_user_id import get_next_user_id
from modules.registration.init_db import init_db
from apis.registration.get_all_users import get_whole_users
from apis.registration.get_specific_user import get_specific_user
from apis.registration.signup import signup_login

# Database configuration
DATABASE = 'users.db'


app = Flask(__name__)


app.register_blueprint(get_whole_users)
app.register_blueprint(get_specific_user)
app.register_blueprint(signup_login)


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Flask User API is running'
    }), 200

if __name__ == '__main__':
    # Initialize database on startup
    init_db()
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)
