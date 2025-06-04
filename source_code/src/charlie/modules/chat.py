from flask import Flask, request, jsonify
import sqlite3
import requests
import jwt
from functools import wraps
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta

app = Flask(__name__)

# Configuration
CHAT_DATABASE = 'chat.db'
USER_API_URL = 'http://localhost:5000'  # User registration API URL
AUTH_API_URL = 'http://localhost:3000'  # Authentication API URL
JWT_SECRET_KEY = 'your-secret-key-change-this-in-production'  # Should match auth_app.py

def init_chat_db():
    """Initialize the chat database with messages table"""
    conn = sqlite3.connect(CHAT_DATABASE)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_user_id TEXT NOT NULL,
            recipient_user_id TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_read BOOLEAN DEFAULT FALSE
        )
    ''')

    conn.commit()
    conn.close()

def verify_user_credentials(user_id, password):
    """Verify user credentials against the user registration database (Legacy)"""
    try:
        # Try different possible paths for the users database
        possible_paths = ['users.db', '../users.db', './users.db']
        user_conn = None

        for path in possible_paths:
            try:
                user_conn = sqlite3.connect(path)
                cursor = user_conn.cursor()
                # Test if the table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
                if cursor.fetchone():
                    print(f"Found users database at: {path}")
                    break
                user_conn.close()
                user_conn = None
            except:
                if user_conn:
                    user_conn.close()
                continue

        if not user_conn:
            print("Could not find users database")
            return False

        cursor = user_conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()

        print(f"Database query result for user {user_id}: {'Found' if result else 'Not found'}")

        user_conn.close()

        if result:
            password_match = check_password_hash(result[0], password)
            print(f"Password verification for {user_id}: {'Success' if password_match else 'Failed'}")
            return password_match
        return False

    except Exception as e:
        print(f"Error verifying credentials: {e}")
        return False

def check_user_exists(user_id):
    """Check if a user exists in the registration database"""
    try:
        # Try different possible paths for the users database
        possible_paths = ['users.db', '../users.db', './users.db']
        user_conn = None

        for path in possible_paths:
            try:
                user_conn = sqlite3.connect(path)
                cursor = user_conn.cursor()
                # Test if the table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
                if cursor.fetchone():
                    break
                user_conn.close()
                user_conn = None
            except:
                if user_conn:
                    user_conn.close()
                continue

        if not user_conn:
            print("Could not find users database")
            return False

        cursor = user_conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        user_conn.close()

        return result is not None

    except Exception as e:
        print(f"Error checking user existence: {e}")
        return False

def token_required(f):
    """Decorator to verify JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'error': 'Token is missing!'}), 401

        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]

            data = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
            current_user = {
                'user_id': data['user_id'],
                'username': data['username']
            }
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token is invalid!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated

# JWT-BASED ENDPOINTS

@app.route('/login', methods=['POST'])
def login():
    """Login endpoint to authenticate user and get JWT token"""
    try:
        data = request.get_json()

        if not data or not data.get('user_id') or not data.get('password'):
            return jsonify({'error': 'User ID and password are required!'}), 400

        user_id = data['user_id']
        password = data['password']

        # Verify credentials against local database
        if verify_user_credentials(user_id, password):
            # Generate JWT token locally (same as auth service)
            token = jwt.encode({
                'user_id': user_id,
                'username': user_id,  # Using user_id as username for simplicity
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, JWT_SECRET_KEY, algorithm='HS256')

            return jsonify({
                'message': 'Login successful!',
                'token': token,
                'user_id': user_id,
                'expires_in': '24 hours'
            }), 200
        else:
            return jsonify({'error': 'Invalid user ID or password!'}), 401

    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'error': 'An error occurred during login'}), 500

@app.route('/auth/send_message', methods=['POST'])
@token_required
def send_message_auth(current_user):
    """Send a message using JWT authentication"""
    try:
        data = request.get_json()
        if not data or 'message' not in data or 'recipient_user_id' not in data:
            return jsonify({
                'error': 'Message content and recipient_user_id are required'
            }), 400

        message = data['message']
        recipient_user_id = data['recipient_user_id']
        sender_user_id = current_user['user_id']

        # Check if recipient exists
        if not check_user_exists(recipient_user_id):
            return jsonify({
                'error': 'Recipient user not found'
            }), 404

        # Check if sender is trying to send to themselves
        if sender_user_id == recipient_user_id:
            return jsonify({
                'error': 'Cannot send message to yourself'
            }), 400

        # Store message in chat database
        conn = sqlite3.connect(CHAT_DATABASE)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO messages (sender_user_id, recipient_user_id, message)
            VALUES (?, ?, ?)
        ''', (sender_user_id, recipient_user_id, message))

        message_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return jsonify({
            'message': 'Message sent successfully',
            'message_id': message_id,
            'sender': sender_user_id,
            'recipient': recipient_user_id,
            'timestamp': datetime.now().isoformat()
        }), 201

    except Exception as e:
        return jsonify({
            'error': f'Failed to send message: {str(e)}'
        }), 500

