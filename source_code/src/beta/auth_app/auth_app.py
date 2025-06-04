from flask import Flask, request, jsonify
import jwt
import datetime
from functools import wraps
import sqlite3
from werkzeug.security import check_password_hash

app = Flask(__name__)

# Secret key for JWT encoding/decoding (in production, use environment variable)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'

def get_user_from_database(user_id):
    """Get user from the users database"""
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
        cursor.execute("SELECT user_id, username, password_hash FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        user_conn.close()

        if result:
            return {
                'user_id': result[0],
                'username': result[1],
                'password_hash': result[2]
            }
        return None

    except Exception as e:
        print(f"Error getting user from database: {e}")
        return None

def verify_user_credentials(user_id, password):
    """Verify user credentials against the user database"""
    try:
        user = get_user_from_database(user_id)
        if user and check_password_hash(user['password_hash'], password):
            return user
        return None
    except Exception as e:
        print(f"Error verifying credentials: {e}")
        return None

def token_required(f):
    """Decorator to verify JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]

            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = {
                'user_id': data['user_id'],
                'username': data['username']
            }
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated

@app.route('/login', methods=['POST'])
def login():
    """Login endpoint to generate JWT token using database credentials"""
    try:
        data = request.get_json()

        if not data or not data.get('user_id') or not data.get('password'):
            return jsonify({'message': 'User ID and password are required!'}), 400

        user_id = data['user_id']
        password = data['password']

        # Verify credentials against database
        user = verify_user_credentials(user_id, password)
        
        if user:
            # Generate JWT token
            token = jwt.encode({
                'user_id': user['user_id'],
                'username': user['username'],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, app.config['SECRET_KEY'], algorithm='HS256')

            return jsonify({
                'message': 'Login successful!',
                'token': token,
                'user_id': user['user_id'],
                'username': user['username'],
                'expires_in': '24 hours'
            }), 200
        else:
            return jsonify({'message': 'Invalid user ID or password!'}), 401

    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'message': 'An error occurred during login'}), 500

@app.route('/verify-token', methods=['GET'])
@token_required
def verify_token(current_user):
    """Verify if token is valid"""
    return jsonify({
        'message': 'Token is valid!',
        'user_id': current_user['user_id'],
        'username': current_user['username']
    }), 200

@app.route('/protected', methods=['GET'])
@token_required
def protected_route(current_user):
    """Example protected route"""
    return jsonify({
        'message': f'Hello {current_user["username"]}! This is a protected route.',
        'user_id': current_user['user_id'],
        'data': 'This is sensitive information only for authenticated users.'
    }), 200

@app.route('/refresh-token', methods=['POST'])
@token_required
def refresh_token(current_user):
    """Refresh JWT token"""
    try:
        # Generate new token
        new_token = jwt.encode({
            'user_id': current_user['user_id'],
            'username': current_user['username'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm='HS256')

        return jsonify({
            'message': 'Token refreshed successfully!',
            'token': new_token,
            'user_id': current_user['user_id'],
            'username': current_user['username'],
            'expires_in': '24 hours'
        }), 200

    except Exception as e:
        return jsonify({'message': 'An error occurred during token refresh'}), 500

@app.route('/user/<user_id>', methods=['GET'])
def get_user_info(user_id):
    """Get user information (for integration with chat API)"""
    try:
        user = get_user_from_database(user_id)
        if user:
            return jsonify({
                'user_id': user['user_id'],
                'username': user['username'],
                'exists': True
            }), 200
        else:
            return jsonify({
                'message': 'User not found',
                'exists': False
            }), 404
    except Exception as e:
        return jsonify({'message': 'Error fetching user information'}), 500

@app.route('/validate-user', methods=['POST'])
def validate_user():
    """Validate user credentials (for chat API integration)"""
    try:
        data = request.get_json()
        if not data or not data.get('user_id') or not data.get('password'):
            return jsonify({'valid': False, 'message': 'User ID and password required'}), 400
        
        user = verify_user_credentials(data['user_id'], data['password'])
        if user:
            return jsonify({
                'valid': True,
                'user_id': user['user_id'],
                'username': user['username']
            }), 200
        else:
            return jsonify({'valid': False, 'message': 'Invalid credentials'}), 401
            
    except Exception as e:
        return jsonify({'valid': False, 'message': 'Validation error'}), 500

@app.route('/', methods=['GET'])
def home():
    """Home endpoint with API documentation"""
    return jsonify({
        'message': 'Flask JWT Authentication API - Database Integrated',
        'endpoints': {
            'POST /login': 'Login with user_id and password to get JWT token',
            'GET /verify-token': 'Verify if JWT token is valid (requires Authorization header)',
            'GET /protected': 'Example protected route (requires Authorization header)',
            'POST /refresh-token': 'Refresh JWT token (requires Authorization header)',
            'GET /user/<user_id>': 'Get user information',
            'POST /validate-user': 'Validate user credentials'
        },
        'usage': {
            'login': {
                'method': 'POST',
                'url': '/login',
                'body': {
                    'user_id': 'your_user_id',
                    'password': 'your_password'
                }
            },
            'protected_access': {
                'method': 'GET',
                'url': '/protected',
                'headers': {
                    'Authorization': 'Bearer <your-jwt-token>'
                }
            }
        }
    }), 200

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
