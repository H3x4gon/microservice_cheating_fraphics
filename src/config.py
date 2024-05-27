from functools import lru_cache
from pydantic import BaseModel
import json


class MinioConfig(BaseModel):
	endpoint: str
	access_key: str
	secret_key: str
	secure: bool
	global_bucket_name: str

class KeycloakConfig(BaseModel):
	server_url: str
	realm: str
	client_id: str
	client_secret: str
	authorization_url: str
	token_url: str

class DBConfig(BaseModel):
	host: str
	port: str
	name: str
	user: str
	password: str


class CConfig(BaseModel):
	logging_level: str
	db: DBConfig
	minio: MinioConfig
	keycloak: KeycloakConfig

	@classmethod
	def from_json(cls, filepath: str):
		with open(filepath, 'r') as f:
			config_data = json.load(f)
		return cls(**config_data)


# Загрузка настроек из JSON файла
config = CConfig.from_json("config.json")

@lru_cache()
def get_config():
	return config
