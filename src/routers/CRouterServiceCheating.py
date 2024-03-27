from fastapi import APIRouter, UploadFile, File, Query
from enum import Enum

from services.CServiceCheating import (upload_file_to_global_bucket, delete_file_from_global_bucket,
									   get_images_from_stored_file, check_images_for_uniqueness,
									   create_global_bucket, clear_global_bucket, rename_global_bucket,
									   delete_global_bucket
									   )
from typing import List

router = (APIRouter
	(
	tags=["ServiceCheating"],
	responses={404: {"description": "Not found"}}
))


class ComparisonMethod(str, Enum):
	pixel_by_pixel = "Pixel-by-pixel comparison method"
	size_of_images = "Sizeof comparison method"


@router.get("/get_images_from_stored_file")
async def m_get_images_from_stored_file(checkpoint_id: str,
										file_id: str,
										version: str,
										filename: str):
	return await get_images_from_stored_file(checkpoint_id, file_id, version, filename)


@router.post("/check_images_for_uniqueness")
def m_check_images_for_uniqueness(checkpoint_id: str,
								  file_id: str,
								  version: str,
								  file: UploadFile = File(...),
								  method: ComparisonMethod = Query(...)):
	return check_images_for_uniqueness(checkpoint_id, file_id, version, file, method.value)


@router.post("/upload_file_to_global_bucket")
async def m_upload_file_to_global_bucket(checkpoint_id: str,
										 file_id: str,
										 version: str,
										 file: UploadFile = File(...)):
	return await upload_file_to_global_bucket(checkpoint_id, file_id, version, file)


@router.post("/create_global_bucket")
def m_create_global_bucket():
	return create_global_bucket()


@router.put("/rename_global_bucket")
def m_rename_global_bucket(new_global_bucket_name: str):
	return rename_global_bucket(new_global_bucket_name)


@router.delete("/delete_file_from_global_bucket")
def m_delete_file_from_global_bucket(checkpoint_id: str, file_id: str, version: str, file_name: str):
	return delete_file_from_global_bucket(checkpoint_id, file_id, version, file_name)


@router.delete("/clear_global_bucket")
def m_clear_global_bucket():
	return clear_global_bucket()
