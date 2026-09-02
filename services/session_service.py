import uuid

from flask import session


def get_visitor_id() -> str:
    if "visitor_id" not in session:
        session["visitor_id"] = str(uuid.uuid4())

    return session["visitor_id"]