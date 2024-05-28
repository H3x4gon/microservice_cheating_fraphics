from fastapi import APIRouter, UploadFile, File, Query, Depends
from enum import Enum
from uuid import UUID

from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from fastapi.responses import JSONResponse
from src.database import get_session
from src.services.CServiceCheating import CServiceCheating

import logging

router = (
	APIRouter(
		tags=["ServiceCheatingGraphics"],
		responses={404: {"description": "Not found"}}
	)
)


class ComparisonMethod(str, Enum):
	aHash = "AvgHash comparison method"  # сравнение хеш функций по среднему (aHash)
	# (в тестах которые я проводил, показал себя хорошо, для требуемых задач думаю хватит и его)
	sizeof_images = "Sizeof comparison method"  # сравнение по размеру


# dct_phash = "DCT-pHash comparison method" возможно добавлю в будущем вычисление перцептивного хеша на основе
# дискретного косинусного преобразования (DCT) (он более устойчив к поворотам, шуму и изменению яркости, но
# в исследованиях в тестах медленнее примерно в 7-8 раз)
#
# dhash = "dHash comparison method" также возможно добавлю в будущем вычисление перцептивного хеша на основе
# функции расстояния (он по идее самый оптимальный по соотношению время/результат, он чуть медленнее aHash)

logger = logging.getLogger("ServiceCheatingGraphics")


@router.post("/check")
async def m_check_images_for_uniqueness(
	document_version: UUID,
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
		logger.exception(e)
		return JSONResponse(content={"message": str(e)}, status_code=400)


@router.post("/")
async def m_upload_images_to_global_bucket(
	document_version: UUID,
	async_session: AsyncSession = Depends(get_session),
):
	try:
		await CServiceCheating.upload_images_to_global_bucket(
			document_version,
			async_session
		)
		return JSONResponse(content={"message": f"Изображения файла с UUID={str(document_version)} успешно загружены"})
	except Exception as e:
		logger.exception(e)
		return JSONResponse(content={"error_message": str(e)}, status_code=400)

@router.post("/create")
async def m_create_global_bucket():
	try:
		await CServiceCheating.create_global_bucket()
		return JSONResponse(content={"message": f"Корзина успешно создана"})
	except Exception as e:
		logger.exception(e)
		return JSONResponse(content={"error_message": str(e)}, status_code=400)

@router.delete("/")
async def m_delete_images_from_global_bucket(
	document_version: UUID,
	async_session: AsyncSession = Depends(get_session)
):
	try:
		await CServiceCheating.delete_images_from_global_bucket(
			document_version,
			async_session
		)
		return JSONResponse(content={"message": f"Изображения файла с UUID={str(document_version)} успешно удалены"})
	except Exception as e:
		logger.exception(e)
		return JSONResponse(content={"error_message": str(e)}, status_code=400)
