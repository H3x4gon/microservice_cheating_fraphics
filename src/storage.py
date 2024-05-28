from minio import Minio
from src.config import config

client = Minio(
	endpoint=config.minio_endpoint,
	access_key=config.minio_access_key,
	secret_key=config.minio_secret_key,
	secure=config.minio_ssl
)
