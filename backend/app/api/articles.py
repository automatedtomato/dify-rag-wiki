"""
Search API for Wikipedia articles
"""

from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import SessionLocal

# Create endpoint group independent from main.py
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
        db.close()


@router.get("/search", response_model=List[schemas.Article])
# Response model = List[schemas.Article]:
# This indicates that this API response is a list of Article schema object
def search_articles(
    q: str = Query(..., min_length=2, description="Search query (2 < characters)"),
    db: Session = Depends(get_db),  # Dependency injection
):
    """
    Search Wikipedia articles by title and content using Trigram index.
    Search results will be sorted by similarity score.
    """

    # SQL func to calculate similarity.
    # `greatest` return the highest value from a list of values.
    # This makes it possible to get highest similarity result
    # among title and content.
    similarity_score = func.greatest(
        func.similarity(models.Article.title, q),
        func.similarity(models.Article.content, q),
    ).label(
        "similarity"
    )  # labelling similarity_score as similarity

    # Filter by similarity score and sor by value
    # `title % q` is to calculate similarity between title and query(q) and
    # check if the similarity is greater than threshold.
    articles = (
        db.query(models.Article)
        .filter(or_(models.Article.title.op("%")(q), models.Article.content.op("%")(q)))
        .order_by(similarity_score.desc())
        .limit(10)
        .all()
    )

    return articles
