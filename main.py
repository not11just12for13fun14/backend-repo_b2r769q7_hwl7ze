import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from passlib.context import CryptContext
from bson import ObjectId

from database import db, create_document, get_documents

app = FastAPI(title="SaaS Landing API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --------- Models ---------
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=6)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    id: str
    name: str
    email: EmailStr

class ContactRequest(BaseModel):
    name: str
    email: EmailStr
    message: str = Field(min_length=5)

class BlogItem(BaseModel):
    title: str
    slug: str
    excerpt: Optional[str] = None
    content: str
    author: Optional[str] = None
    tags: Optional[List[str]] = None


# --------- Helpers ---------

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


# --------- Routes ---------
@app.get("/")
def root():
    return {"message": "SaaS Landing Backend Running"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response

# Auth
@app.post("/auth/register", response_model=AuthResponse)
def register(payload: RegisterRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    existing = db["user"].find_one({"email": str(payload.email).lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_doc = {
        "name": payload.name,
        "email": str(payload.email).lower(),
        "password_hash": hash_password(payload.password),
        "is_active": True,
    }
    new_id = create_document("user", user_doc)
    return AuthResponse(id=new_id, name=user_doc["name"], email=user_doc["email"]) 

@app.post("/auth/login", response_model=AuthResponse)
def login(payload: LoginRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    user = db["user"].find_one({"email": str(payload.email).lower()})
    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or password")
    if not verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    return AuthResponse(id=str(user.get("_id")), name=user.get("name"), email=user.get("email"))

# Contact
@app.post("/contact")
def create_contact(payload: ContactRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    contact_id = create_document("contactmessage", payload.model_dump())
    return {"status": "ok", "id": contact_id}

# Blog
@app.get("/blog", response_model=List[BlogItem])
def list_blog():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    posts = get_documents("blogpost", {}, limit=50)
    if not posts:
        # Seed with 3 demo posts for the landing
        demos = [
            {
                "title": "Announcing Cardify: The Modern Fintech Toolkit",
                "slug": "announcing-cardify",
                "excerpt": "We built a developer-first toolkit to help you launch card products faster.",
                "content": "Cardify helps teams design, test, and launch card experiences with built-in compliance.",
                "author": "Team Cardify",
                "tags": ["announcement", "fintech"],
            },
            {
                "title": "Designing with Glassmorphism in Real Products",
                "slug": "glassmorphism-design",
                "excerpt": "Practical tips for using glassmorphism without sacrificing accessibility.",
                "content": "We cover contrast, motion, and depth to make glassmorphic UIs usable.",
                "author": "Maya Lee",
                "tags": ["design", "ux"],
            },
            {
                "title": "From Prototype to Production: Our Infrastructure Stack",
                "slug": "infra-stack",
                "excerpt": "How we ship fast while staying compliant.",
                "content": "A look at our APIs, data pipelines, and monitoring choices.",
                "author": "Dev Team",
                "tags": ["engineering"],
            },
        ]
        for d in demos:
            create_document("blogpost", d)
        posts = get_documents("blogpost", {}, limit=50)

    # Normalize to Pydantic response
    normalized = []
    for p in posts:
        normalized.append(
            BlogItem(
                title=p.get("title", "Untitled"),
                slug=p.get("slug", str(p.get("_id", "post"))),
                excerpt=p.get("excerpt"),
                content=p.get("content", ""),
                author=p.get("author"),
                tags=p.get("tags"),
            )
        )
    return normalized


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
