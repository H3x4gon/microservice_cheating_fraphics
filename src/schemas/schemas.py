from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from typing import Dict
from fastapi.encoders import jsonable_encoder


class CImage(BaseModel):
	id: Optional[UUID] = None
	document_ver_id: Optional[UUID] = None
	rel_id: Optional[str] = None
	filename: Optional[str] = None
	data: Optional[bytes] = None
	size: Optional[int] = None
	hash: Optional[str] = None
	max_similarity: Optional[float] = None
	img_path_with_max_similarity: Optional[str] = None

	class Config:
		from_attributes = True

	def json_compatible(self):
		# image_data_base64 = b64encode(self.data).decode('utf-8')
		return jsonable_encoder({
			"img_id": self.id,
			"filename": self.filename,
			"rel_id": self.rel_id,
			"max_similarity": self.max_similarity,
			"img_path_with_max_similarity": self.img_path_with_max_similarity
		})


class CImageSet(BaseModel):
	images: Dict[UUID, CImage] = {}

	def json_compatible(self):
		images_json_compatible = {document_ver_id: image.json_compatible() for document_ver_id, image in
		                          self.images.items()}
		return jsonable_encoder({
			"suspect_imageset": images_json_compatible
		})
