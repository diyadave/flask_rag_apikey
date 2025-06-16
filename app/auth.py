from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
import os
import json
from pathlib import Path

auth_bp = Blueprint('auth', __name__)

# User storage in the app folder
USERS_FILE = Path(__file__).parent.parent / 'users.json'

def _load_users():
    if not USERS_FILE.exists():
        return {}
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def _save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or 'email' not in data or 'password' not in data or 'name' not in data:
        return jsonify({"error": "Name, email and password are required"}), 400
    
    users = _load_users()
    
    if data['email'] in users:
        return jsonify({"error": "Email already registered"}), 400
    
    users[data['email']] = {
        'name': data['name'],
        'password': generate_password_hash(data['password']),
        'email': data['email']
    }
    
    _save_users(users)
    
    return jsonify({"message": "User registered successfully"}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({"error": "Email and password are required"}), 400
    
    users = _load_users()
    user = users.get(data['email'])
    
    if not user or not check_password_hash(user['password'], data['password']):
        return jsonify({"error": "Invalid credentials"}), 401
    
    access_token = create_access_token(identity=user['email'])
    return jsonify({
        "access_token": access_token,
        "user": {
            "name": user['name'],
            "email": user['email']
        }
    }), 200