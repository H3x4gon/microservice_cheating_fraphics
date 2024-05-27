from fastapi import UploadFile, File, Query, HTTPException
from fastapi.responses import JSONResponse
from io import BytesIO

from .ImageHandling import extract_images_from_docx, compare_image_sets
from src.repositories.CRepositoryServiceCheating import CRepositoryServiceCheating
from fastapi.encoders import jsonable_encoder
from uuid import UUID
from minio.error import S3Error
from src.storage import client, global_bucket_name

from schemas.schemas import CImage, CImageSet

class CServiceCheating:

	@classmethod
	async def check_images_for_uniqueness(cls,
	                                      document_version: UUID,
	                                      async_session,
	                                      method: str = Query(...)):

		try:
			suspect_metadata = await CRepositoryServiceCheating.pull_images_metadata(
				document_version,
				async_session
			)

			suspect_image_set = CImageSet()
			for SQLImage in suspect_metadata:
				suspect_image = CImage.from_orm(SQLImage)
				suspect_image_set.images[document_version] = suspect_image
			
			reference_metadata = await CRepositoryServiceCheating.pull_all_other_user_images_metadata(
				document_version,
				async_session
			)

			reference_image_set = CImageSet()
			for SQLImage in reference_metadata:
				reference_image = CImage.from_orm(SQLImage)
				reference_image_set.images[document_version] = reference_image
			
			result_image_set = compare_image_sets(suspect_image_set, reference_image_set, method)
			
			return result_image_set.json_compatible()
			
		except Exception as e:
			raise e

	@classmethod
	async def upload_images_to_global_bucket(cls,
	                                         document_version: UUID,
	                                         async_session
	                                         ):
		try:
			file_data = await CRepositoryServiceCheating.pull_file(
				document_version
			)

			incoming_image_set = extract_images_from_docx(file_data)
			
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
	async def delete_images_from_global_bucket(cls,
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
