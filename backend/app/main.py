from fastapi import FastAPI
from app.db.database import engine, Base
from app.models.user import User
from app.routes import auth

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(auth.router)

@app.get("/")
def root():
    return {"message": "AI Knowledge Assistant Running"}


from app.core.security import get_current_user
from fastapi import Depends

@app.get("/me")
def read_current_user(current_user = Depends(get_current_user)):
    return {
        "email": current_user.email,
        "id": current_user.id
    }


from app.routes import upload
app.include_router(upload.router)

from app.routes import upload
app.include_router(upload.router)

from app.routes import query
app.include_router(query.router)


from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:8501",
    "https://your-frontend-url.onrender.com"
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}