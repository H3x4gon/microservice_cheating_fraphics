from fastapi import APIRouter, UploadFile, File
from services.CServiceModels import (upload_docx_and_extract_images, clear_bucket,
                                     delete_image_from_bucket, get_imageset, rename_bucket, delete_bucket)
from typing import List

router = (APIRouter
(
    prefix="/models",
    tags=["models"],
    responses={404: {"description": "Not found"}}
))

@router.get("/about")
def about():
    return "Здесь собраны методы для извлечения изображений из docx файла"


@router.get("/get_imageset")
def m_get_imageset(bucket_name: str):
    return get_imageset(bucket_name)

@router.put("/rename_bucket")
def m_rename_bucket(bucket_name: str, new_bucket_name: str):
    return rename_bucket(bucket_name, new_bucket_name)
@router.post("/upload_docx_and_extract_images")
def m_upload_docx_and_extract_images(file: UploadFile = File(...)):
    return upload_docx_and_extract_images(file)

@router.delete("/delete_bucket")
def m_delete_bucket(bucket_name: str):
    return delete_bucket(bucket_name)
@router.delete("/delete_imageset")
def m_delete_imageset(bucket_name: str):
    return clear_bucket(bucket_name)

@router.delete("/delete_image_from_bucket")
def m_delete_image_from_bucket(bucket_name: str, image_name: str):
    return delete_image_from_bucket(bucket_name, image_name)
