from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.gateways.llm.mock_gateway import MockGateway
from app.repositories.in_memory import InMemoryRepository
from app.routers import chat, pages
from app.services.chat_service import ChatService

app = FastAPI(title="chatui-template-with-htmx")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/healthz")
def healthz():
    return {"ok": True}


# simple shared instances for template app
repo = InMemoryRepository()
llm = MockGateway()
app.state.chat_service = ChatService(repo=repo, llm=llm)

app.include_router(pages.router)
app.include_router(chat.router)
