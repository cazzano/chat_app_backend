from flask import Flask, request, jsonify
import sqlite3
import os
from werkzeug.security import generate_password_hash

app = Flask(__name__)

# Database configuration
DATABASE = 'users.db'

def init_db():
    """Initialize the database with users table"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,
            username TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def get_next_user_id():
    """Generate the next user ID in format Uxx"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Get the highest user number
    cursor.execute("SELECT user_id FROM users ORDER BY id DESC LIMIT 1")
    result = cursor.fetchone()
    
    if result:
        # Extract number from last user_id (e.g., "U05" -> 5)
        last_user_id = result[0]
        last_number = int(last_user_id[1:])
        next_number = last_number + 1
    else:
        next_number = 1
    
    conn.close()
    
    # Format as Uxx (e.g., U01, U02, etc.)
    return f"U{next_number:02d}"

@app.route('/register', methods=['POST'])
def register_user():
    """Register a new user with username and password from headers"""
    try:
        # Get username and password from headers
        username = request.headers.get('username')
        password = request.headers.get('password')
        
        # Validate required headers
        if not username or not password:
            return jsonify({
                'error': 'Missing required headers: username and password'
            }), 400
        
        # Check if username already exists
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            conn.close()
            return jsonify({
                'error': 'Username already exists'
            }), 409
        
        # Generate user ID and hash password
        user_id = get_next_user_id()
        password_hash = generate_password_hash(password)
        
        # Insert new user
        cursor.execute('''
            INSERT INTO users (user_id, username, password_hash)
            VALUES (?, ?, ?)
        ''', (user_id, username, password_hash))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': 'User registered successfully',
            'user_id': user_id,
            'username': username
        }), 201
        
    except Exception as e:
        return jsonify({
            'error': f'Registration failed: {str(e)}'
        }), 500

@app.route('/users', methods=['GET'])
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

@app.route('/user/<user_id>', methods=['GET'])
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
