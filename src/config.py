from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class CConfig(BaseSettings):
	logging_level: str = "INFO"

	minio_endpoint: str = "play.min.io"
	minio_access_key: str = "access_key"
	minio_secret_key: str = "secret_key"
	minio_ssl: bool = True
	minio_bucket_name: str = "bucket"

	db_host: str = "localhost"
	db_port: int = 5432
	db_name: str = "database"
	db_user: str = "postgres"
	db_password: str = "12345"

	model_config = SettingsConfigDict(env_file=".env")


config = CConfig()


@lru_cache()
def get_config():
	return config
