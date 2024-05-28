from fastapi import Query
from uuid import UUID

from .CServiceImages import extract_images_from_docx, compare_image_sets
from src.repositories.CRepositoryServiceCheating import CRepositoryServiceCheating, NoImagesFoundError

from src.schemas.schemas import CImage, CImageSet


class CServiceCheating:

	@classmethod
	async def check_images_for_uniqueness(
		cls,
		document_version: UUID,
		async_session,
		method: str = Query(...)
	):

		try:
			# Получаем метаданные подозреваемых изображений
			suspect_metadata = await CRepositoryServiceCheating.pull_images_metadata(
				document_version,
				async_session
			)

			# Создаем набор подозреваемых изображений
			suspect_image_set = CImageSet()
			for sql_image in suspect_metadata:
				suspect_image = CImage.from_orm(sql_image)
				if document_version not in suspect_image_set.images:
					suspect_image_set.images[document_version] = []
				suspect_image_set.images[document_version].append(suspect_image)

			# Получаем метаданные эталонных изображений
			reference_metadata = await CRepositoryServiceCheating.pull_all_other_user_images_metadata(
				document_version,
				async_session
			)

			# Создаем набор эталонных изображений
			reference_image_set = CImageSet()
			for sql_image in reference_metadata:
				reference_image = CImage.from_orm(sql_image)
				doc_ver_id = reference_image.document_ver_id
				if doc_ver_id not in reference_image_set.images:
					reference_image_set.images[doc_ver_id] = []
				reference_image_set.images[doc_ver_id].append(reference_image)

			# Сравниваем наборы изображений
			result_image_set = compare_image_sets(suspect_image_set, reference_image_set, method)

			return result_image_set.json_compatible()

		except Exception as e:
			raise e

	@classmethod
	async def create_global_bucket(
		cls,
	):
		try:
			await CRepositoryServiceCheating.create_global_bucket()
		except Exception as e:
			raise e

	@classmethod
	async def upload_images_to_global_bucket(
		cls,
		document_version: UUID,
		async_session
	):
		try:

			file_data = await CRepositoryServiceCheating.pull_file(
				document_version
			)

			incoming_image_set = extract_images_from_docx(file_data, document_version)

			if incoming_image_set == {}:
				raise NoImagesFoundError("В документе нет графических изображений")

			await CRepositoryServiceCheating.upload(
				async_session,
				document_version,
				incoming_image_set
			)
		except Exception as e:
			raise e

	@classmethod
	async def delete_images_from_global_bucket(
		cls,
		document_version: UUID,
		async_session
	):
		try:
			await CRepositoryServiceCheating.delete(
				async_session,
				document_version
			)

		except Exception as e:
			raise e
