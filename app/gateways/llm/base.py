from typing import AsyncIterator, Protocol

from app.domain.models import Message
from app.schemas.stream_events import StreamEvent


class LLMGateway(Protocol):
    async def stream_chat(self, messages: list[Message]) -> AsyncIterator[StreamEvent]: ...
