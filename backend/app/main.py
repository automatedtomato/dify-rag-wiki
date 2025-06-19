from logging import getLogger

from fastapi import FastAPI
from sqlalchemy import text

from . import models
from .common.config_loader import load_config
from .common.log_setter import setup_logger
from .database import SessionLocal, engine

logger = getLogger(__name__)
config = load_config(layer="logger")
logger = setup_logger(logger, config=config)

app = FastAPI(
    title="Dify Chatbot API",
    description="Dify Chatbot - Wikipedia knowledge base API",
    version="0.1.0",
)


# Event handler when starting the API
@app.on_event("startup")
def on_startup():
    """When starting the API, check database connection"""

    models.Base.metadata.create_all(bind=engine)  # Create DB tables from models module

    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))  # Check connection
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
