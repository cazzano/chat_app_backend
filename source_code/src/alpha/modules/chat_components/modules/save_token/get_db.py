from flask import Flask, request, jsonify,Blueprint
import sqlite3
import requests
import json
from datetime import datetime


def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect('token.db')
    conn.row_factory = sqlite3.Row
    return conn
