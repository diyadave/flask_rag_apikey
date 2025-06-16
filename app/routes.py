from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from app.services.story_generator import StoryGenerator
import uuid
from datetime import datetime
from pathlib import Path
import json
import os

main_bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

# Session storage in the app folder
SESSIONS_FILE = Path(__file__).parent.parent / 'sessions.json'

def _ensure_sessions_file():
    """Ensure sessions.json exists and is valid JSON"""
    if not SESSIONS_FILE.exists():
        with open(SESSIONS_FILE, 'w') as f:
            json.dump({}, f)
    else:
        # Validate existing file
        try:
            with open(SESSIONS_FILE, 'r') as f:
                content = f.read()
                if content.strip():  # Only parse if not empty
                    json.loads(content)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Invalid sessions.json, resetting: {str(e)}")
            with open(SESSIONS_FILE, 'w') as f:
                json.dump({}, f)

def _load_sessions():
    """Load sessions from file with error handling"""
    _ensure_sessions_file()
    try:
        with open(SESSIONS_FILE, 'r') as f:
            content = f.read()
            return json.loads(content) if content.strip() else {}
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error loading sessions: {str(e)}")
        return {}

def _save_sessions(sessions):
    """Save sessions to file with error handling"""
    try:
        with open(SESSIONS_FILE, 'w') as f:
            json.dump(sessions, f, indent=2)
    except IOError as e:
        logger.error(f"Error saving sessions: {str(e)}")
        raise

# In routes.py
@main_bp.route('/generate_story', methods=['POST'])
@jwt_required()
def generate_story():
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400

    data = request.get_json()
    if not data or 'prompt' not in data:
        return jsonify({"error": "Prompt is required"}), 400

    try:
        generator = StoryGenerator()
        result = generator.generate_story(
            prompt=data.get('prompt'),
            category=data.get('category')
        )
        
        if "error" in result:
            return jsonify(result), 500
            
        return jsonify({"story": result["response"]})  # Simplified response
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({"error": "Processing failed"}), 500