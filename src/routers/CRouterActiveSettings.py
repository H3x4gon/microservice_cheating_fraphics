from fastapi import APIRouter
from fastapi import Depends
from src.config import CConfig, get_config

router = APIRouter(
    prefix="/config",
    tags=["config"],
    responses={404: {"description": "Not found"}}
)

@router.get("/")
async def about(config: CConfig = Depends(get_config)):
    return {
        "db_host": config.db_host,
        "db_name": config.db_name,
        "minio_url": config.minio_endpoint,
        "minio_bucket": config.minio_global_bucket_name
    }
