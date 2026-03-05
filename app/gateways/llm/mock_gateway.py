import asyncio
from typing import AsyncIterator

from app.domain.models import Message
from app.schemas.stream_events import StreamEvent


class MockGateway:
    async def stream_chat(self, messages: list[Message]) -> AsyncIterator[StreamEvent]:
        text = "Hello! This is a mock response. Tool-call events are shown in real time."

        yield StreamEvent(event="tool_call_start", data={"name": "get_weather", "call_id": "call_1"})
        await asyncio.sleep(0.1)
        yield StreamEvent(event="tool_call_args", data={"call_id": "call_1", "args": {"city": "Tokyo"}})
        await asyncio.sleep(0.1)
        yield StreamEvent(event="tool_result", data={"call_id": "call_1", "result": {"temp_c": 23}})

        for ch in text:
            await asyncio.sleep(0.02)
            yield StreamEvent(event="token", data={"text": ch})

        yield StreamEvent(event="done", data={})
