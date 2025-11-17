"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    password_hash: str = Field(..., description="BCrypt hashed password")
    is_active: bool = Field(True, description="Whether user is active")

class Blogpost(BaseModel):
    """
    Blog posts collection schema
    Collection name: "blogpost"
    """
    title: str = Field(...)
    slug: str = Field(..., description="URL-friendly unique slug")
    excerpt: Optional[str] = Field(None)
    content: str = Field(...)
    author: Optional[str] = Field(None)
    tags: Optional[List[str]] = Field(default=None)

class Contactmessage(BaseModel):
    """
    Contact messages collection schema
    Collection name: "contactmessage"
    """
    name: str = Field(...)
    email: EmailStr = Field(...)
    message: str = Field(..., min_length=5)
