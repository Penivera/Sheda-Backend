from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status, Query
from typing import Annotated, List, Optional

from cloudinary import uploader

from app.schemas.transaction_schema import (
    TransactionListResponse,
    TransactionUploadResponse,
)
from app.services.transactions import get_transactions
from app.services.user_service import ActiveUser
from core.dependecies import DBSession
from core.logger import logger


router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("", response_model=TransactionListResponse, status_code=status.HTTP_200_OK)
async def list_transactions(
    current_user: ActiveUser,
    db: DBSession,
    status: Optional[str] = Query(
        None, description="Filter by status: ongoing, completed, cancelled"
    ),
):
    data = await get_transactions(status, current_user, db)
    return TransactionListResponse(data=data)


@router.post(
    "/{bid_id}/upload-documents",
    response_model=TransactionUploadResponse,
    status_code=status.HTTP_200_OK,
)
async def upload_transaction_documents(
    bid_id: str,
    current_user: ActiveUser,
    db: DBSession,
    images: Annotated[List[UploadFile], File(...)],
    description: Annotated[Optional[str], Form()] = None,
):
    if not images:
        raise HTTPException(status_code=400, detail="No files provided")

    uploaded_urls: List[str] = []
    for upload in images:
        if not upload.filename:
            continue
        file_content = await upload.read()
        try:
            result = uploader.upload(
                file_content,
                public_id=f"transactions/{bid_id}/{upload.filename}",
                folder="transactions",
                overwrite=True,
            )
            uploaded_urls.append(result.get("secure_url"))
        except Exception as exc:
            logger.error(f"Transaction document upload failed: {exc}")
            raise HTTPException(
                status_code=500, detail="Failed to upload transaction document"
            ) from exc

    if not uploaded_urls:
        raise HTTPException(status_code=400, detail="No valid files uploaded")

    return TransactionUploadResponse(
        uploaded_urls=uploaded_urls, description=description
    )
