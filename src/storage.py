from minio import Minio
from src.config import config

client = Minio(
	endpoint=config.minio.endpoint,
	access_key=config.minio.access_key,
	secret_key=config.minio.secret_key,
	secure=config.minio.secure
)

global_bucket_name = config.minio.global_bucket_name
