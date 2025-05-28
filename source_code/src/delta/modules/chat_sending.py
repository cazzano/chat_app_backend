from flask import Flask, request, jsonify
import sqlite3
import requests
from werkzeug.security import check_password_hash
from datetime import datetime

app = Flask(__name__)

# Database configuration for chat
CHAT_DATABASE = 'chat.db'
USER_API_URL = 'http://localhost:5000'  # User registration API URL

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
    """Verify user credentials against the user registration database"""
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

@app.route('/send_message', methods=['POST'])
def send_message():
    """Send a message to a recipient"""
    try:
        # Get headers (try different header name formats)
        sender_user_id = request.headers.get('sender_user_id') or request.headers.get('Sender-User-Id')
        recipient_user_id = request.headers.get('recipient_user_id') or request.headers.get('Recipient-User-Id')
        sender_password = request.headers.get('sender_password') or request.headers.get('Sender-Password')
        
        # Debug: Print received headers
        print(f"Received headers: {dict(request.headers)}")
        print(f"Sender ID: {sender_user_id}, Recipient ID: {recipient_user_id}, Password: {'***' if sender_password else None}")
        
        # Get message from request body
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({
                'error': 'Message content is required in request body'
            }), 400
        
        message = data['message']
        
        # Validate required headers
        if not all([sender_user_id, recipient_user_id, sender_password]):
            return jsonify({
                'error': 'Missing required headers: sender_user_id, recipient_user_id, sender_password'
            }), 400
        
        # Verify sender credentials
        if not verify_user_credentials(sender_user_id, sender_password):
            return jsonify({
                'error': 'Invalid sender credentials'
            }), 401
        
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

@app.route('/messages/<user_id>', methods=['GET'])
def get_messages(user_id):
    """Get messages for a specific user (both sent and received)"""
    try:
        # Get password from header for authentication
        password = request.headers.get('password')
        
        if not password:
            return jsonify({
                'error': 'Password header is required'
            }), 400
        
        # Verify user credentials
        if not verify_user_credentials(user_id, password):
            return jsonify({
                'error': 'Invalid credentials'
            }), 401
        
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

@app.route('/conversation/<user_id>/<other_user_id>', methods=['GET'])
def get_conversation(user_id, other_user_id):
    """Get conversation between two users"""
    try:
        # Get password from header for authentication
        password = request.headers.get('password')
        
        if not password:
            return jsonify({
                'error': 'Password header is required'
            }), 400
        
        # Verify user credentials
        if not verify_user_credentials(user_id, password):
            return jsonify({
                'error': 'Invalid credentials'
            }), 401
        
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

@app.route('/mark_read/<message_id>', methods=['PUT'])
def mark_message_read(message_id):
    """Mark a message as read"""
    try:
        # Get user credentials from headers
        user_id = request.headers.get('user_id')
        password = request.headers.get('password')
        
        if not all([user_id, password]):
            return jsonify({
                'error': 'Missing required headers: user_id, password'
            }), 400
        
        # Verify user credentials
        if not verify_user_credentials(user_id, password):
            return jsonify({
                'error': 'Invalid credentials'
            }), 401
        
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

@app.route('/debug/user/<user_id>', methods=['GET'])
def debug_user(user_id):
    """Debug endpoint to check user existence and database connectivity"""
    try:
        # Check which database path works
        possible_paths = ['users.db', '../users.db', './users.db']
        working_path = None
        
        for path in possible_paths:
            try:
                conn = sqlite3.connect(path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
                if cursor.fetchone():
                    working_path = path
                    
                    # Get user info
                    cursor.execute("SELECT user_id, username FROM users WHERE user_id = ?", (user_id,))
                    user_data = cursor.fetchone()
                    
                    # Get all users for context
                    cursor.execute("SELECT user_id, username FROM users")
                    all_users = cursor.fetchall()
                    
                    conn.close()
                    
                    return jsonify({
                        'database_path': working_path,
                        'user_found': user_data is not None,
                        'user_data': {'user_id': user_data[0], 'username': user_data[1]} if user_data else None,
                        'all_users': [{'user_id': u[0], 'username': u[1]} for u in all_users]
                    }), 200
                    
                conn.close()
            except Exception as e:
                continue
        
        return jsonify({
            'error': 'Could not find users database',
            'tried_paths': possible_paths
        }), 404
        
    except Exception as e:
        return jsonify({
            'error': f'Debug failed: {str(e)}'
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Flask Chat API is running',
        'port': 2000
    }), 200

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get chat statistics"""
    try:
        conn = sqlite3.connect(CHAT_DATABASE)
        cursor = conn.cursor()
        
        # Total messages
        cursor.execute("SELECT COUNT(*) FROM messages")
        total_messages = cursor.fetchone()[0]
        
        # Unread messages
        cursor.execute("SELECT COUNT(*) FROM messages WHERE is_read = FALSE")
        unread_messages = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'total_messages': total_messages,
            'unread_messages': unread_messages,
            'read_messages': total_messages - unread_messages
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Failed to fetch stats: {str(e)}'
        }), 500

if __name__ == '__main__':
    # Initialize chat database on startup
    init_chat_db()
    
    print("Chat API starting on port 2000...")
    print("Make sure the User Registration API is running on port 5000")
    
    # Run the Flask app on port 2000
    app.run(debug=True, host='0.0.0.0', port=2000)
