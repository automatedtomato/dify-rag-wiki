"""
Search API for Wikipedia articles
"""

from typing import List

from fastapi import APIRouter, Depends, Query
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
    q: str = Query(..., min_length=1, description="Search query"),
    db: Session = Depends(get_db),  # Dependency injection
):
    """
    Search Wikipedia articles by title (partial match)
    """
    # Search by title including query(q)
    search_query = f"%{q}%"
    articles = (
        db.query(models.Article)
        .filter(models.Article.title.like(search_query))
        .limit(10)
        .all()
    )

    return articles
