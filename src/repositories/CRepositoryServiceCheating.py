import logging
from io import BytesIO
from uuid import UUID, uuid4

from sqlalchemy import delete
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.storage import client
from src.models.db_models import SQLImage, SQLDocumentVersion, SQLDocument, SQLReport, \
	SQLStudent, SQLUser
from src.schemas.schemas import CImageSet

from src.config import config

logger = logging.getLogger("ServiceCheatingGraphics")


class NoImagesFoundError(Exception):
	pass


class CRepositoryServiceCheating:

	@classmethod
	# Выгрузка файла с MinIO
	async def pull_file(
			cls,
			document_version: UUID
	):
		document_name = str(document_version)

		file_path = f"documents/{document_name}.docx"

		# Загружаем файл
		response = client.get_object(config.minio_bucket_name, file_path)

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
		# async with async_session.begin():
		# Получаем существующие записи изображений для данной версии документа
		result = await async_session.execute(
			select(SQLImage).
			where(SQLImage.document_ver_id == document_version)
		)
		existing_images = result.scalars().all()

		return list(existing_images)

	@classmethod
	async def pull_all_other_user_images_metadata(
			cls,
			document_version_id: UUID,
			async_session: AsyncSession
	):
		# Получаем пользователя по версии документа
		result = await async_session.execute(
			select(SQLUser)
			.join(SQLStudent)
			.join(SQLReport)
			.join(SQLDocument)
			.join(SQLDocumentVersion)
			.where(SQLDocumentVersion.id == document_version_id)
			.options(
				joinedload(SQLUser.student)
				.joinedload(SQLStudent.reports)
				.joinedload(SQLReport.documents)
				.joinedload(SQLDocument.versions)
			)
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
			.options(
				joinedload(SQLImage.document_version)
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
				# Проверяем, существуют ли записи о картинках для данного отчета
				stmt = select(SQLImage).where(SQLImage.document_ver_id == document_version)
				result = await async_session.execute(stmt)
				existing_images = result.scalars().all()

				# Если записи существуют, удаляем их и соответствующие файлы из MinIO
				if existing_images:
					for image in existing_images:
						file_name = f"images/{document_version}/{image.id}.png"
						try:
							client.remove_object(config.minio_bucket_name, file_name)
						except Exception as e:
							logger.exception(f"Ошибка удаления файла из MinIO: {e}")
							raise

					# Удаляем записи из базы данных
					delete_stmt = delete(SQLImage).where(SQLImage.document_ver_id == document_version)
					await async_session.execute(delete_stmt)

				# Добавляем новые записи в базу данных
				for image in incoming_image_set.images[document_version]:
					CImageTODB = SQLImage(
						id=uuid4(),
						document_ver_id=image.document_ver_id,
						rel_id=image.rel_id,
						hash=image.hash,
						size=image.size
					)
					async_session.add(CImageTODB)
					image.id = CImageTODB.id

				# Если запись в базу данных прошла успешно, пытаемся сохранить файлы в MinIO
				document_name = str(document_version)
				file_path = f"images/{document_name}/"
				ext = ".png"

				for image in incoming_image_set.images[document_version]:
					try:
						file_name = file_path + str(image.id) + ext
						client.put_object(
							config.minio_bucket_name,
							file_name,
							BytesIO(image.data),
							len(image.data)
						)
					except Exception as e:
						# Если загрузка в MinIO не удалась, откатываем транзакцию
						logger.exception(f"Ошибка загрузки изображения в MinIO: {e}")
						raise

				# Если все файлы успешно загружены в MinIO, коммитим транзакцию
				await async_session.commit()
			except Exception as e:
				await async_session.rollback()
				raise Exception(f"Произошла ошибка: {e}")

	@classmethod
	async def delete(cls, async_session: AsyncSession, document_version: UUID):
		async with async_session.begin():
			try:
				# Получаем существующие записи изображений для данной версии документа
				result = await async_session.execute(
					select(SQLImage).where(SQLImage.document_ver_id == document_version)
				)
				existing_images = result.scalars().all()

				# Удаляем записи изображений из базы данных
				for image in existing_images:
					await async_session.delete(image)

				# Если удаление из БД прошло успешно, пытаемся удалить файлы из MinIO
				document_name = str(document_version)
				file_path = f"images/{document_name}/"
				ext = ".png"

				for image in existing_images:
					try:
						file_name = file_path + str(image.id) + ext
						client.remove_object(config.minio_bucket_name, file_name)
					except Exception as e:
						logger.error(f"Ошибка удаления изображения из MinIO: {e}")
						raise

				# Если все файлы успешно удалены из MinIO, коммитим транзакцию
				await async_session.commit()
			except Exception as e:
				await async_session.rollback()
				logger.exception(f"Произошла ошибка при удалении: {e}")
				raise
