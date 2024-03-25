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

import json

# Загрузка конфигурации из файла
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

# Инициализация клиента Minio с использованием данных из конфигурационного файла
client = Minio(
    endpoint=config['minio']['endpoint'],
    access_key=config['minio']['access_key'],
    secret_key=config['minio']['secret_key'],
    secure=config['minio']['secure']
)

global_bucket_name = config['global_bucket']['name']
def create_global_bucket():
	try:
		# Проверяем, существует ли бакет, и если нет, то создаем его
		if not client.bucket_exists(global_bucket_name):
			client.make_bucket(global_bucket_name)
			return {"message": f"Хранилище '{global_bucket_name}' успешно создано."}
		else:
			return {"message": f"Хранилище '{global_bucket_name}' уже существует."}
	except Exception as e:
		error_detail = str(e)
		return JSONResponse(status_code=500, content={"message": error_detail})
def check_images_for_uniqueness(checkpoint_id: str, file_id: str, version: str, file: UploadFile = File(...)):
	if not file.filename.endswith('.docx'):
		raise HTTPException(status_code=400, detail="Неподдерживаемый тип файла.")

	try:
		# Извлекаем только изображения из docx-файла и добавляем их в CImageSet
		image_set = extract_images_from_docx(file.file)

		# Вычисляем хеш для каждого изображения
		calc_image_set_hashes(image_set)

		json_data = image_set.json_compatible()

		return JSONResponse(content=json_data)

	except Exception as e:
		error_detail = str(e)
		return JSONResponse(status_code=500, content={"message": error_detail})
def upload_file_to_global_bucket(checkpoint_id: str, file_id: str, version: str, file: UploadFile = File(...)):
    filename = file.filename
    try:
        # Формируем путь к файлу внутри бакета
        file_path = f"{checkpoint_id}/{file_id}/{version}/{filename}"

        # Проверяем существование бакета
        if not client.bucket_exists(global_bucket_name):
            client.make_bucket(global_bucket_name)

        file.file.seek(0)
        # Загружаем файл в бакет
        client.put_object(
            bucket_name=global_bucket_name,
            object_name=file_path,
            data=file.file,
            length=file.file.tell(),
            content_type=file.content_type
        )
        # Закрываем файл после загрузки
        file.file.close()
        return {"message": f"Файл {filename} успешно загружен в {file_path}"}

    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})
def clear_global_bucket():
	try:
		# Проверяем существование бакета
		if client.bucket_exists(global_bucket_name):
			# Получаем список объектов в бакете
			objects = client.list_objects(global_bucket_name)

			# Удаляем каждый объект из бакета
			for obj in objects:
				client.remove_object(global_bucket_name, obj.object_name)

			# Успешно очищаем бакет
			return {"message": f"Хранилище {global_bucket_name} успешно очищено"}

		else:
			return {"message": f"Хранилище {global_bucket_name} не существует"}

	except S3Error as e:
		return {"error": f"Ошибка Minio: {e}"}
	except Exception as e:
		return {"error": f"Ошибка при очистке бакета: {e}"}
def delete_global_bucket():
	try:
		if client.bucket_exists(global_bucket_name):
			# Получаем список объектов в бакете
			objects_to_delete = client.list_objects(global_bucket_name, recursive=True)

			# Удаляем объекты из бакета
			for obj in objects_to_delete:
				client.remove_object(global_bucket_name, obj.object_name)

			# Удаляем сам бакет
			client.remove_bucket(global_bucket_name)

			# Возвращаем сообщение об успешном удалении бакета
			return {"message": f"Бакет {global_bucket_name} и все его содержимое успешно удалены"}

		else:
			# Бакет не существует, возвращаем соответствующее сообщение
			return {"message": f"Бакет {global_bucket_name} не существует"}

	except S3Error as e:
		# Возвращаем сообщение об ошибке от S3
		return {"error": f"Ошибка S3: {e}"}
	except Exception as e:
		# Возвращаем сообщение о любой другой ошибке
		return {"error": f"Ошибка при удалении бакета: {e}"}
