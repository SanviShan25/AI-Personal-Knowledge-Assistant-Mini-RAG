from fastapi import APIRouter, UploadFile, File, Depends
from app.core.security import get_current_user
from app.services.ingestion import process_document
from app.models.user import User

router = APIRouter()

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    await process_document(file, current_user.id)
    return {"message": "Document processed successfully"}

from fastapi import APIRouter, UploadFile, File, Depends
from app.core.security import get_current_user
from app.models.user import User
from app.services.ingestion import process_document

router = APIRouter()

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    await process_document(file, current_user.id)
    return {"message": "Document processed successfully"}