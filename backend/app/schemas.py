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
