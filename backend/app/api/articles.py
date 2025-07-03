"""
Search API for Wikipedia articles
"""

from logging import getLogger
from typing import List
import time

import torch
from fastapi import APIRouter, Depends, HTTPException, Query
from sentence_transformers import SentenceTransformer
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from .. import models, schemas
from ..common.log_setter import setup_logger
from ..database import SessionLocal

# ========== Logging Config ==========
logger = getLogger(__name__)
logger = setup_logger(logger=logger, log_level="DEBUG")

# ========== Constants ==========
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
logger.info(f"Using device: {DEVICE}")


# Create endpoint group independent from main.py
router = APIRouter()

# Load model
model = SentenceTransformer(MODEL_NAME, device=DEVICE)


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
        db.close()


@router.get("/search", response_model=List[schemas.Article])
# Response model = List[schemas.Article]:
# This indicates that this API response is a list of Article schema object
def search_articles(
    q: str = Query(..., min_length=2, description="Search query (2 < characters)"),
    db: Session = Depends(get_db),  # Dependency injection
):
    """
    Perform a hybrid search using both keyword (pg_trgm) and semantic (pg_vector).
    """
    logger.info("--- Search request received ---")
    logger.info(f"Query: {q}")
    
    # Stage 1: Keyword Search (limit to 100)
    try:
        logger.info("[Step 1/6] Starting keyword search (pg_trgm)...")
        start_time = time.time()
        trigram_similarity = func.greatest(
            func.similarity(models.Article.title, q),
            func.similarity(models.Article.content, q),
        ).label("trigram_similarity")

        candidates = (
            db.query(models.Article.id)  # get only ID for faster query
            .filter(
                or_(models.Article.title.op("%")(q), models.Article.content.op("%")(q))
            )
            .order_by(trigram_similarity.desc())
            .limit(100)
            .all()
        )

        candidate_ids = [article_id for article_id, in candidates]

        logger.info(f"[Step 2/6] Keyword search found {len(candidate_ids)} candidates in {time.time() - start_time:.2f} seconds.")
        if not candidate_ids:
            logger.warning("Keyword search returned no results")
            return []

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error during keword search stage: {e}"
        )

    # Stage 2: Semantic Search (limit to 10)
    try:
        logger.info("[Step 3/6] Vectorizing query...")
        start_time = time.time()

        query_vector = model.encode(q, convert_to_tensor=False, device=DEVICE)
        logger.info(f"[Step 4/6] Query vectorized successfully in {time.time() - start_time:.2f} seconds.")
        
        # Usin l2_distance (<->) to sort by similarity
        logger.info("[Step 5/6] Starting semantic search (pg_vector re-ranking)...")
        start_time = time.time()
        final_articles = (
            db.query(models.Article)
            .filter(models.Article.id.in_(candidate_ids))
            .order_by(models.Article.content_vector.l2_distance(query_vector))
            .limit(10)
            .all()
        )

        logger.info(f"[Step 6/6] Semantic search complete in {time.time() - start_time:.2f} seconds. Returning results.")
        return final_articles

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error during semantic search stage: {e}"
        )
