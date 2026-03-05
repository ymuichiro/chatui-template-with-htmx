from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.auth import get_current_user
from app.schemas.auth import CurrentUser
from app.services.chat_service import ChatService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _render_chat_page(
    request: Request,
    user: CurrentUser,
    conversation_id: str | None = None,
):
    chat_service: ChatService = request.app.state.chat_service
    conversations = chat_service.list_conversations(user.user_id)
    active_conversation_id = conversation_id or (conversations[0].id if conversations else None)
    if active_conversation_id:
        try:
            messages = chat_service.get_conversation_messages(user.user_id, active_conversation_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="conversation not found") from exc
    else:
        messages = []

    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "conversations": conversations,
            "active_conversation_id": active_conversation_id,
            "messages": messages,
        },
    )


@router.get("/", response_class=HTMLResponse)
def home(request: Request, user: CurrentUser = Depends(get_current_user)):
    return _render_chat_page(request=request, user=user)


@router.get("/c/{conversation_id}", response_class=HTMLResponse)
def conversation_page(
    request: Request,
    conversation_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    return _render_chat_page(
        request=request,
        user=user,
        conversation_id=conversation_id,
    )


@router.get("/auth/me")
def auth_me(user: CurrentUser = Depends(get_current_user)):
    return user.model_dump()
