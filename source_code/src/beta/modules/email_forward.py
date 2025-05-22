from flask import Flask, request, jsonify
import sqlite3
import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime
import re

app = Flask(__name__)

# Email configuration (you'll need to set these environment variables)
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS', 'your_email@gmail.com')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', 'your_app_password')

# Database setup
def init_db():
    """Initialize the SQLite database"""
    conn = sqlite3.connect('pin_code.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pin_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,
            pin_code TEXT NOT NULL,
            email TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

def generate_random_code():
    """Generate a random 9-character code with special characters, underscores, hexadecimals, and dots"""
    # Define character sets
    hex_chars = '0123456789ABCDEF'
    special_chars = '!@#$%^&*()_+-=[]{}|;:,.<>?'
    underscore = '_'
    dot = '.'

    # Combine all possible characters
    all_chars = hex_chars + special_chars + underscore + dot

    # Generate 9 random characters
    code = ''.join(random.choices(all_chars, k=9))
    return code

def generate_user_id():
    """Generate a unique user ID in format Uxx"""
    conn = sqlite3.connect('pin_code.db')
    cursor = conn.cursor()

    # Get the highest user ID number
    cursor.execute("SELECT user_id FROM pin_codes ORDER BY id DESC LIMIT 1")
    result = cursor.fetchone()

    if result:
        # Extract number from last user_id (e.g., "U05" -> 5)
        last_id = result[0]
        number = int(last_id[1:]) + 1
    else:
        number = 1

    # Format as Uxx (e.g., U01, U02, etc.)
    user_id = f"U{number:02d}"
    conn.close()

    return user_id

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def send_email(to_email, pin_code, user_id):
    """Send email with the generated PIN code"""
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email
        msg['Subject'] = "Your Verification Code"

        # Email body
        body = f"""
        Hello,

        Your verification code is: {pin_code}
        User ID: {user_id}

        This code was generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

        Please keep this code secure and do not share it with anyone.

        Best regards,
        Email Forwarder Service
        """

        msg.attach(MIMEText(body, 'plain'))

        # Connect to server and send email
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_ADDRESS, to_email, text)
        server.quit()

        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

@app.route('/send-code', methods=['POST'])
def send_code():
    """API endpoint to send verification code to email"""
    try:
        # Get email from request
        data = request.get_json()

        if not data or 'email' not in data:
            return jsonify({
                'success': False,
                'message': 'Email is required'
            }), 400

        email = data['email'].strip().lower()

        # Validate email format
        if not validate_email(email):
            return jsonify({
                'success': False,
                'message': 'Invalid email format'
            }), 400

        # Generate code and user ID
        pin_code = generate_random_code()
        user_id = generate_user_id()

        # Save to database
        conn = sqlite3.connect('pin_code.db')
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO pin_codes (user_id, pin_code, email)
                VALUES (?, ?, ?)
            ''', (user_id, pin_code, email))

            conn.commit()

            # Send email
            if send_email(email, pin_code, user_id):
                return jsonify({
                    'success': True,
                    'message': 'Verification code sent successfully',
                    'user_id': user_id
                })
            else:
                # If email fails, remove from database
                cursor.execute('DELETE FROM pin_codes WHERE user_id = ?', (user_id,))
                conn.commit()
                return jsonify({
                    'success': False,
                    'message': 'Failed to send email'
                }), 500

        except sqlite3.IntegrityError:
            return jsonify({
                'success': False,
                'message': 'Database error occurred'
            }), 500
        finally:
            conn.close()

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }), 500

@app.route('/verify-code', methods=['POST'])
def verify_code():
    """API endpoint to verify a PIN code"""
    try:
        data = request.get_json()

        if not data or 'user_id' not in data or 'pin_code' not in data:
            return jsonify({
                'success': False,
                'message': 'User ID and PIN code are required'
            }), 400

        user_id = data['user_id']
        pin_code = data['pin_code']

        # Check database
        conn = sqlite3.connect('pin_code.db')
        cursor = conn.cursor()

        cursor.execute('''
            SELECT email, created_at FROM pin_codes
            WHERE user_id = ? AND pin_code = ?
        ''', (user_id, pin_code))

        result = cursor.fetchone()
        conn.close()

        if result:
            email, created_at = result
            return jsonify({
                'success': True,
                'message': 'Code verified successfully',
                'email': email,
                'created_at': created_at
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid user ID or PIN code'
            }), 401

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }), 500

@app.route('/get-codes', methods=['GET'])
def get_codes():
    """API endpoint to get all codes (for testing purposes)"""
    try:
        conn = sqlite3.connect('pin_code.db')
        cursor = conn.cursor()

        cursor.execute('''
            SELECT user_id, pin_code, email, created_at FROM pin_codes
            ORDER BY created_at DESC
        ''')

        results = cursor.fetchall()
        conn.close()

        codes = []
        for row in results:
            codes.append({
                'user_id': row[0],
                'pin_code': row[1],
                'email': row[2],
                'created_at': row[3]
            })

        return jsonify({
            'success': True,
            'codes': codes
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }), 500

@app.route('/delete-code/<user_id>', methods=['DELETE'])
def delete_code(user_id):
    """API endpoint to delete a specific code"""
    try:
        conn = sqlite3.connect('pin_code.db')
        cursor = conn.cursor()

        cursor.execute('DELETE FROM pin_codes WHERE user_id = ?', (user_id,))

        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            return jsonify({
                'success': True,
                'message': f'Code for user {user_id} deleted successfully'
            })
        else:
            conn.close()
            return jsonify({
                'success': False,
                'message': 'User ID not found'
            }), 404

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'message': 'Email Forwarder Service is running',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    # Initialize database
    init_db()

    print("Email Forwarder Service Starting...")
    print("Available endpoints:")
    print("- POST /send-code - Send verification code to email")
    print("- POST /verify-code - Verify a PIN code")
    print("- GET /get-codes - Get all codes (testing)")
    print("- DELETE /delete-code/<user_id> - Delete specific code")
    print("- GET /health - Health check")
    print("\nMake sure to set these environment variables:")
    print("- SMTP_SERVER (default: smtp.gmail.com)")
    print("- SMTP_PORT (default: 587)")
    print("- EMAIL_ADDRESS (your email)")
    print("- EMAIL_PASSWORD (your app password)")

    app.run(debug=True, host='0.0.0.0', port=3000)
