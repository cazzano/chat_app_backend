from flask import Flask, request, jsonify
import jwt
import datetime
from functools import wraps
import hashlib

app = Flask(__name__)

# Secret key for JWT encoding/decoding (in production, use environment variable)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'

# Hardcoded user credentials (in production, use a database)
USERS = {
    'vincenzo': {
        'password': hashlib.sha256('itu@#$'.encode()).hexdigest(),
        'user_id': 1
    }
}

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
            current_user = data['username']
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated

@app.route('/login', methods=['POST'])
def login():
    """Login endpoint to generate JWT token"""
    try:
        data = request.get_json()

        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'message': 'Username and password are required!'}), 400

        username = data['username']
        password = data['password']

        # Hash the provided password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        # Verify credentials
        if username in USERS and USERS[username]['password'] == hashed_password:
            # Generate JWT token
            token = jwt.encode({
                'username': username,
                'user_id': USERS[username]['user_id'],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, app.config['SECRET_KEY'], algorithm='HS256')

            return jsonify({
                'message': 'Login successful!',
                'token': token,
                'expires_in': '24 hours'
            }), 200
        else:
            return jsonify({'message': 'Invalid username or password!'}), 401

    except Exception as e:
        return jsonify({'message': 'An error occurred during login'}), 500

@app.route('/verify-token', methods=['GET'])
@token_required
def verify_token(current_user):
    """Verify if token is valid"""
    return jsonify({
        'message': 'Token is valid!',
        'username': current_user
    }), 200

@app.route('/protected', methods=['GET'])
@token_required
def protected_route(current_user):
    """Example protected route"""
    return jsonify({
        'message': f'Hello {current_user}! This is a protected route.',
        'data': 'This is sensitive information only for authenticated users.'
    }), 200

@app.route('/refresh-token', methods=['POST'])
@token_required
def refresh_token(current_user):
    """Refresh JWT token"""
    try:
        # Generate new token
        new_token = jwt.encode({
            'username': current_user,
            'user_id': USERS[current_user]['user_id'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm='HS256')

        return jsonify({
            'message': 'Token refreshed successfully!',
            'token': new_token,
            'expires_in': '24 hours'
        }), 200

    except Exception as e:
        return jsonify({'message': 'An error occurred during token refresh'}), 500

@app.route('/', methods=['GET'])
def home():
    """Home endpoint with API documentation"""
    return jsonify({
        'message': 'Flask JWT Authentication API',
        'endpoints': {
            'POST /login': 'Login with username and password to get JWT token',
            'GET /verify-token': 'Verify if JWT token is valid (requires Authorization header)',
            'GET /protected': 'Example protected route (requires Authorization header)',
            'POST /refresh-token': 'Refresh JWT token (requires Authorization header)'
        },
        'usage': {
            'login': {
                'method': 'POST',
                'url': '/login',
                'body': {
                    'username': 'vincenzo',
                    'password': 'itu@#$'
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

if __name__ == '__main__':
    print("Flask JWT Authentication App")
    print("=" * 40)
    print("Available endpoints:")
    print("- POST /login - Login to get JWT token")
    print("- GET /verify-token - Verify token validity")
    print("- GET /protected - Protected route example")
    print("- POST /refresh-token - Refresh your token")
    print("=" * 40)
    print("Test credentials:")
    print("Username: vincenzo")
    print("Password: itu@#$")
    print("=" * 40)

    app.run(debug=True, host='0.0.0.0', port=5000)
