from typing import Annotated

from uuid import UUID

from fastapi import Query
from pydantic import Field

from .CServiceImages import extract_images_from_docx, compare_image_sets
from src.repositories.CRepositoryServiceCheating import CRepositoryServiceCheating, NoImagesFoundError

from src.schemas.schemas import CImage, CImageSet


class CServiceCheating:

	@classmethod
	async def check_images_for_uniqueness(
		cls,
		document_version: UUID,
		async_session,
		method: str,
		threshold: Annotated[int, Field(ge=1, le=100)],
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

			# Преобразуем пороговое значение в диапазон от 0 до 1
			normalized_threshold = threshold / 100.0

			# Сравниваем наборы изображений
			result_image_set = compare_image_sets(suspect_image_set, reference_image_set, method)
			temp_image_set = result_image_set.copy()

			total_image_count = sum(len(image_list) for image_list in result_image_set.images.values())
			justified_image_count = 0

			for images in result_image_set.images.values():
				for image in images:
					if image.max_similarity is None or image.max_similarity < normalized_threshold:
						justified_image_count += 1

			# Фильтруем список изображений
			for key in temp_image_set.images:
				temp_image_set.images[key] = [
					image for image in temp_image_set.images[key]
					if image.max_similarity is not None and image.max_similarity >= normalized_threshold
				]

			originality_score = (justified_image_count * 100) / total_image_count if total_image_count > 0 else None

			if originality_score is not None:
				originality_score = round(originality_score, 2)

			return {
				"result_image_set": temp_image_set.json_compatible(),
				"originality_score": originality_score
			}

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
