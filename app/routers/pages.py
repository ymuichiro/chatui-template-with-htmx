from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.auth import get_current_user
from app.schemas.auth import CurrentUser

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def home(request: Request, user: CurrentUser = Depends(get_current_user)):
    return templates.TemplateResponse("chat.html", {"request": request, "user": user})


@router.get("/auth/me")
def auth_me(user: CurrentUser = Depends(get_current_user)):
    return user.model_dump()
