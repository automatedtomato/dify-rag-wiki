"""
Define type and structure of request and response with pydantic
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ArticleBase(BaseModel):
    title: str
    content: str | None = None  # Consider null content


class Article(ArticleBase):
    id: int
    wiki_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ChatMessageBase(BaseModel):
    role: str
    content: str
    
class ChatMessageCreate(ChatMessageBase):
    pass

class ChatMessage(ChatMessageBase):
    id: int
    session_id: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
    
class ChatRequest(BaseModel):
    session_id: str
    query: str