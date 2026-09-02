"""
Zora AI — application entry point.

This file's only job is to build the Flask app: register the three
blueprints in routes/, make sure the database exists, and run the
dev server. All actual logic lives in routes/ (thin controllers) and
services/ (business logic) — nothing here should grow beyond this.
"""

from flask import Flask

import config
from database import init_db
from routes import chat_bp, conversations_bp, pages_bp


def create_app() -> Flask:
    app = Flask(__name__)

    if not config.SECRET_KEY:
        raise RuntimeError(
            "SECRET_KEY is missing. Add it to your environment variables."
        )

    app.secret_key = config.SECRET_KEY

    app.register_blueprint(pages_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(conversations_bp)

    @app.before_request
    def _ensure_db():
        init_db()

    return app


app = create_app()

if __name__ == "__main__":
    init_db()
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)