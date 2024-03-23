from fastapi import UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from minio import Minio
from minio.commonconfig import CopySource
from minio.error import S3Error
from typing import List
from io import BytesIO
from .ImageHandling import extract_images_from_docx, calc_image_set_hashes, CMinioImageSets, \
	CImageSet, CImage
from fastapi.encoders import jsonable_encoder

# Инициализация клиента Minio
client = Minio(
	endpoint="play.min.io",
	access_key="Q3AM3UQ867SPQQA43P2F",
	secret_key="zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG",
	secure=True
)


def upload_docx_and_extract_images(file: UploadFile = File(...)):
	if not file.filename.endswith('.docx'):
		raise HTTPException(status_code=400, detail="Неподдерживаемый тип файла.")

	try:
		# Извлекаем только изображения из docx-файла и добавляем их в CImageSet
		image_set = extract_images_from_docx(file.file)

		# Вычисляем хеш для каждого изображения
		calc_image_set_hashes(image_set)

		# Создаем бакет в Minio, если его нет
		bucket_name = "proverka"

		client.make_bucket(bucket_name)

		# Загружаем преобразованные изображения в Minio
		for image_filename, image_data in image_set.images.items():
			client.put_object(bucket_name, image_filename, BytesIO(image_data.data), len(image_data.data))

		json_data = image_set.json_compatible()

		return JSONResponse(content=json_data)

	except Exception as e:
		error_detail = str(e)
		return JSONResponse(status_code=500, content={"message": error_detail})


def clear_bucket(bucket_name):
	try:
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

def delete_bucket(bucket_name):
    try:
        # Проверяем существование бакета
        if client.bucket_exists(bucket_name):
            # Получаем список объектов в бакете
            objects_to_delete = client.list_objects(bucket_name, recursive=True)

            # Удаляем объекты из бакета
            for obj in objects_to_delete:
                client.remove_object(bucket_name, obj.object_name)

            # Удаляем сам бакет
            client.remove_bucket(bucket_name)

            # Возвращаем сообщение об успешном удалении бакета
            return {"message": f"Бакет {bucket_name} и все его содержимое успешно удалены"}

        else:
            # Бакет не существует, возвращаем соответствующее сообщение
            return {"message": f"Бакет {bucket_name} не существует"}

    except S3Error as e:
        # Возвращаем сообщение об ошибке от S3
        return {"error": f"Ошибка S3: {e}"}
    except Exception as e:
        # Возвращаем сообщение о любой другой ошибке
        return {"error": f"Ошибка при удалении бакета: {e}"}

def delete_image_from_bucket(bucket_name, file_name):
	try:
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


def rename_bucket(old_bucket_name, new_bucket_name):
	try:
		# Проверяем существование старого бакета
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
