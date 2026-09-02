"""
Simple document reader for Zora AI.

Reads text-based files so their contents can be sent
to the AI as context.
"""

from pathlib import Path


TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".py",
    ".js",
    ".ts",
    ".html",
    ".css",
    ".json",
    ".csv",
    ".log",
}


class DocumentReadError(Exception):
    pass


def extract_text(file_path: str | Path) -> str:
    """
    Read and return the contents of a supported text file.
    """

    path = Path(file_path)

    if not path.exists():
        raise DocumentReadError("File not found.")

    if path.suffix.lower() not in TEXT_EXTENSIONS:
        raise DocumentReadError(
            f"Zora cannot read {path.suffix} files yet."
        )

    try:
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()

    except UnicodeDecodeError:
        raise DocumentReadError(
            "This file could not be read as text."
        )

    except Exception as exc:
        raise DocumentReadError(
            f"Could not read file: {exc}"
        )

    # Prevent extremely large files from being sent to the AI.
    MAX_CHARACTERS = 300

    if len(content) > MAX_CHARACTERS:
        content = content[:MAX_CHARACTERS]
        content += "\n\n[File truncated because it is too large.]"

    return content