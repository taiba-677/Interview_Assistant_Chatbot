# from fastapi import APIRouter, UploadFile, File
# import os

# router = APIRouter()  

# UPLOAD_DIR = "data/uploads"
# os.makedirs(UPLOAD_DIR, exist_ok=True)

# @router.post("/upload")
# async def upload_cv(file: UploadFile = File(...)):
#     file_path = os.path.join(UPLOAD_DIR, file.filename)

#     with open(file_path, "wb") as f:
#         f.write(await file.read())

#     return {"filename": file.filename}


# newas open api key

# from fastapi import APIRouter, UploadFile, File, HTTPException
# import os
# import uuid

# # Import pipeline services
# from app.services.pdf_reader import extract_text_from_pdf
# from app.services.pii_masking import mask_pii
# from app.services.chunking import split_text
# from app.db.vector_store import create_vector_store

# router = APIRouter()

# UPLOAD_DIR = "data/uploads"
# os.makedirs(UPLOAD_DIR, exist_ok=True)


# @router.post("/upload")
# def upload_cv(file: UploadFile = File(...)):
#     try:
#         file_path = os.path.join(UPLOAD_DIR, file.filename)

#         with open(file_path, "wb") as f:
#             f.write(file.file.read())

#         raw_text = extract_text_from_pdf(file_path)
        
#         # Clean up the file after extraction
#         os.remove(file_path)
        
#         masked_text = mask_pii(raw_text)
#         chunks = split_text(masked_text)
        
#         user_id = str(uuid.uuid4())
#         create_vector_store(chunks, user_id)

#         return {
#             "message": "CV processed successfully",
#             "chunks": len(chunks),
#             "user_id": user_id
#         }

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))





#gemini open key

from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import uuid

from app.core.config import settings

# Import pipeline services
from app.services.pdf_reader import extract_text_from_pdf
from app.services.pii_masking import mask_pii
from app.services.chunking import split_text
from app.db.vector_store import create_vector_store
from app.db.session import get_db
from sqlalchemy.orm import Session
from fastapi import Depends
from app.models.sql_models import Resume

router = APIRouter()

UPLOAD_DIR = settings.UPLOAD_DIR
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
def upload_cv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if file.content_type != "application/pdf" and not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400, 
            detail="Invalid file format. Only PDF files are allowed."
        )

    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)

        with open(file_path, "wb") as f:
            f.write(file.file.read())

        raw_text = extract_text_from_pdf(file_path)

        # Clean up the file after extraction
        os.remove(file_path)

        masked_text = mask_pii(raw_text)
        chunks = split_text(masked_text)

        user_id = str(uuid.uuid4())
        
        # 1. Save to PostgreSQL (Clean/Masked text)
        db_resume = Resume(
            user_id=user_id,
            filename=file.filename,
            content=masked_text
        )
        db.add(db_resume)
        db.commit()
        db.refresh(db_resume)

        # 2. Save to Chroma DB (Embeddings)
        create_vector_store(chunks, user_id)

        return {
            "message": "CV processed successfully",
            "chunks": len(chunks),
            "user_id": user_id,
            "postgres_id": str(db_resume.resume_id)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
