from collections import defaultdict

from app.domain.models import Conversation, Message, new_id


class InMemoryRepository:
    def __init__(self) -> None:
        self.conversations: dict[str, Conversation] = {}
        self.messages: dict[str, Message] = {}
        self.message_ids_by_conversation: dict[str, list[str]] = defaultdict(list)

    def create_conversation(self, user_id: str) -> Conversation:
        conv = Conversation(id=new_id(), user_id=user_id)
        self.conversations[conv.id] = conv
        return conv

    def get_conversation(self, conversation_id: str, user_id: str) -> Conversation | None:
        conv = self.conversations.get(conversation_id)
        if not conv or conv.user_id != user_id:
            return None
        return conv

    def add_message(self, message: Message) -> None:
        self.messages[message.id] = message
        self.message_ids_by_conversation[message.conversation_id].append(message.id)

    def list_messages(self, conversation_id: str, user_id: str) -> list[Message]:
        conv = self.get_conversation(conversation_id, user_id)
        if not conv:
            return []
        ids = self.message_ids_by_conversation.get(conversation_id, [])
        return [self.messages[mid] for mid in ids]

    def get_message(self, message_id: str, user_id: str) -> Message | None:
        msg = self.messages.get(message_id)
        if not msg:
            return None
        conv = self.get_conversation(msg.conversation_id, user_id)
        if not conv:
            return None
        return msg
