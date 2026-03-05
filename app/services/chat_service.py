from typing import AsyncIterator

from app.core.config import settings
from app.domain.models import Conversation, Message, new_id
from app.gateways.llm.base import LLMGateway
from app.repositories.base import ChatRepository
from app.schemas.stream_events import StreamEvent


class ChatService:
    def __init__(self, repo: ChatRepository, llm: LLMGateway) -> None:
        self.repo = repo
        self.llm = llm

    def list_conversations(self, user_id: str) -> list[Conversation]:
        return self.repo.list_conversations(user_id)

    def get_conversation_messages(self, user_id: str, conversation_id: str) -> list[Message]:
        conv = self.repo.get_conversation(conversation_id, user_id)
        if not conv:
            raise KeyError("conversation not found")
        return self.repo.list_messages(conversation_id, user_id)

    def create_user_message(self, user_id: str, message_text: str, conversation_id: str | None) -> tuple[Message, Message]:
        text = message_text.strip()
        if not text:
            raise ValueError("message must not be empty")
        if len(text) > settings.max_message_length:
            raise ValueError(f"message is too long (max: {settings.max_message_length})")

        if conversation_id:
            conv = self.repo.get_conversation(conversation_id, user_id)
            if not conv:
                raise KeyError("conversation not found")
        else:
            conv = self.repo.create_conversation(user_id)
        if not conv.title:
            conv.title = self._build_conversation_title(text)

        user_msg = Message(
            id=new_id(),
            conversation_id=conv.id,
            role="user",
            content=text,
        )
        assistant_placeholder = Message(
            id=new_id(),
            conversation_id=conv.id,
            role="assistant",
            content="",
        )
        self.repo.add_message(user_msg)
        self.repo.add_message(assistant_placeholder)
        return user_msg, assistant_placeholder

    @staticmethod
    def _build_conversation_title(text: str, max_len: int = 34) -> str:
        if len(text) <= max_len:
            return text
        return f"{text[:max_len - 1].rstrip()}..."

    async def stream_assistant_response(self, user_id: str, assistant_message_id: str) -> AsyncIterator[StreamEvent]:
        assistant_msg = self.repo.get_message(assistant_message_id, user_id)
        if not assistant_msg:
            yield StreamEvent(event="error", data={"message": "message not found"})
            return

        history = self.repo.list_messages(assistant_msg.conversation_id, user_id)
        output = ""
        async for event in self.llm.stream_chat(history):
            if event.event == "token":
                output += event.data.get("text", "")
            yield event

        assistant_msg.content = output
