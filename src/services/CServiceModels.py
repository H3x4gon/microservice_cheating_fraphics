from fastapi import UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from minio import Minio
from minio.commonconfig import CopySource
from minio.error import S3Error
import cv2
import os
import zipfile
import io
import numpy as np
from docx import Document
from io import BytesIO
from PIL import Image
from dataclasses import dataclass, field
from typing import Dict
@dataclass
class CImage:
	filename: str  # Имя файла изображения
	data: bytes  # Данные изображения в формате bytes
	hash: str  # Хешированные данные изображения


@dataclass
class CImageSet:
	images: Dict[str, CImage] = field(default_factory=dict)  # Словарь с изображениями и их метаданными

@dataclass
class MinioImageSets:
	repositories: Dict[str, CImageSet]  # Словарь для хранения CImageSet, где ключи - имена корзин MinIO


def upload_file(file: UploadFile = File(...)):
	if not file.filename.endswith('.docx'):
		raise HTTPException(status_code=400, detail="Неподдерживаемый тип файла.")

	try:
		# Создаем объект CImageSet
		image_set = CImageSet()

		# Извлекаем только изображения из docx-файла и добавляем их в CImageSet
		extract_images_from_docx(file.file, image_set)

		# Преобразуем извлеченные изображения в формат JPG и получаем новый CImageSet
		converted_images_set = convert_images_to_jpg(image_set)

		# Инициализируем клиента Minio
		client = Minio(
			endpoint="play.min.io",
			access_key="Q3AM3UQ867SPQQA43P2F",
			secret_key="zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG",
			secure=True
		)

		# Создаем бакет в Minio, если его нет
		bucket_name = "proverkaNew"  # Замените на ваше имя бакета

		client.make_bucket(bucket_name)

		# Загружаем преобразованные изображения в Minio
		for image_filename, image_data in converted_images_set.images.items():
			client.put_object(bucket_name, image_filename, io.BytesIO(image_data.data), len(image_data.data))

		return {"message": "Изображения успешно загружены в Minio"}

	except Exception as e:
		error_detail = str(e)
		return JSONResponse(status_code=500, content={"message": error_detail})


def delete_imageset(bucket_name):
	try:
		# Инициализируем клиента Minio
		client = Minio(
			endpoint="play.min.io",
			access_key="Q3AM3UQ867SPQQA43P2F",
			secret_key="zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG",
			secure=True
		)

		# Проверяем существование бакета
		if client.bucket_exists(bucket_name):
			# Получаем список объектов в бакете
			objects = client.list_objects(bucket_name)

			# Удаляем каждый объект из бакета
			for obj in objects:
				client.remove_object(bucket_name, obj.object_name)

			# Успешно очищаем бакет
			return {"message": f"Хранилище {bucket_name} успешно очищено"}

		else:
			return {"message": f"Хранилище {bucket_name} не существует"}

	except S3Error as e:
		return {"error": f"Ошибка Minio: {e}"}
	except Exception as e:
		return {"error": f"Ошибка при очистке бакета: {e}"}


def delete_image_from_repos(bucket_name, file_name):
	try:
		# Инициализируем клиента Minio
		client = Minio(
			endpoint="play.min.io",
			access_key="Q3AM3UQ867SPQQA43P2F",
			secret_key="zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG",
			secure=True
		)

		# Проверяем существование бакета
		if not client.bucket_exists(bucket_name):
			return {"message": f"Бакет {bucket_name} не существует"}

		# Удаляем файл из бакета
		client.remove_object(bucket_name, file_name)

		# Успешно удаляем файл
		return {"message": f"Файл {file_name} успешно удален из бакета {bucket_name}"}

	except S3Error as e:
		return {"error": f"Ошибка Minio: {e}"}
	except Exception as e:
		return {"error": f"Ошибка при удалении файла из бакета: {e}"}


