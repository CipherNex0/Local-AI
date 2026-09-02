"""
POST /api/chat            send a message, get an AI reply
POST /api/upload           upload an attachment ahead of sending it
GET  /api/uploads/<name>   download a previously uploaded attachment
"""

from flask import Blueprint, jsonify, request, send_file

from services import conversation_service, file_service
from services.session_service import get_visitor_id
from services.ai_service import AiNotConfigured, AiRequestError
from services.file_service import UploadRejected

chat_bp = Blueprint("chat", __name__, url_prefix="/api")


@chat_bp.post("/chat")
def send_chat_message():
    data = request.get_json(silent=True) or {}
    visitor_id = get_visitor_id()
    convo_id = data.get("conversation_id")
    text = (data.get("text") or "").strip()
    attachment = data.get("attachment")
    attachment_path = data.get("attachment_path")

    if not text:
        return jsonify({"error": "text is required"}), 400
    if not convo_id:
        return jsonify({"error": "conversation_id is required"}), 400

    try:
        result = conversation_service.send_message(
            visitor_id, convo_id, text, attachment, attachment_path
        )
    except conversation_service.ConversationNotFound:
        return jsonify({"error": "Unknown conversation_id"}), 400
    except AiNotConfigured as exc:
        return jsonify({"error": str(exc), "kind": "not_configured"}), 500
    except AiRequestError as exc:
        return jsonify({"error": str(exc), "kind": "request_failed"}), 502

    return jsonify(result)


@chat_bp.post("/upload")
def upload_attachment():
    file_storage = request.files.get("file")


    try:
        saved = file_service.save_upload(file_storage)
    except UploadRejected as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(saved), 201


@chat_bp.get("/uploads/<path:stored_name>")
def download_attachment(stored_name):
    path = file_service.get_upload_path(stored_name)
    if not path:
        return jsonify({"error": "File not found"}), 404
    return send_file(path)