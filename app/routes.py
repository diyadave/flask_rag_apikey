from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from app.services.story_generator import StoryGenerator
import uuid
from datetime import datetime
from pathlib import Path
import json

main_bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

# Path to sessions file
SESSIONS_FILE = Path(__file__).parent.parent / 'sessions.json'

def _ensure_sessions_file():
    """Ensure sessions.json exists and is valid JSON"""
    if not SESSIONS_FILE.exists():
        SESSIONS_FILE.write_text('{}')
    else:
        try:
            content = SESSIONS_FILE.read_text()
            if content.strip():
                json.loads(content)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Invalid sessions.json, resetting: {str(e)}")
            SESSIONS_FILE.write_text('{}')

def _load_sessions():
    """Load sessions from file with error handling"""
    _ensure_sessions_file()
    try:
        content = SESSIONS_FILE.read_text()
        return json.loads(content) if content.strip() else {}
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error loading sessions: {str(e)}")
        return {}

def _save_sessions(sessions):
    """Save sessions to file with error handling"""
    try:
        SESSIONS_FILE.write_text(json.dumps(sessions, indent=2))
    except IOError as e:
        logger.error(f"Error saving sessions: {str(e)}")
        raise

@main_bp.route('/generate_story', methods=['POST'])
@jwt_required()
def generate_story():
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400

    data = request.get_json()
    if 'prompt' not in data or 'category' not in data:
        return jsonify({"error": "Prompt and category are required"}), 400

    try:
        generator = StoryGenerator()
        result = generator.generate_story(
            prompt=data['prompt'],
            category=data['category']
        )

        if "error" in result:
            return jsonify(result), 500

        # Optionally store session info
        session_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        user_email = get_jwt_identity()

        session_data = {
            "user": user_email,
            "prompt": data['prompt'],
            "category": data['category'],
            "story": result['response'],
            "timestamp": timestamp
        }

        sessions = _load_sessions()
        sessions[session_id] = session_data
        _save_sessions(sessions)

        return jsonify({
            "session_id": session_id,
            "story": result['response'],
            "timestamp": timestamp
        }), 200

    except Exception as e:
        logger.error(f"Error during story generation: {str(e)}")
        return jsonify({"error": "Story generation failed"}), 500

@main_bp.route("/", methods=["GET"])
def index():
    return jsonify({"message": "Diya's RAG API is running."}), 200