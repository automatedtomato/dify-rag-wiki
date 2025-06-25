from logging import getLogger

from fastapi import FastAPI
from sqlalchemy import text

from . import models
from .api import articles, chat
from .common.config_loader import load_config
from .common.log_setter import setup_logger
from .database import SessionLocal, engine

# ========== Logging Config ==========
logger = getLogger(__name__)
config = load_config(layer="logger")
logger = setup_logger(logger, config=config)


#  ========== FastAPI Config ==========
app = FastAPI(
    title="Dify Chatbot API",
    description="Dify Chatbot - Wikipedia knowledge base API",
    version="0.1.0",
)

# Include API groups defined in api/
# prefix: all API endpoints defined in articles.py will be prefixed with "/api/articles"
# tags: for grouping API documents
app.include_router(articles.router, prefix="/api/articles", tags=["Articles"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])


# ========== Routers ==========
# Event handler when starting the API
@app.on_event("startup")
def on_startup():
    """When starting the API, check database connection"""

    models.Base.metadata.create_all(bind=engine)  # Create DB tables from models module

    try:
        with SessionLocal() as db:
            logger.info("Database connection successful")

            logger.info("Checking extensions...")
            # Check pg_trgm extension
            db.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
            # Check pg_vector extension
            db.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            logger.info('"pg_trgm" and "vector" extension enabled')

    except Exception as e:
        logger.error(f"Database connection failed: {e}")


# GET request endpoint for root URL("/")
@app.get("/")
def read_root():
    """
    Simple endpoint to health-check API server is
    working correctly.
    """
    return {"status": "ok", "message": "Welcome to Dify Chatbot API!"}
