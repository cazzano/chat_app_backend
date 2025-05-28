from flask import Flask, request, jsonify
import sqlite3
import random
import string
import os
from datetime import datetime
import re
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

app = Flask(__name__)

# SendGrid configuration
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
FROM_EMAIL = os.getenv('FROM_EMAIL', 'noreply@yourdomain.com')  # Must be verified in SendGrid

# Validate SendGrid configuration
if not SENDGRID_API_KEY:
    print("WARNING: SENDGRID_API_KEY environment variable not set!")

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

def send_email_sendgrid(to_email, pin_code, user_id):
    """Send email using SendGrid with the generated PIN code"""
    try:
        # Check if SendGrid is configured
        if not SENDGRID_API_KEY:
            print("SendGrid API key not configured")
            return False

        # Create email content
        subject = "Your Verification Code"

        # HTML content for better formatting
        html_content = f"""
        <html>
        <head></head>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #333; text-align: center;">Verification Code</h2>
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <p style="font-size: 16px; color: #333;">Hello,</p>
                    <p style="font-size: 16px; color: #333;">Your verification code is:</p>
                    <div style="background-color: #e9ecef; padding: 15px; border-left: 4px solid #007bff; margin: 15px 0;">
                        <h3 style="margin: 0; color: #007bff; font-family: monospace; letter-spacing: 2px;">{pin_code}</h3>
                    </div>
                    <p style="font-size: 14px; color: #666;">
                        <strong>User ID:</strong> {user_id}<br>
                        <strong>Generated on:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    </p>
                    <p style="font-size: 14px; color: #dc3545; margin-top: 20px;">
                        ⚠ Please keep this code secure and do not share it with anyone.
                    </p>
                </div>
                <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6;">
                    <p style="font-size: 12px; color: #6c757d;">
                        This email was sent by Email Forwarder Service
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        # Plain text version
        plain_content = f"""
        Hello,

        Your verification code is: {pin_code}
        User ID: {user_id}

        This code was generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

        Please keep this code secure and do not share it with anyone.

        Best regards,
        Email Forwarder Service
        """

        # Create the mail object
        message = Mail(
            from_email=FROM_EMAIL,
            to_emails=to_email,
            subject=subject,
            html_content=html_content,
            plain_text_content=plain_content
        )

        # Send email
        sg = SendGridAPIClient(api_key=SENDGRID_API_KEY)
        response = sg.send(message)

        # Check if email was sent successfully
        if response.status_code in [200, 201, 202]:
            print(f"Email sent successfully to {to_email}. Status: {response.status_code}")
            return True
        else:
            print(f"Failed to send email. Status: {response.status_code}")
            return False

    except Exception as e:
        print(f"Error sending email via SendGrid: {str(e)}")
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

        # Check if SendGrid is configured
        if not SENDGRID_API_KEY:
            return jsonify({
                'success': False,
                'message': 'Email service not configured'
            }), 500

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

            # Send email via SendGrid
            if send_email_sendgrid(email, pin_code, user_id):
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
        'sendgrid_configured': bool(SENDGRID_API_KEY),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/test-sendgrid', methods=['POST'])
def test_sendgrid():
    """Test SendGrid configuration"""
    try:
        data = request.get_json()
        if not data or 'email' not in data:
            return jsonify({
                'success': False,
                'message': 'Test email address is required'
            }), 400

        test_email = data['email']

        # Send test email
        if send_email_sendgrid(test_email, "TEST123", "U00"):
            return jsonify({
                'success': True,
                'message': 'Test email sent successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to send test email'
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Test failed: {str(e)}'
        }), 500

if __name__ == '__main__':
    # Initialize database
    init_db()

    print("="*60)
    print("📧 EMAIL FORWARDER SERVICE WITH SENDGRID")
    print("="*60)

    print("\n🚀 Available endpoints:")
    print("- POST /send-code - Send verification code to email")
    print("- POST /verify-code - Verify a PIN code")
    print("- GET /get-codes - Get all codes (testing)")
    print("- DELETE /delete-code/<user_id> - Delete specific code")
    print("- GET /health - Health check")
    print("- POST /test-sendgrid - Test SendGrid configuration")

    print("\n⚙  Required Environment Variables:")
    print("- SENDGRID_API_KEY: Your SendGrid API key (REQUIRED)")
    print("- FROM_EMAIL: Verified sender email in SendGrid (REQUIRED)")

    print("\n📋 SendGrid Setup Instructions:")
    print("1. Sign up at https://sendgrid.com")
    print("2. Verify your sender email/domain")
    print("3. Create an API key with 'Mail Send' permissions")
    print("4. Set environment variables:")
    print("   export SENDGRID_API_KEY='your_api_key_here'")
    print("   export FROM_EMAIL='your_verified_email@domain.com'")

    if not SENDGRID_API_KEY:
        print("\n⚠  WARNING: SENDGRID_API_KEY not configured!")
        print("   The email service will not work until you set this variable.")

    print("\n" + "="*60)

    app.run(debug=True, host='0.0.0.0', port=3000)
