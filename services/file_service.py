"""
Attachment handling.

Uploaded files are saved under uploads/ with a uuid-prefixed name so
two people attaching "notes.txt" never collide, while the original
filename is kept for display. Nothing here touches the database —
conversation_service decides what to do with the returned names.
"""

import uuid
from pathlib import Path

from werkzeug.utils import secure_filename

from config import UPLOAD_FOLDER, MAX_UPLOAD_SIZE

ALLOWED_EXTENSIONS = {
    "txt", "md", "csv", "json", "log",
    "py", "js", "ts",
    "html", "css", "c", "cpp", "c++",
    "png", "jpg", "jpeg", "gif", "webp",
    "pdf",
}


class UploadRejected(ValueError):
    pass


def _extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def save_upload(file_storage) -> dict:
    """
    file_storage: a werkzeug FileStorage from request.files.

    Returns {"stored_name": ..., "original_name": ...}
    Raises UploadRejected for empty/disallowed/oversized files.
    """
    if not file_storage or not file_storage.filename:
        raise UploadRejected("No file provided.")

    original_name = secure_filename(file_storage.filename)
    if not original_name:
        raise UploadRejected("Invalid filename.")

    ext = _extension(original_name)
    if ext not in ALLOWED_EXTENSIONS:
        raise UploadRejected(f"Files of type .{ext} aren't supported.")

    file_storage.seek(0, 2)  # seek to end
    size = file_storage.tell()
    file_storage.seek(0)
    if size > MAX_UPLOAD_SIZE:
        raise UploadRejected("File is larger than the 10 MB limit.")

    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}_{original_name}"
    file_storage.save(UPLOAD_FOLDER / stored_name)

    return {"stored_name": stored_name, "original_name": original_name}


def get_upload_path(stored_name: str) -> Path | None:
    safe = secure_filename(stored_name)
    path = UPLOAD_FOLDER / safe
    if not path.exists() or not path.is_file():
        return None
    return path