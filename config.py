"""
Central configuration for Zora AI.

Everything environment-specific lives here and nowhere else, so the
rest of the app never touches os.environ directly.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

#load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

dotenv_path=BASE_DIR / ".env"

load_dotenv(dotenv_path, override=True)

# --- Groq -----------------------------------------------------------------

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# openai/gpt-oss-120b is Groq's current flagship open-weight model —
# strong general reasoning and instruction-following, which fits a
# system-design / coding / automation assistant. Swap to
# openai/gpt-oss-20b in .env for faster, cheaper replies if 120b is
# more than you need.
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_TEMPERATURE = float(os.getenv("GROQ_TEMPERATURE", "0.6"))
GROQ_MAX_TOKENS = int(os.getenv("GROQ_MAX_TOKENS", "1024"))

SYSTEM_PROMPT = (
    "You are Zora, an AI assistant built into a local chat interface. "
    "The person you're helping designs AI systems, writes Python "
    "automation scripts, builds n8n workflows, and works with "
    "JavaScript, SQL, and Linux. Give direct, technically precise "
    "answers. Use code blocks for code. If a request is ambiguous, "
    "ask one clarifying question before proceeding instead of guessing."
)

# --- Database ---------------------------------------------------------------

# Flask convention: runtime data (the actual db file) lives in
# instance/, separate from source code, and is never committed.
INSTANCE_DIR = BASE_DIR / "instance"
DB_PATH = INSTANCE_DIR / "zora.db"

# --- Uploads ------------------------------------------------------------

UPLOAD_FOLDER = BASE_DIR / "uploads"
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB

# --- Flask ----------------------------------------------------------------

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("FLASK_DEBUG", "1") == "1"