from flask import Flask, request, jsonify,Blueprint
import sqlite3
import requests
import json
from datetime import datetime
from modules.save_token.init_db import init_db
from modules.save_token.get_db import get_db_connection
from apis.save_token.save_token import save_token_

app = Flask(__name__)

app.register_blueprint(save_token_)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'Token API is running'}), 200

if __name__ == '__main__':
    # Initialize database when starting the application
    init_db()
    print("Database initialized successfully!")
    print("Starting Flask Token Management API...")
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=2001)
