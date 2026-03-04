from typing import Literal

from pydantic import BaseModel


class StreamEvent(BaseModel):
    event: Literal[
        "token", "tool_call_start", "tool_call_args", "tool_result", "done", "error"
    ]
    data: dict
