from fastapi import APIRouter, UploadFile, File
from ..services.CServiceModels import my_sum, my_extract_images

router = APIRouter(
    prefix="/models",
    tags=["models"],
    responses={404: {"description": "Not found"}}
)

@router.get("/about")
def about():
    return "Здесь собраны методы для вызова моделей обработки данных"

@router.get("/sum")
def m_sum(x: float = 0, y: float = 0):
    return my_sum(x, y)

@router.post("/extract_images")
def m_extract_images(file):
    return my_extract_images(file)