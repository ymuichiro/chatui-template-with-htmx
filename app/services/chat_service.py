from typing import AsyncIterator

from app.core.config import settings
from app.domain.models import Message, new_id
from app.gateways.llm.base import LLMGateway
from app.repositories.base import ChatRepository
from app.schemas.stream_events import StreamEvent


class ChatService:
    def __init__(self, repo: ChatRepository, llm: LLMGateway) -> None:
        self.repo = repo
        self.llm = llm

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
