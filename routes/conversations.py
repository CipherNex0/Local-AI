"""
GET    /api/conversations                list conversations
POST   /api/conversations                create a conversation
DELETE /api/conversations                delete ALL conversations
GET    /api/conversations/export         download everything as .json
GET    /api/conversations/<id>           get one conversation + messages
PATCH  /api/conversations/<id>           rename a conversation
DELETE /api/conversations/<id>           delete a conversation
DELETE /api/conversations/<id>/messages  clear a conversation's messages
GET    /api/conversations/<id>/export    download one conversation as .txt
"""

import json

from flask import Blueprint, Response, jsonify, request

from services import conversation_service

conversations_bp = Blueprint("conversations", __name__, url_prefix="/api/conversations")


@conversations_bp.get("")
def list_conversations():
    return jsonify(conversation_service.list_conversations())


@conversations_bp.post("")
def new_conversation():
    conversation = conversation_service.create_conversation()
    return jsonify(conversation), 201


@conversations_bp.delete("")
def delete_all_conversations():
    conversation_service.delete_all_conversations()
    return "", 204


@conversations_bp.get("/export")
def export_all():
    payload = json.dumps(conversation_service.export_all(), indent=2)
    return Response(
        payload,
        mimetype="application/json",
        headers={"Content-Disposition": 'attachment; filename="zora-conversations.json"'},
    )


@conversations_bp.get("/<convo_id>")
def get_conversation(convo_id):
    convo = conversation_service.get_conversation(convo_id)
    if not convo:
        return jsonify({"error": "Conversation not found"}), 404
    return jsonify(convo)


@conversations_bp.patch("/<convo_id>")
def rename_conversation(convo_id):
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "title is required"}), 400
    return jsonify(conversation_service.rename_conversation(convo_id, title))


@conversations_bp.delete("/<convo_id>")
def delete_conversation(convo_id):
    conversation_service.delete_conversation(convo_id)
    return "", 204


@conversations_bp.delete("/<convo_id>/messages")
def clear_messages(convo_id):
    conversation_service.clear_messages(convo_id)
    return "", 204


@conversations_bp.get("/<convo_id>/export")
def export_conversation(convo_id):
    text = conversation_service.export_conversation_text(convo_id)
    if text is None:
        return jsonify({"error": "Conversation not found"}), 404
    return Response(
        text,
        mimetype="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{convo_id}.txt"'},
    )