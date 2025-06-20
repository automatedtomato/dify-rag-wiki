from logging import getLogger

from fastapi import FastAPI
from sqlalchemy import text

from . import models
from .api import articles
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

# Include API groups defined in articles.py.
# prefix: all API endpoints defined in articles.py will be prefixed with "/api/articles"
# tags: for grouping API documents
app.include_router(articles.router, prefix="/api/articles", tags=["Articles"])


# ========== Routers ==========
# Event handler when starting the API
@app.on_event("startup")
def on_startup():
    """When starting the API, check database connection"""

    models.Base.metadata.create_all(bind=engine)  # Create DB tables from models module

    try:
        db = SessionLocal()
        # Check connection # wrap with text() to prevent SQL injection
        db.execute(text("SELECT 1"))
        logger.info("Database connection successful")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
    finally:
        db.close()


# GET request endpoint for root URL("/")
@app.get("/")
def read_root():
    """
    Simple endpoint to health-check API server is
    working correctly.
    """
    return {"status": "ok", "message": "Welcome to Dify Chatbot API!"}
