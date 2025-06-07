from flask import Flask, request, jsonify
import sqlite3
import os
from werkzeug.security import generate_password_hash

app = Flask(__name__)

# Database configuration
DATABASE = 'users.db'

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
