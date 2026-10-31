from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path
from threading import Lock
from uuid import UUID, uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from decimal import InvalidOperation
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from groq import APIError, AuthenticationError, Groq, RateLimitError
from pydantic import BaseModel, Field

from store_agent.agent import Agent
from store_agent.catalog import Catalog


ROOT = Path(__file__).resolve().parent.parent


class ChatMessage(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    session_id: UUID | None = None


def create_app(client=None):
    load_dotenv(ROOT / ".env")
    owns_client = client is None
    if client is None and os.getenv("GROQ_API_KEY"):
        client = Groq(max_retries=0, timeout=30)

    @asynccontextmanager
    async def lifespan(app):
        yield
        if owns_client and client:
            client.close()

    app = FastAPI(title="Empório da Música", lifespan=lifespan)
    sessions = {}
    busy = Lock()
    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    catalog = Catalog()
    app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

    @app.get("/")
    def index():
        return FileResponse(ROOT / "static" / "index.html")

    @app.get("/api/health")
    def health():
        return {"configured": client is not None}

    @app.get("/api/catalog")
    def browse_catalog(
        query: str = Query(default="", max_length=100),
        category: str = Query(default="", max_length=100),
        max_price: str | None = Query(default=None, max_length=20),
        offset: int = Query(default=0, ge=0),
    ):
        try:
            result = catalog.search_products(
                query=query, category=category, max_price=max_price, offset=offset, limit=12,
            )
        except (ValueError, InvalidOperation):
            raise HTTPException(422, "Enter a valid, non-negative maximum price.") from None
        result["categories"] = catalog.list_categories()["categories"]
        return result

    @app.post("/api/chat")
    def chat(body: ChatMessage):
        if not client:
            raise HTTPException(503, "The assistant is not configured. Set the server's Groq API key.")
        if not body.message.strip():
            raise HTTPException(422, "Please enter a message.")
        if not busy.acquire(blocking=False):
            raise HTTPException(409, "Another message is being answered. Please wait a moment.")
        try:
            session_id = str(body.session_id) if body.session_id else str(uuid4())
            if body.session_id and session_id not in sessions:
                raise HTTPException(404, "This conversation has ended. Start a new conversation.")
            if session_id not in sessions:
                # Bound memory use in this local demo; oldest sessions are discarded.
                if len(sessions) >= 20:
                    sessions.pop(next(iter(sessions)))
                sessions[session_id] = Agent(client, model=model)
            agent = sessions[session_id]
            answer = agent.reply(body.message)
            logging.getLogger("uvicorn.error").info(
                "Chat completed: requests=%s tokens=%s tools=%s",
                agent.requests, agent.tokens, [call["tool"] for call in agent.calls],
            )
            return {"answer": answer, "session_id": session_id}
        except RateLimitError as error:
            headers = {}
            wait = error.response.headers.get("retry-after")
            if wait:
                headers["Retry-After"] = wait
            raise HTTPException(429, "The assistant reached its usage limit. Please try again later.", headers=headers) from None
        except AuthenticationError:
            raise HTTPException(503, "The assistant's API credentials need to be checked on the server.") from None
        except APIError as error:
            logging.getLogger("uvicorn.error").warning(
                "Groq request failed: type=%s status=%s requests=%s reported_tokens=%s",
                type(error).__name__, getattr(error, "status_code", None),
                agent.requests, agent.tokens,
            )
            raise HTTPException(502, "The assistant is temporarily unavailable. Please try again later.") from None
        except (ValueError, RuntimeError):
            raise HTTPException(502, "The assistant could not complete this answer. Try a more specific question.") from None
        finally:
            busy.release()

    @app.delete("/api/sessions/{session_id}")
    def clear_session(session_id: UUID):
        if not busy.acquire(blocking=False):
            raise HTTPException(409, "Please wait for the current answer before clearing the conversation.")
        try:
            sessions.pop(str(session_id), None)
            return {"cleared": True}
        finally:
            busy.release()

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
