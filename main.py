import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from core.config import settings
from core.logging_config import setup_logging
from core.database import engine
from api.v1 import api_router as v1_router

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application...")
    yield
    logger.info("Shutting down...")
    await engine.dispose()

app = FastAPI(
    title="Travel Itinerary API",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url=None
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include only the v1 API router to avoid duplicate endpoints
app.include_router(v1_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"message": "Welcome to Travel Itinerary API. See /docs for API documentation."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)