"""
GET /  — renders the chat page.
"""

from flask import Blueprint, render_template, request

from services import conversation_service, session_service

pages_bp = Blueprint("pages", __name__)


@pages_bp.route("/")
def index():
    visitor_id = session_service.get_visitor_id()

    requested_id = request.args.get("conversation")

    state = conversation_service.get_initial_state(visitor_id, requested_id)

    return render_template(
        "index.html",
        conversations=state["conversations"],
        active=state["active"],
        initial_state=state,
    )