def rename_repos(old_bucket_name, new_bucket_name):
	try:
		# Инициализируем клиента Minio
		client = Minio(
			endpoint="play.min.io",
			access_key="Q3AM3UQ867SPQQA43P2F",
			secret_key="zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG",
			secure=True
		)

		# Прове.0632
		# 59/*ряем существование старого бакета
		if not client.bucket_exists(old_bucket_name):
			return {"error": f"Бакет {old_bucket_name} не существует"}

		# Проверяем, существует ли уже бакет с новым именем
		if not client.bucket_exists(new_bucket_name):
			# Создаем новый бакет
			client.make_bucket(new_bucket_name)
		else:
			return {"error": f"Бакет {new_bucket_name} уже существует"}

		# Копируем все объекты из старого бакета в новый
		objects = client.list_objects(old_bucket_name)
		for obj in objects:
			source = CopySource(old_bucket_name, obj.object_name)
			client.copy_object(new_bucket_name, obj.object_name, source)

		# Удаляем старый бакет, очищая его от объектов
		for obj in objects:
			client.remove_object(old_bucket_name, obj.object_name)
		client.remove_bucket(old_bucket_name)

		return {"message": f"Бакет {old_bucket_name} успешно переименован в {new_bucket_name}"}

	except S3Error as e:
		return {"error": f"Ошибка Minio: {e}"}
	except Exception as e:
		return {"error": f"Ошибка при переименовании бакета: {e}"}


def get_imageset(bucket_name):
	try:
		# Инициализируем клиента Minio
		client = Minio(
			endpoint="play.min.io",
			access_key="Q3AM3UQ867SPQQA43P2F",
			secret_key="zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG",
			secure=True
		)

		# Проверяем существование бакета
		if not client.bucket_exists(bucket_name):
			return {"message": f"Бакет {bucket_name} не существует"}

		# Получаем список объектов (файлов) в бакете
		objects = client.list_objects(bucket_name)

		# Извлекаем названия файлов и добавляем их в список
		file_names = [obj.object_name for obj in objects]

		# Возвращаем список названий файлов
		return {"file_names": file_names}

	except S3Error as e:
		return {"error": f"Ошибка Minio: {e}"}
	except Exception as e:
		return {"error": f"Ошибка при получении списка файлов из бакета: {e}"}


def extract_images_from_docx(file, image_set: CImageSet):
	with zipfile.ZipFile(file, "r") as zip_ref:
		for filename in zip_ref.namelist():
			if filename.startswith("word/media/") and filename.count("/") == 2:
				img_data = zip_ref.read(filename)
				img_filename = os.path.basename(filename)
				image_set.images[img_filename] = CImage(filename=img_filename, data=img_data, hash=None)


def convert_images_to_jpg(image_set: CImageSet):
	converted_images = CImageSet()
	for img_filename, img_data in image_set.images.items():
		with Image.open(BytesIO(img_data.data)) as img:
			img = img.convert("RGB")
			output = BytesIO()
			img.save(output, format="JPEG")
			converted_images.images[os.path.splitext(img_filename)[0] + ".jpg"] = CImage(
				filename=os.path.splitext(img_filename)[0] + ".jpg",
				data=output.getvalue(),
				hash=None
			)
	return converted_images


# Функция вычисления хэша
def calc_image_hash(image_obj: CImage) -> str:
	image = Image.open(BytesIO(image_obj.data))

	resized = cv2.resize(image, (8, 8), interpolation=cv2.INTER_AREA)  # Изменение размера до 8x8
	gray_image = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)  # Перевод в черно-белый формат
	_, threshold_image = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)  # Бинаризация

	# Рассчет хеша
	_hash = ""
	for i in range(8):
		for j in range(8):
			pixel_value = threshold_image[i, j]
			if pixel_value > gray_image.mean():
				_hash += "1"
			else:
				_hash += "0"

	return _hash


def calc_image_set_hash(imageset_obj: CImageSet) -> None:
	for img_info in imageset_obj.images:
		img_info.hash = calc_image_hash(img_info)


def compare_hash(hash1, hash2):
	return np.count_nonzero(np.array(list(hash1)) != np.array(list(hash2)))
