from flask import Flask, request, jsonify,Blueprint
import sqlite3
import requests
import json
from datetime import datetime



def init_db():
    """Initialize the SQLite database and create the tokens table"""
    conn = sqlite3.connect('token.db')
    cursor = conn.cursor()

    # Create tokens table with user_id as primary key
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tokens (
            user_id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            token TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
