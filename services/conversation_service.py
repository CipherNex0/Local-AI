"""
Conversation orchestration.

Routes call into this file, never into database.models or
services.ai_service directly. This is where multi-step business
rules live: auto-titling a conversation from its first message,
making sure one exists before the page renders, saving both sides of
a chat turn around the AI call.
"""

from database import models
from services import ai_service, document_service


TITLE_MAX_LEN = 34


def _derive_title(text: str) -> str:
    text = text.strip()
    return text if len(text) <= TITLE_MAX_LEN else text[:TITLE_MAX_LEN] + "…"


# --- reads ------------------------------------------------------------

def list_conversations() -> list[dict]:
    return models.list_conversations()


def get_conversation(convo_id: str) -> dict | None:
    return models.get_conversation(convo_id)


def get_initial_state(requested_id: str | None = None) -> dict:
    """
    Used by the page route to render the first paint: guarantees at
    least one conversation exists, and picks which one is active.
    """
    conversations = models.list_conversations()

    if not conversations:
        models.create_conversation("New conversation")
        conversations = models.list_conversations()

    active_id = requested_id or conversations[0]["id"]
    active = models.get_conversation(active_id) or models.get_conversation(conversations[0]["id"])

    return {"conversations": conversations, "active": active}


# --- writes -----------------------------------------------------------

def create_conversation() -> dict:
    return models.create_conversation("New conversation")


def rename_conversation(convo_id: str, title: str) -> dict:
    models.rename_conversation(convo_id, title)
    return {"id": convo_id, "title": title}


def delete_conversation(convo_id: str) -> None:
    models.delete_conversation(convo_id)


def delete_all_conversations() -> None:
    models.delete_all_conversations()


def clear_messages(convo_id: str) -> None:
    models.clear_messages(convo_id)


def export_conversation_text(convo_id: str) -> str | None:
    return models.export_conversation_text(convo_id)


def export_all() -> list[dict]:
    return models.export_all()


# --- chat ---------------------------------------------------------------

class ConversationNotFound(ValueError):
    pass


def send_message(
    convo_id: str,
    text: str,
    attachment: str | None = None,
    attachment_path: str | None = None,
) -> dict:
    """
    Saves the user's message, calls the AI provider with full
    history, saves the reply, and returns both the reply text and
    the (possibly newly-titled) conversation.

    Raises ConversationNotFound, ai_service.AiNotConfigured, or
    ai_service.AiRequestError — routes translate these to HTTP codes.
    """
    convo = models.get_conversation(convo_id)
    if not convo:
        raise ConversationNotFound(convo_id)

    if not convo["messages"]:
        models.rename_conversation(convo_id, _derive_title(text))

    # This is the text that will be sent to the AI
    message_for_ai = text

    # If a file was attached, try to read it.
    if attachment and attachment_path:
        try:
            from config import UPLOAD_FOLDER

            file_path = UPLOAD_FOLDER / attachment_path
            file_content = document_service.extract_text(file_path)
            message_for_ai = f"""
User message: 
{text}

Attached file: {attachment}

File content:
{file_content}"""

        except document_service.DocumentReadError as exc:
            # The chat should still work even if the file cannot be read.
            message_for_ai = f"""
Use message: 
{text}

Attached file: {attachment}

The file could not be read: 
{exc}"""

    # Save the ORIGINAL user message to the database.
    models.add_message(convo_id, "user", text, attachment, attachment_path)

    # Get the conversation history
    history = models.get_conversation(convo_id)["messages"]

    # Replace the latest user message with the AI-enriched version.
    if history:
        history[-1]["content"] = message_for_ai

    # Send history to Groq.
    reply = ai_service.get_reply(history)  # may raise AiNotConfigured / AiRequestError

    # Save AI response
    models.add_message(convo_id, "ai", reply)

    return {
        "reply": reply,
        "conversation": models.get_conversation(convo_id),
    }