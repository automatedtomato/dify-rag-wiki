"""
Process conversation between user and Dify.
"""

import time
from logging import getLogger

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..common.log_setter import setup_logger
from ..database import SessionLocal
from ..services.dify_client import DifyClient

logger = getLogger(__name__)
logger = setup_logger(logger=logger, log_level="DEBUG")

# Create independent endpoint group
router = APIRouter()


def get_db():
    """
    Dependency to get a SessionLocal object.

    Yields a database session that should be used as a dependency
    for endpoints that require database access. The session is
    properly closed after it is no longer needed.
    """

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close


@router.post("/", response_model=schemas.ChatMessage)
def handle_chat_message(request: schemas.ChatRequest, db: Session = Depends(get_db)):
    """
    Recieve message from user, talk with Dify,
    and save conversation to DB
    """
    logger.info("--- Chat request received ---")
    logger.info(f"Session ID: {request.session_id}, Query: '{request.query}'")

    session_id = request.session_id
    user_query = request.query

    # 1. Get conversation_id from the latest history of th session
    last_assisant_message = (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.session_id == session_id)
        .filter(models.ChatMessage.role == "assistant")
        .order_by(models.ChatMessage.created_at.desc())
        .first()
    )

    conversation_id_for_dify = (
        last_assisant_message.dify_conversation_id
        if last_assisant_message and last_assisant_message.dify_conversation_id
        else None
    )

    if conversation_id_for_dify:
        logger.debug(
            f"Continuing conversation. Dify conversation_id: {conversation_id_for_dify}"
        )
    else:
        logger.debug("Starting new conversation.")

    # 2. Save user message to DB
    user_message = models.ChatMessage(
        session_id=session_id, role="user", content=user_query
    )
    db.add(user_message)

    # 3. Call Dify client
    dify_client = DifyClient()

    logger.debug("Calling DifyClient.chat()... This may take a while.")
    start_time = time.time()

    assistant_response_content, new_conversation_id = dify_client.chat(
        user_input=user_query,
        user_id=session_id,
        conversation_id=conversation_id_for_dify,
    )

    end_time = time.time()
    logger.debug(f"DifyClient.chat() finished in {end_time - start_time:.2f} seconds.")
    logger.debug(f"Response from Dify client (content): '{assistant_response_content}'")
    logger.debug(
        f"Response from Dify client (new_conversation_id): {new_conversation_id}"
    )

    if not assistant_response_content:
        db.rollback()
        logger.error(
            "Assistant response content is empty. Rolling back and raising HTTPException."
        )
        raise HTTPException(status_code=500, detail="Failed to get response from Dify")

    # 4. Save response from Dify to db as object
    assistant_message = models.ChatMessage(
        session_id=session_id,
        role="assistant",
        content=assistant_response_content,
        dify_conversation_id=(
            new_conversation_id if new_conversation_id else conversation_id_for_dify
        ),
    )
    db.add(assistant_message)

    # 5. Commit and refresh
    db.commit()
    db.refresh(assistant_message)

    # 4. Return response to frontend
    return schemas.ChatMessage.model_validate(assistant_message)
