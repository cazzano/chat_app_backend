from flask import Flask, request, jsonify
import jwt
import datetime
from functools import wraps
import sqlite3
from werkzeug.security import check_password_hash


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