def delete_file_from_global_bucket(checkpoint_id: str, file_id: str, version: str, file_name: str):
	try:
		# Формируем путь к файлу внутри бакета
		file_path = f"{checkpoint_id}/{file_id}/{version}/{file_name}"

		# Проверяем существование бакета
		if not client.bucket_exists(global_bucket_name):
			return {"message": f"Бакет {global_bucket_name} не существует"}

		client.stat_object(
			bucket_name=global_bucket_name,
			object_name=file_path
		)

		# Если файл существует, то удаляем его
		client.remove_object(
			bucket_name=global_bucket_name,
			object_name=file_path
		)

		# Успешно удаляем файл
		return {"message": f"Файл {file_name} успешно удален из бакета {global_bucket_name}"}

	except S3Error as e:
		return {"error": f"Ошибка Minio: {e}"}
	except Exception as e:
		return {"error": f"Ошибка при удалении файла из бакета: {e}"}
def update_config_file(config_file_path, new_global_bucket_name):
	try:
		# Читаем текущие конфигурации из файла
		with open(config_file_path, 'r') as file:
			config = json.load(file)

		# Обновляем имя бакета
		config['global_bucket']['name'] = new_global_bucket_name

		# Пишем обновленные конфигурации обратно в файл
		with open(config_file_path, 'w') as file:
			json.dump(config, file, indent=4)

		print(f"Конфигурационный файл {config_file_path} был успешно обновлен.")
	except Exception as e:
		print(f"Ошибка при обновлении конфигурационного файла: {e}")
def rename_global_bucket(new_global_bucket_name):
	try:
		# Проверяем существование старого бакета
		if not client.bucket_exists(global_bucket_name):
			return {"error": f"Бакет {global_bucket_name} не существует"}

		# Проверяем, существует ли уже бакет с новым именем
		if not client.bucket_exists(new_global_bucket_name):
			# Создаем новый бакет
			client.make_bucket(new_global_bucket_name)
		else:
			return {"error": f"Бакет {new_global_bucket_name} уже существует"}

		# Копируем все объекты из старого бакета в новый
		objects = client.list_objects(global_bucket_name)
		for obj in objects:
			source = CopySource(bucket_name, obj.object_name)
			client.copy_object(new_global_bucket_name, obj.object_name, source)

		# Удаляем старый бакет, очищая его от объектов
		for obj in objects:
			client.remove_object(global_bucket_name, obj.object_name)
		client.remove_bucket(global_bucket_name)

		# Обновляем название глобального бакета на новое
		global_bucket_name = new_global_bucket_name

		update_config_file('config.json', new_global_bucket_name)

		return {"message": f"Бакет {global_bucket_name} успешно переименован в {new_global_bucket_name}"}

	except S3Error as e:
		return {"error": f"Ошибка Minio: {e}"}
	except Exception as e:
		return {"error": f"Ошибка при переименовании бакета: {e}"}
def get_images_from_stored_file(checkpoint_id: str, file_id: str, version: str, filename: str):
	try:
		# Формируем путь к файлу внутри бакета
		file_path = f"{checkpoint_id}/{file_id}/{version}/{filename}"

		# Проверяем существование бакета
		if not client.bucket_exists(global_bucket_name):
			return {"message": f"Бакет {global_bucket_name} не существует"}

		# Проверяем существование файла в бакете
		if not client.stat_object(global_bucket_name, file_path):
			return {"message": f"Файл {filename} не найден в папке {file_path}"}

		# Загружаем файл
		response = client.get_object(global_bucket_name, file_path)

		# Считываем все данные из потока в формате BytesIO
		file_data = File(fileobj=response.read(), filename=filename, content_type="application/zip")

		images = extract_images_from_docx(file_data)

		# Не забудьте закрыть поток, когда он больше не нужен
		response.close()
		response.release_conn()

		# Возвращаем извлеченные изображения
		return {f"{file_id}_{version}": images}

	except S3Error as e:
		return {"error": f"Ошибка Minio: {e}"}
	except Exception as e:
		return {"error": f"Ошибка при получении изображений из файла: {e}"}
