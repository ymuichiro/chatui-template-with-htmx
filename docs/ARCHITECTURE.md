# Architecture

## 1. System Overview

This application is a server-rendered chat UI built with FastAPI + HTMX.

- Frontend: Jinja2 templates + HTMX + SSE stream rendering
- Backend: FastAPI routers + service layer + repository layer
- Authentication: JWT-based (`proxy` or `dev_demo`)

## 2. Request Flow

### Initial page load

1. `GET /` or `GET /c/{conversation_id}`
2. `pages` router resolves current user and active conversation
3. `chat.html` is rendered with sidebar + message list

### Send message

1. `POST /chat/messages`
2. `ChatService.create_user_message(...)` creates user + assistant placeholder
3. `components/message_pair.html` is appended to `#chat-log`
4. Browser opens SSE to `/chat/messages/{message_id}/stream`

### Stream response

1. Backend emits SSE events (`token`, `tool_call_*`, `done`)
2. Frontend updates assistant bubble in real time
3. Conversation list is refreshed after completion

## 3. Layer Responsibilities

- `app/routers`
  - HTTP API, template responses, error mapping
- `app/services`
  - Conversation/message use cases
- `app/repositories`
  - Data storage abstraction (`InMemoryRepository`)
- `app/gateways/llm`
  - LLM provider abstraction (`MockGateway`)
- `app/core`
  - Configuration and auth dependency

## 4. Conversation URL Model

- Root page: `/`
- Conversation page: `/c/{conversation_id}`
- Sidebar selection uses `hx-push-url` so URL and UI stay synchronized.

## 5. Directory Structure

```text
app/
  core/
    auth.py
    config.py
  routers/
    pages.py
    chat.py
  services/
    chat_service.py
  repositories/
    base.py
    in_memory.py
  gateways/
    llm/
      base.py
      mock_gateway.py
  domain/
    models.py
  schemas/
    auth.py
    stream_events.py
  templates/
    base.html
    chat.html
    components/
  static/
    css/
scripts_gen_demo_jwt.py
```
