from flask import Flask, request, jsonify, Blueprint
import sqlite3
import requests
import jwt
from functools import wraps
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
from modules.chat.token_verification_and_autorization import token_required

send_friend_request = Blueprint('send_friend_request', __name__)

# Configuration
CHAT_DATABASE = 'chat.db'
FR_REQUESTS_DATABASE = 'fr_requests.db'
FRIENDS_DATABASE = 'friends.db'
USER_API_URL = 'http://localhost:5000'  # User registration API URL
AUTH_API_URL = 'http://localhost:3000'  # Authentication API URL
JWT_SECRET_KEY = 'your-secret-key-change-this-in-production'  # Should match auth_app.py


def init_friends_db():
    """Initialize the friends database"""
    try:
        conn = sqlite3.connect(FRIENDS_DATABASE)
        cursor = conn.cursor()
        
        # Create friends table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS friends (
                friendship_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id TEXT NOT NULL,
                user1_username TEXT NOT NULL,
                user2_id TEXT NOT NULL,
                user2_username TEXT NOT NULL,
                friendship_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user1_id) REFERENCES users(user_id),
                FOREIGN KEY (user2_id) REFERENCES users(user_id),
                UNIQUE(user1_id, user2_id),
                UNIQUE(user2_id, user1_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("Friends database initialized successfully")
        
    except Exception as e:
        print(f"Error initializing friends database: {e}")


def init_friend_requests_db():
    """Initialize the friend requests database"""
    try:
        conn = sqlite3.connect(FR_REQUESTS_DATABASE)
        cursor = conn.cursor()
        
        # Create friend_requests table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS friend_requests (
                request_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_user_id TEXT NOT NULL,
                sender_username TEXT NOT NULL,
                recipient_user_id TEXT NOT NULL,
                recipient_username TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                request_data TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sender_user_id) REFERENCES users(user_id),
                FOREIGN KEY (recipient_user_id) REFERENCES users(user_id),
                UNIQUE(sender_user_id, recipient_user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("Friend requests database initialized successfully")
        
    except Exception as e:
        print(f"Error initializing friend requests database: {e}")


def add_friendship(user1_id, user1_username, user2_id, user2_username):
    """Add friendship to friends database"""
    try:
        init_friends_db()
        conn = sqlite3.connect(FRIENDS_DATABASE)
        cursor = conn.cursor()
        
        # Check if friendship already exists (in either direction)
        cursor.execute('''
            SELECT friendship_id FROM friends 
            WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)
        ''', (user1_id, user2_id, user2_id, user1_id))
        
        if cursor.fetchone():
            conn.close()
            return False, "Friendship already exists"
        
        # Add friendship (always store in alphabetical order by user_id for consistency)
        if user1_id < user2_id:
            cursor.execute('''
                INSERT INTO friends (user1_id, user1_username, user2_id, user2_username)
                VALUES (?, ?, ?, ?)
            ''', (user1_id, user1_username, user2_id, user2_username))
        else:
            cursor.execute('''
                INSERT INTO friends (user1_id, user1_username, user2_id, user2_username)
                VALUES (?, ?, ?, ?)
            ''', (user2_id, user2_username, user1_id, user1_username))
        
        friendship_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return True, friendship_id
        
    except Exception as e:
        print(f"Error adding friendship: {e}")
        return False, str(e)


def remove_friendship(user1_id, user2_id):
    """Remove friendship from friends database"""
    try:
        conn = sqlite3.connect(FRIENDS_DATABASE)
        cursor = conn.cursor()
        
        # Remove friendship (check both directions)
        cursor.execute('''
            DELETE FROM friends 
            WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)
        ''', (user1_id, user2_id, user2_id, user1_id))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted_count > 0
        
    except Exception as e:
        print(f"Error removing friendship: {e}")
        return False


def get_user_friends(user_id):
    """Get all friends for a specific user"""
    try:
        init_friends_db()
        conn = sqlite3.connect(FRIENDS_DATABASE)
        cursor = conn.cursor()
        
        # Get friends where user is either user1 or user2
        cursor.execute('''
            SELECT 
                friendship_id,
                CASE 
                    WHEN user1_id = ? THEN user2_id 
                    ELSE user1_id 
                END as friend_id,
                CASE 
                    WHEN user1_id = ? THEN user2_username 
                    ELSE user1_username 
                END as friend_username,
                friendship_date
            FROM friends 
            WHERE user1_id = ? OR user2_id = ?
            ORDER BY friendship_date DESC
        ''', (user_id, user_id, user_id, user_id))
        
        friends = []
        for row in cursor.fetchall():
            friends.append({
                'friendship_id': row[0],
                'friend_id': row[1],
                'friend_username': row[2],
                'friendship_date': row[3]
            })
        
        conn.close()
        return friends
        
    except Exception as e:
        print(f"Error getting user friends: {e}")
        return []


def get_user_by_username(username):
    """Get user_id by username from users database"""
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
            return None

        cursor = user_conn.cursor()
        cursor.execute("SELECT user_id, username FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        user_conn.close()

        if result:
            return {'user_id': result[0], 'username': result[1]}
        return None

    except Exception as e:
        print(f"Error getting user by username: {e}")
        return None


def get_username_by_user_id(user_id):
    """Get username by user_id from users database"""
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
            return None

        cursor = user_conn.cursor()
        cursor.execute("SELECT username FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        user_conn.close()

        return result[0] if result else None

    except Exception as e:
        print(f"Error getting username by user_id: {e}")
        return None


def check_existing_friend_request(sender_user_id, recipient_user_id):
    """Check if a friend request already exists between two users"""
    try:
        conn = sqlite3.connect(FR_REQUESTS_DATABASE)
        cursor = conn.cursor()
        
        # Check for existing request in either direction
        cursor.execute('''
            SELECT request_id, status FROM friend_requests 
            WHERE (sender_user_id = ? AND recipient_user_id = ?) 
               OR (sender_user_id = ? AND recipient_user_id = ?)
        ''', (sender_user_id, recipient_user_id, recipient_user_id, sender_user_id))
        
        result = cursor.fetchone()
        conn.close()
        
        return result
        
    except Exception as e:
        print(f"Error checking existing friend request: {e}")
        return None


def check_if_already_friends(user1_id, user2_id):
    """Check if two users are already friends"""
    try:
        init_friends_db()
        conn = sqlite3.connect(FRIENDS_DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT friendship_id FROM friends 
            WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)
        ''', (user1_id, user2_id, user2_id, user1_id))
        
        result = cursor.fetchone()
        conn.close()
        
        return result is not None
        
    except Exception as e:
        print(f"Error checking if users are friends: {e}")
        return False


@send_friend_request.route('/auth/send_friend_request', methods=['POST'])
@token_required
def send_friend_request_auth(current_user):
    """Send a friend request using JWT authentication"""
    try:
        # Initialize database if not exists
        init_friend_requests_db()
        
        data = request.get_json()
        if not data or 'username' not in data:
            return jsonify({
                'error': 'Username is required'
            }), 400

        target_username = data['username']
        sender_user_id = current_user['user_id']

        # Get sender's username
        sender_username = get_username_by_user_id(sender_user_id)
        if not sender_username:
            return jsonify({
                'error': 'Sender user not found'
            }), 404

        # Get recipient's user_id by username
        recipient_info = get_user_by_username(target_username)
        if not recipient_info:
            return jsonify({
                'error': 'Username not found'
            }), 404

        recipient_user_id = recipient_info['user_id']
        recipient_username = recipient_info['username']

        # Check if sender is trying to send friend request to themselves
        if sender_user_id == recipient_user_id:
            return jsonify({
                'error': 'Cannot send friend request to yourself'
            }), 400

        # Check if they are already friends
        if check_if_already_friends(sender_user_id, recipient_user_id):
            return jsonify({
                'error': f'You are already friends with {recipient_username}'
            }), 409

        # Check if friend request already exists
        existing_request = check_existing_friend_request(sender_user_id, recipient_user_id)
        if existing_request:
            status = existing_request[1]
            if status == 'pending':
                return jsonify({
                    'error': 'Friend request already pending between these users'
                }), 409

        # Create friend request JSON data
        friend_request_data = {
            f"friend_request_from_{sender_username}": "accept_or_reject"
        }

        # Store friend request in database
        conn = sqlite3.connect(FR_REQUESTS_DATABASE)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO friend_requests 
            (sender_user_id, sender_username, recipient_user_id, recipient_username, request_data, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
        ''', (sender_user_id, sender_username, recipient_user_id, recipient_username, str(friend_request_data)))

        request_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return jsonify({
            'message': 'Friend request sent successfully',
            'request_id': request_id,
            'sender': sender_username,
            'recipient': recipient_username,
            'request_data': friend_request_data,
            'timestamp': datetime.now().isoformat()
        }), 201

    except Exception as e:
        return jsonify({
            'error': f'Failed to send friend request: {str(e)}'
        }), 500


@send_friend_request.route('/auth/get_friend_requests', methods=['GET'])
@token_required
def get_friend_requests_auth(current_user):
    """Get all friend requests for the authenticated user"""
    try:
        user_id = current_user['user_id']
        
        conn = sqlite3.connect(FR_REQUESTS_DATABASE)
        cursor = conn.cursor()
        
        # Get received friend requests (where user is recipient)
        cursor.execute('''
            SELECT request_id, sender_user_id, sender_username, request_data, status, timestamp
            FROM friend_requests 
            WHERE recipient_user_id = ? AND status = 'pending'
            ORDER BY timestamp DESC
        ''', (user_id,))
        
        received_requests = []
        for row in cursor.fetchall():
            received_requests.append({
                'request_id': row[0],
                'sender_user_id': row[1],
                'sender_username': row[2],
                'request_data': eval(row[3]),  # Convert string back to dict
                'status': row[4],
                'timestamp': row[5]
            })
        
        # Get sent friend requests (where user is sender)
        cursor.execute('''
            SELECT request_id, recipient_user_id, recipient_username, request_data, status, timestamp
            FROM friend_requests 
            WHERE sender_user_id = ?
            ORDER BY timestamp DESC
        ''', (user_id,))
        
        sent_requests = []
        for row in cursor.fetchall():
            sent_requests.append({
                'request_id': row[0],
                'recipient_user_id': row[1],
                'recipient_username': row[2],
                'request_data': eval(row[3]),  # Convert string back to dict
                'status': row[4],
                'timestamp': row[5]
            })
        
        conn.close()
        
        return jsonify({
            'received_requests': received_requests,
            'sent_requests': sent_requests,
            'total_received': len(received_requests),
            'total_sent': len(sent_requests)
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Failed to get friend requests: {str(e)}'
        }), 500


@send_friend_request.route('/auth/get_friends', methods=['GET'])
@token_required
def get_friends_auth(current_user):
    """Get all friends for the authenticated user"""
    try:
        user_id = current_user['user_id']
        username = get_username_by_user_id(user_id)
        
        if not username:
            return jsonify({
                'error': 'User not found'
            }), 404
        
        # Get user's friends
        friends = get_user_friends(user_id)
        
        return jsonify({
            'user_id': user_id,
            'username': username,
            'friends': friends,
            'total_friends': len(friends)
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Failed to get friends: {str(e)}'
        }), 500


@send_friend_request.route('/auth/respond_friend_request', methods=['POST'])
@token_required
def respond_friend_request_auth(current_user):
    """Accept or reject a friend request using friend's username"""
    try:
        data = request.get_json()
        if not data or 'username' not in data or 'action' not in data:
            return jsonify({
                'error': 'Username and action (accept/reject) are required'
            }), 400

        friend_username = data['username']
        action = data['action'].lower()
        user_id = current_user['user_id']

        if action not in ['accept', 'reject']:
            return jsonify({
                'error': 'Action must be either "accept" or "reject"'
            }), 400

        # Get current user's username
        current_user_username = get_username_by_user_id(user_id)
        if not current_user_username:
            return jsonify({
                'error': 'Current user not found'
            }), 404

        # Get friend's user_id by username
        friend_info = get_user_by_username(friend_username)
        if not friend_info:
            return jsonify({
                'error': 'Friend username not found'
            }), 404

        friend_user_id = friend_info['user_id']

        conn = sqlite3.connect(FR_REQUESTS_DATABASE)
        cursor = conn.cursor()

        # Check if the request exists where friend is sender and current user is recipient
        cursor.execute('''
            SELECT request_id, sender_user_id, sender_username, recipient_user_id, status 
            FROM friend_requests 
            WHERE sender_user_id = ? AND recipient_user_id = ? AND status IN ('pending', 'rejected')
        ''', (friend_user_id, user_id))

        result = cursor.fetchone()
        if not result:
            conn.close()
            return jsonify({
                'error': 'No friend request found from this user (must be pending or previously rejected)'
            }), 404

        request_id = result[0]
        sender_username = result[2]
        current_status = result[4]

        # Check if already accepted
        if current_status == 'accepted':
            conn.close()
            return jsonify({
                'error': f'You are already friends with {sender_username}'
            }), 409

        # Update the request status
        new_status = 'accepted' if action == 'accept' else 'rejected'
        cursor.execute('''
            UPDATE friend_requests 
            SET status = ?, timestamp = CURRENT_TIMESTAMP 
            WHERE request_id = ?
        ''', (new_status, request_id))

        conn.commit()
        conn.close()

        # Handle friendship database based on action
        friendship_result = None
        if action == 'accept':
            # Add friendship to friends.db - This will make both users friends with each other
            success, result = add_friendship(user_id, current_user_username, friend_user_id, sender_username)
            if success:
                friendship_result = f"Friendship added to database (ID: {result})"
            else:
                friendship_result = f"Friendship already exists: {result}"
        else:  # action == 'reject'
            # Remove friendship from friends.db (in case it was previously accepted)
            if remove_friendship(user_id, friend_user_id):
                friendship_result = "Friendship removed from database"
            else:
                friendship_result = "No existing friendship to remove"

        # Get updated friend counts for both users
        user_friends_count = len(get_user_friends(user_id))
        friend_friends_count = len(get_user_friends(friend_user_id))

        # Create appropriate response message
        if current_status == 'rejected' and action == 'accept':
            message = f'Previously rejected friend request from {sender_username} has been accepted! You are now friends.'
        elif current_status == 'pending' and action == 'accept':
            message = f'Friend request from {sender_username} accepted successfully! You are now friends.'
        elif current_status == 'pending' and action == 'reject':
            message = f'Friend request from {sender_username} rejected successfully'
        else:  # rejected -> rejected
            message = f'Friend request from {sender_username} rejected again'

        return jsonify({
            'message': message,
            'request_id': request_id,
            'friend_username': friend_username,
            'action': action,
            'previous_status': current_status,
            'new_status': new_status,
            'friendship_result': friendship_result,
            'your_friends_count': user_friends_count,
            'their_friends_count': friend_friends_count
        }), 200

    except Exception as e:
        return jsonify({
            'error': f'Failed to respond to friend request: {str(e)}'
        }), 500
