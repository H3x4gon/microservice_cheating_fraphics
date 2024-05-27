from models.db_models import SQLImage, SQLDocumentVersion, SQLDocument, SQLReport, SQLCheckpoint, SQLSubject, \
	SQLStudent, SQLUser

from src.storage import client, global_bucket_name
from schemas.schemas import CImageSet

from uuid import UUID, uuid4
from storage import client, global_bucket_name

from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select

from io import BytesIO

import logging

class NoImagesFoundError(Exception):
	pass


class CRepositoryServiceCheating:

	logger = logging.getLogger("ServiceCheating")

	@classmethod
	# Выгрузка файла с MinIO
	async def pull_file(
			cls,
			document_version: UUID
	):
		document_name = str(document_version)

		file_path = f"documents/{document_name}.docx"

		# Загружаем файл
		response = client.get_object(global_bucket_name, file_path)

		# Считываем все данные из потока в формате BytesIO
		file_data = BytesIO(response.read())

		return file_data

	@classmethod
	# Выгрузка метаданных о картинках по заданной версии документа
	async def pull_images_metadata(
			cls,
			document_version: UUID,
			async_session: AsyncSession
	):
		async with async_session.begin():
			# Получаем существующие записи изображений для данной версии документа
			result = await async_session.execute(
				select(SQLImage).
				where(SQLImage.document_ver_id == document_version)
			)
			existing_images = result.scalars().all()

		return list(existing_images)

	@classmethod
	async def pull_all_other_user_images_metadata(cls,
	                                              document_version_id: UUID,
	                                              async_session: AsyncSession
	                                              ):
		async with async_session.begin():
			# Получаем пользователя по версии документа
			result = await async_session.execute(
				select(SQLUser)
				.join(SQLStudent)
				.join(SQLReport)
				.join(SQLDocument)
				.join(SQLDocumentVersion)
				.where(SQLDocumentVersion.id == document_version_id)
				.options(joinedload(SQLUser.student)
				         .joinedload(SQLStudent.reports)
				         .joinedload(SQLReport.documents)
				         .joinedload(SQLDocument.versions))
			)
			user = result.scalars().first()

			if not user:
				return []

			# Получаем все изображения, загруженные другими пользователями
			result = await async_session.execute(
				select(SQLImage)
				.join(SQLDocumentVersion)
				.join(SQLDocument)
				.join(SQLReport)
				.join(SQLStudent)
				.join(SQLUser)
				.where(SQLUser.id != user.id)
				.options(joinedload(SQLImage.document_version)
				         .joinedload(SQLDocumentVersion.document)
				         .joinedload(SQLDocument.report))
			)
			images = result.scalars().all()

		return list(images)

	@classmethod
	async def upload(
			cls,
			async_session: AsyncSession,
			document_version: UUID,
			incoming_image_set: CImageSet
	):
		async with async_session.begin():
			try:
				image_uuid_map = {}
				for rel_id, Image in incoming_image_set.images.items():
					CImageTODB = SQLImage(
						id=uuid4(),
						document_ver_id=document_version,
						rel_id=Image.relationship_id,
						hash=Image.hash,
						size=Image.size
					)
					async_session.add(CImageTODB)
					image_uuid_map[rel_id] = str(CImageTODB.id)

				# Если запись в базу данных прошла успешно, пытаемся сохранить файлы в MinIO
				document_name = str(document_version)
				file_path = f"images/{document_name}/"
				ext = ".png"

				for rel_id, Image in incoming_image_set.images.items():
					try:
						next_uuid = image_uuid_map[rel_id]
						file_name = file_path + next_uuid + ext
						client.put_object(global_bucket_name, file_name, BytesIO(Image.data),
						                  len(Image.data))
					except Exception as e:
						# Если загрузка в MinIO не удалась, откатываем транзакцию
						print(f"Ошибка загрузки изображения в MinIO: {e}")
						raise

				# Если все файлы успешно загружены в MinIO, коммитим транзакцию
				await async_session.commit()
			except Exception as e:
				await async_session.rollback()
				raise Exception(f"Произошла ошибка: {e}")

	@classmethod
	async def update(
			cls,
			async_session: AsyncSession,
			document_version: UUID,
			incoming_image_set: CImageSet
	):
		async with async_session.begin():
			try:
				# Получаем существующие записи изображений для данной версии документа
				result = await async_session.execute(
					select(SQLImage).
					where(SQLImage.document_ver_id == document_version)
				)
				existing_images = result.scalars().all()

				# Удаляем существующие записи изображений из базы данных
				for image in existing_images:
					await async_session.delete(image)

				# Добавляем новые записи изображений в базу данных
				image_uuid_map = {}
				for rel_id, Image in incoming_image_set.images.items():
					CImageTODB = SQLImage(
						id=uuid4(),
						document_ver_id=document_version,
						rel_id=Image.relationship_id,
						hash=Image.hash,
						size=Image.size
					)
					async_session.add(CImageTODB)
					image_uuid_map[rel_id] = str(CImageTODB.id)

				# Если запись в базу данных прошла успешно, пытаемся сохранить файлы в MinIO
				document_name = str(document_version)
				file_path = f"images/{document_name}/"
				ext = ".png"

				# Удаляем старые изображения из MinIO
				for image in existing_images:
					file_name = file_path + str(image.id) + ext
					client.remove_object(global_bucket_name, file_name)

				# Загрузка новых изображений в MinIO
				for rel_id, Image in incoming_image_set.images.items():
					try:
						next_uuid = image_uuid_map[rel_id]
						file_name = file_path + next_uuid + ext
						client.put_object(global_bucket_name, file_name, BytesIO(Image.data),
						                  len(Image.data))
					except Exception as e:
						# Если загрузка в MinIO не удалась, откатываем транзакцию
						print(f"Ошибка загрузки изображения в MinIO: {e}")
						raise

				# Если все файлы успешно загружены в MinIO, коммитим транзакцию
				await async_session.commit()
			except Exception as e:
				await async_session.rollback()
				raise Exception(f"Произошла ошибка: {e}")

	@classmethod
	async def delete(
			cls,
			async_session: AsyncSession,
			document_version: UUID
	):
		async with async_session.begin():
			try:
				# Получаем существующие записи изображений для данной версии документа
				result = await async_session.execute(
					select(SQLImage).
					where(SQLImage.document_ver_id == document_version)
				)
				existing_images = result.scalars().all()

				# Удаляем записи изображений из базы данных
				for image in existing_images:
					await async_session.delete(image)

				# Если удаление из бд прошло успешно, пытаемся удалить файлы из MinIO
				document_name = str(document_version)
				file_path = f"images/{document_name}/"
				ext = ".png"

				for image in existing_images:
					try:
						file_name = file_path + str(image.id) + ext
						client.remove_object(global_bucket_name, file_name)
					except Exception as e:
						print(f"Ошибка удаления изображения из MinIO: {e}")
						raise

				# Если все файлы успешно удалены из MinIO, коммитим транзакцию
				await async_session.commit()
			except Exception as e:
				await async_session.rollback()
				raise Exception(f"Произошла ошибка: {e}")
