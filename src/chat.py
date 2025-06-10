from flask import Flask, request, jsonify, Blueprint
import sqlite3
import requests
import jwt
from functools import wraps
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
from modules.chat.init_chat_db import init_chat_db
from modules.chat.token_verification_and_autorization import token_required
from modules.chat.users_credentials_verification_from_db import verify_user_credentials
from modules.chat.check_user_exist_from_db import check_user_exists
from modules.chat.token_verification_and_autorization import token_required
from modules.chat.init_friends_db import init_friends_db
from modules.chat.init_request_db import init_friend_requests_db
from modules.chat.remove_friendship import remove_friendship
from modules.chat.get_user_friends import get_user_friends
from modules.chat.get_user_by_username import get_user_by_username
from modules.chat.add_friendship import add_friendship
from modules.chat.check_existing_friend_request import check_existing_friend_request
from modules.chat.check_if_already_friends import check_if_already_friends
from modules.chat.get_user_by_userid import get_username_by_user_id
from apis.chat.send_messages import send_messages
from apis.chat.get_users import get_users
from apis.chat.conversation import conversation
from apis.chat.delete_message import delete_message
from apis.chat.mark_as_read import mark_as_read
from apis.chat.get_messages import get_messages
from apis.chat.search_user import search_user
from apis.chat.send_friend_request import send_friend_request
from apis.chat.get_friend_requests import get_friend_requests
from apis.chat.get_friends import get_friends
from apis.chat.respond_friend_request import respond_friend_request

# Configuration
CHAT_DATABASE = 'chat.db'
USER_API_URL = 'http://localhost:5000'  # User registration API URL
AUTH_API_URL = 'http://localhost:3000'  # Authentication API URL
JWT_SECRET_KEY = 'your-secret-key-change-this-in-production'  # Should match auth_app.py

# Blueprints

app = Flask(__name__)

app.register_blueprint(send_messages)
app.register_blueprint(get_messages)
app.register_blueprint(get_users)
app.register_blueprint(conversation)
app.register_blueprint(delete_message)
app.register_blueprint(mark_as_read)
app.register_blueprint(search_user)
app.register_blueprint(send_friend_request)
app.register_blueprint(get_friend_requests)
app.register_blueprint(get_friends)
app.register_blueprint(respond_friend_request)


# Utility endpoints

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Chat API',
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get basic statistics about the chat system"""
    try:
        conn = sqlite3.connect(CHAT_DATABASE)
        cursor = conn.cursor()

        # Get total messages
        cursor.execute('SELECT COUNT(*) FROM messages')
        total_messages = cursor.fetchone()[0]

        # Get total unread messages
        cursor.execute('SELECT COUNT(*) FROM messages WHERE is_read = FALSE')
        unread_messages = cursor.fetchone()[0]

        # Get unique users who have sent messages
        cursor.execute('SELECT COUNT(DISTINCT sender_user_id) FROM messages')
        active_senders = cursor.fetchone()[0]

        # Get unique users who have received messages
        cursor.execute('SELECT COUNT(DISTINCT recipient_user_id) FROM messages')
        active_recipients = cursor.fetchone()[0]

        conn.close()

        return jsonify({
            'total_messages': total_messages,
            'unread_messages': unread_messages,
            'active_senders': active_senders,
            'active_recipients': active_recipients,
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        return jsonify({
            'error': f'Failed to fetch stats: {str(e)}'
        }), 500

# Error handlers

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'error': 'Method not allowed'
    }), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error'
    }), 500

# Initialize database and run the application
if __name__ == '__main__':
    # Initialize the chat database
    init_chat_db()
    print("Chat database initialized successfully!")
    
    # Run the Flask application
    print("Starting Chat API server...")
    print("Available endpoints:")
    print("  POST /login - Authenticate and get JWT token")
    print("  POST /auth/send_message - Send message (JWT auth)")
    print("  GET /auth/messages - Get user messages (JWT auth)")
    print("  GET /auth/conversation/<user_id> - Get conversation (JWT auth)")
    print("  PUT /auth/mark_read/<message_id> - Mark message as read (JWT auth)")
    print("  GET /auth/users - Get all users (JWT auth)")
    print("  DELETE /auth/delete_message/<message_id> - Delete message (JWT auth)")
    print("  GET /health - Health check")
    print("  GET /stats - System statistics")
    
    app.run(host='0.0.0.0', port=2000, debug=True)
