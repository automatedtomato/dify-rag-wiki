"""
models.py

This module is used to define the database models for the application.
"""

from sqlalchemy import BigInteger, Column, DateTime, Integer, String, Text, ForeignKey
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

class ChatMessage(Base):
    """ 
    Table model for chat messages
    """
    
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Which conversation this message belongs to
    session_id = Column(String(255), nullable=False, index=True)
    
    # Type of message: 'user' or 'assistant'
    role = Column(String(50), nullable=False)
    
    # Message content
    content = Column(Text, nullable=False)
    
    created_at = Column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    def __repr__(self):
        return f"<ChatMessage(session_id='{self.session_id}', role='{self.role}')>"