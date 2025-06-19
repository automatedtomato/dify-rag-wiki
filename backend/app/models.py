"""
models.py

This module is used to define the database models for the application.
"""

from sqlalchemy import BigInteger, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from .database import Base


class Article(Base):
    """
    Table model for Wikipedia articles
    """

    # Define table name
    __tablename__ = "articles"

    # Define table columns
    id = Column(Integer, primary_key=True, index=True)
    wiki_id = Column(
        BigInteger, unique=True, nullable=False, index=True
    )  # Wikipedia article ID
    title = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now()
    )

    def __repr__(self):
        return f"<Article(id={self.id}, title='{self.title}')>"
