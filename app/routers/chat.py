from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from app.core.auth import get_current_user
from app.schemas.auth import CurrentUser
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])
templates = Jinja2Templates(directory="app/templates")


def _sse(event: str, data: dict) -> str:
    import json

    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/messages", response_class=HTMLResponse)
def create_message(
    request: Request,
    message: str = Form(...),
    conversation_id: str | None = Form(default=None),
    user: CurrentUser = Depends(get_current_user),
):
    chat_service: ChatService = request.app.state.chat_service

    try:
        user_msg, assistant_msg = chat_service.create_user_message(
            user_id=user.user_id,
            message_text=message,
            conversation_id=conversation_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="conversation not found") from exc

    return templates.TemplateResponse(
        "components/message_pair.html",
        {
            "request": request,
            "user_msg": user_msg,
            "assistant_msg": assistant_msg,
            "conversation_id": user_msg.conversation_id,
        },
    )


@router.get("/messages/{message_id}/stream")
async def stream_message(
    request: Request,
    message_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    chat_service: ChatService = request.app.state.chat_service

    async def event_gen():
        # keep-alive / proxies
        yield ": stream-start\n\n"

        seen_done = False
        async for event in chat_service.stream_assistant_response(user.user_id, message_id):
            if event.event == "error":
                yield _sse("error", event.data)
                return
            if event.event == "done":
                seen_done = True
            yield _sse(event.event, event.data)
        if not seen_done:
            yield _sse("done", {})

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