@app.route('/auth/messages', methods=['GET'])
@token_required
def get_messages_auth(current_user):
    """Get messages for authenticated user"""
    try:
        user_id = current_user['user_id']
        
        conn = sqlite3.connect(CHAT_DATABASE)
        cursor = conn.cursor()

        # Get all messages where user is either sender or recipient
        cursor.execute('''
            SELECT id, sender_user_id, recipient_user_id, message, timestamp, is_read
            FROM messages
            WHERE sender_user_id = ? OR recipient_user_id = ?
            ORDER BY timestamp DESC
        ''', (user_id, user_id))

        messages = []
        for row in cursor.fetchall():
            messages.append({
                'message_id': row[0],
                'sender': row[1],
                'recipient': row[2],
                'message': row[3],
                'timestamp': row[4],
                'is_read': bool(row[5]),
                'direction': 'sent' if row[1] == user_id else 'received'
            })

        conn.close()

        return jsonify({
            'messages': messages,
            'total_messages': len(messages)
        }), 200

    except Exception as e:
        return jsonify({
            'error': f'Failed to fetch messages: {str(e)}'
        }), 500

@app.route('/auth/conversation/<other_user_id>', methods=['GET'])
@token_required
def get_conversation_auth(current_user, other_user_id):
    """Get conversation between authenticated user and another user"""
    try:
        user_id = current_user['user_id']
        
        conn = sqlite3.connect(CHAT_DATABASE)
        cursor = conn.cursor()

        # Get messages between the two users
        cursor.execute('''
            SELECT id, sender_user_id, recipient_user_id, message, timestamp, is_read
            FROM messages
            WHERE (sender_user_id = ? AND recipient_user_id = ?)
               OR (sender_user_id = ? AND recipient_user_id = ?)
            ORDER BY timestamp ASC
        ''', (user_id, other_user_id, other_user_id, user_id))

        messages = []
        for row in cursor.fetchall():
            messages.append({
                'message_id': row[0],
                'sender': row[1],
                'recipient': row[2],
                'message': row[3],
                'timestamp': row[4],
                'is_read': bool(row[5]),
                'direction': 'sent' if row[1] == user_id else 'received'
            })

        conn.close()

        return jsonify({
            'conversation': messages,
            'participants': [user_id, other_user_id],
            'total_messages': len(messages)
        }), 200

    except Exception as e:
        return jsonify({
            'error': f'Failed to fetch conversation: {str(e)}'
        }), 500

@app.route('/auth/mark_read/<message_id>', methods=['PUT'])
@token_required
def mark_message_read_auth(current_user, message_id):
    """Mark a message as read using JWT authentication"""
    try:
        user_id = current_user['user_id']
        
        conn = sqlite3.connect(CHAT_DATABASE)
        cursor = conn.cursor()

        # Check if message exists and user is the recipient
        cursor.execute('''
            SELECT recipient_user_id FROM messages WHERE id = ?
        ''', (message_id,))

        result = cursor.fetchone()
        if not result:
            conn.close()
            return jsonify({
                'error': 'Message not found'
            }), 404

        if result[0] != user_id:
            conn.close()
            return jsonify({
                'error': 'You can only mark your received messages as read'
            }), 403

        # Mark message as read
        cursor.execute('''
            UPDATE messages SET is_read = TRUE WHERE id = ?
        ''', (message_id,))

        conn.commit()
        conn.close()

        return jsonify({
            'message': 'Message marked as read'
        }), 200

    except Exception as e:
        return jsonify({
            'error': f'Failed to mark message as read: {str(e)}'
        }), 500

@app.route('/auth/users', methods=['GET'])
@token_required
def get_users_auth(current_user):
    """Get list of all users (JWT authenticated)"""
    try:
        # Try different possible paths for the users database
        possible_paths = ['users.db', '../users.db', './users.db']
        user_conn = None

        for path in possible_paths:
            try:
                user_conn = sqlite3.connect(path)
                cursor = user_conn.cursor()
                # Test if the table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
                if cursor.fetchone():
                    break
                user_conn.close()
                user_conn = None
            except:
                if user_conn:
                    user_conn.close()
                continue

        if not user_conn:
            return jsonify({
                'error': 'Could not find users database'
            }), 500

        cursor = user_conn.cursor()
        cursor.execute("SELECT user_id, email, full_name, created_at FROM users")
        users = []
        
        for row in cursor.fetchall():
            users.append({
                'user_id': row[0],
                'email': row[1],
                'full_name': row[2],
                'created_at': row[3]
            })

        user_conn.close()

        return jsonify({
            'users': users,
            'total_users': len(users)
        }), 200

    except Exception as e:
        return jsonify({
            'error': f'Failed to fetch users: {str(e)}'
        }), 500

@app.route('/auth/delete_message/<message_id>', methods=['DELETE'])
@token_required
def delete_message_auth(current_user, message_id):
    """Delete a message (only sender can delete)"""
    try:
        user_id = current_user['user_id']
        
        conn = sqlite3.connect(CHAT_DATABASE)
        cursor = conn.cursor()

        # Check if message exists and user is the sender
        cursor.execute('''
            SELECT sender_user_id FROM messages WHERE id = ?
        ''', (message_id,))

        result = cursor.fetchone()
        if not result:
            conn.close()
            return jsonify({
                'error': 'Message not found'
            }), 404

        if result[0] != user_id:
            conn.close()
            return jsonify({
                'error': 'You can only delete messages you sent'
            }), 403

        # Delete the message
        cursor.execute('''
            DELETE FROM messages WHERE id = ?
        ''', (message_id,))

        conn.commit()
        conn.close()

        return jsonify({
            'message': 'Message deleted successfully'
        }), 200

    except Exception as e:
        return jsonify({
            'error': f'Failed to delete message: {str(e)}'
        }), 500

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
