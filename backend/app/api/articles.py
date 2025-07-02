"""
Search API for Wikipedia articles
"""

from logging import getLogger
from typing import List

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
logger = setup_logger(logger=logger)

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

    # Stage 1: Keyword Search (limit to 100)
    try:
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

        if not candidate_ids:
            logger.warning("Keyword search returned no results")
            return []

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error during keword search stage: {e}"
        )

    # Stage 2: Semantic Search (limit to 10)
    try:
        query_vector = model.encode(q, convert_to_tensor=False, device=DEVICE)
        # Usin l2_distance (<->) to sort by similarity
        final_articles = (
            db.query(models.Article)
            .filter(models.Article.id.in_(candidate_ids))
            .order_by(models.Article.content_vector.l2_distance(query_vector))
            .limit(10)
            .all()
        )

        return final_articles

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error during semantic search stage: {e}"
        )
