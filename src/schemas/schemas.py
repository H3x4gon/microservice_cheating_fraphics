from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List, Dict
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
		return jsonable_encoder({
			"img_id": self.id,
			"filename": self.filename,
			"rel_id": self.rel_id,
			"max_similarity": self.max_similarity,
			"img_path_with_max_similarity": self.img_path_with_max_similarity
		})


class CImageSet(BaseModel):
	images: Dict[UUID, List[CImage]] = {}

	def json_compatible(self):
		# Преобразуем каждый объект CImage в JSON-совместимый формат
		images_json_compatible = {
			str(key) + ".docx": [image.json_compatible() for image in value]
			for key, value in self.images.items()
		}
		return jsonable_encoder(
			images_json_compatible
		)
