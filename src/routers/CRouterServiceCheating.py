from fastapi import APIRouter, UploadFile, File
from services.CServiceCheating import (upload_file_to_global_bucket, create_global_bucket, clear_global_bucket,
                                     delete_file_from_global_bucket, get_images_from_stored_file, rename_global_bucket,
                                       delete_global_bucket)
from typing import List

router = (APIRouter
(
    tags=["ServiceCheating"],
    responses={404: {"description": "Not found"}}
))

@router.get("/get_images_from_stored_file")
def m_get_images_from_stored_file(checkpoint_id: str,
								  file_id: str,
								  version: str,
								  filename: str):
    return get_images_from_stored_file(checkpoint_id, file_id, version, filename)
@router.get("/check_images_for_uniqueness")
def m_check_images_for_uniqueness(checkpoint_id: str,
								  file_id: str,
								  version: str,
								  file: UploadFile = File(...)):
	return check_images_for_uniqueness(checkpoint_id, file_id, version, file)
@router.post("/create_global_bucket")
def m_create_global_bucket():
    return create_global_bucket()
@router.post("/upload_file_to_global_bucket")
def m_upload_file_to_global_bucket(checkpoint_id: str,
                                   file_id: str,
                                   version: str,
                                   file: UploadFile = File(...)):
    return upload_file_to_global_bucket(checkpoint_id, file_id, version, file)
@router.put("/rename_global_bucket")
def m_rename_global_bucket(new_global_bucket_name: str):
    return rename_global_bucket(new_global_bucket_name)
@router.put("/clear_global_bucket")
def m_clear_global_bucket():
    return clear_global_bucket()
@router.delete("/delete_global_bucket")
def m_delete_global_bucket():
    return delete_global_bucket()
@router.delete("/delete_file_from_global_bucket")
def m_delete_file_from_global_bucket(checkpoint_id: str, file_id: str, version: str, file_name: str):
    return delete_file_from_global_bucket(checkpoint_id, file_id, version, file_name)
