from fastapi import APIRouter, UploadFile, File, Query, Depends
from enum import Enum
from uuid import UUID
from services.CServiceCheating import CServiceCheating
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_session
from fastapi.responses import JSONResponse

router = (APIRouter
	(
	tags=["ServiceCheating"],
	responses={404: {"description": "Not found"}}
))


class ComparisonMethod(str, Enum):
	pixel_by_pixel = "Pixel-by-pixel comparison method"
	size_of_images = "Sizeof comparison method"


@router.post("/check_images_for_uniqueness")
async def m_check_images_for_uniqueness(document_version: UUID,
                                        async_session: AsyncSession = Depends(get_session),
                                        method: ComparisonMethod = Query(...)
                                        ):
	try:
		comparison_result = await CServiceCheating.check_images_for_uniqueness(
			document_version,
			async_session,
			method.value
		)
		return JSONResponse(content={"result": comparison_result})
	except Exception as e:
		return JSONResponse(content={"message": str(e)}, status_code=400)


@router.post("/upload_images_to_global_bucket")
async def m_upload_images_to_global_bucket(document_version: UUID,
                                           async_session: AsyncSession = Depends(get_session),
                                           ):
	try:
		await CServiceCheating.upload_images_to_global_bucket(
			document_version,
			async_session
		)
		return JSONResponse(content={"message": f"Изображения файла с UUID={str(document_version)} успешно загружены"})
	except Exception as e:
		return JSONResponse(content={"error_message": str(e)}, status_code=400)


@router.delete("/delete_images_from_global_bucket")
async def m_delete_images_from_global_bucket(document_version: UUID,
                                             async_session: AsyncSession = Depends(get_session)
                                             ):
	try:
		await CServiceCheating.delete_images_from_global_bucket(
			document_version,
			async_session
		)
		return JSONResponse(content={"message": f"Изображения файла с UUID={str(document_version)} успешно удалены"})
	except Exception as e:
		return JSONResponse(content={"error_message": str(e)}, status_code=400)
