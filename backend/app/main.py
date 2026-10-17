from __future__ import annotations
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import router
from .config import get_settings
from .graph.builder import build_graph
from .rag.ingest import ingest

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    Path(settings.sqlite_path).parent.mkdir(parents=True, exist_ok=True)
    app.state.db = sqlite3.connect(settings.sqlite_path, check_same_thread=False)
    app.state.db.execute("CREATE TABLE IF NOT EXISTS threads (id TEXT PRIMARY KEY, state TEXT NOT NULL)")
    app.state.db.commit()
    app.state.graph = build_graph(ingest(settings.pdf_dir, settings.chroma_dir))
    yield
    app.state.db.close()

app = FastAPI(title="Northwind HR Assistant", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=get_settings().origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(router)
