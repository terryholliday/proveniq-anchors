from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.database import engine, Base
from app.routers import events, anchors, health


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown: Clean up
    await engine.dispose()


app = FastAPI(
    title="PROVENIQ Anchors",
    description="The Physical Trust Layer — Event ingestion and anchor management",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
origins = settings.allowed_origins.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router, tags=["Health"])
app.include_router(events.router, prefix="/api/v1", tags=["Events"])
app.include_router(anchors.router, prefix="/api/v1", tags=["Anchors"])


@app.get("/")
async def root():
    return {
        "service": "PROVENIQ Anchors",
        "version": "0.1.0",
        "status": "operational",
        "docs": "/docs",
    }
