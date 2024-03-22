from fastapi import APIRouter, UploadFile, File
from src.services.CServiceModels import upload_file, delete_imageset, delete_image_from_repos, get_imageset, rename_repos

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
def m_get_imageset(repos_name: str):
    return get_imageset(repos_name)

@router.put("/rename_repos")
def m_rename_repos(repos_name: str, new_repos_name: str):
    return rename_repos(repos_name, new_repos_name)
@router.post("/upload_file")
def m_extract_images(file: UploadFile = File(...)):
    return upload_file(file)

@router.delete("/delete_imageset")
def m_delete_imageset(repos_name: str):
    return delete_imageset(repos_name)

@router.delete("/delete_image_from_repos")
def m_delete_image_from_repos(repos_name: str, image_name: str):
    return delete_image_from_repos(repos_name, image_name)
