import xml.etree.ElementTree as ET
import zipfile
import json
import cv2
import os

from PIL import Image
from io import BytesIO
from pydantic import BaseModel, Field
from fastapi.encoders import jsonable_encoder
from typing import Dict, Optional
from numpy import count_nonzero, array
from base64 import b64encode


class CImage(BaseModel):
	filename: Optional[str] = None
	data: Optional[bytes] = None  # предполагается, что это бинарные данные изображения
	size: Optional[int] = None
	hash: Optional[str] = None
	max_similarity: Optional[float] = None
	img_path_with_max_similarity: Optional[str] = None

	# Метод для преобразования экземпляра модели в JSON-совместимый словарь
	def json_compatible(self):
		# Кодируем байты в base64 для JSON-сериализации
		# image_data_base64 = b64encode(self.data).decode('utf-8')
		return jsonable_encoder({
			"filename": self.filename,
			#    "data": image_data_base64,
			"size": self.size,
			"hash": self.hash,
			"max_similarity": self.max_similarity,
			"img_path_with_max_similarity": self.img_path_with_max_similarity
		})


class CImageSet(BaseModel):
	images: Dict[str, CImage] = {}

	def json_compatible(self):
		# Получаем каждый CImage в JSON-совместимом формате
		images_json_compatible = {relationship_id: image.json_compatible() for relationship_id, image in
								  self.images.items()}
		return jsonable_encoder({
			"report_id": images_json_compatible
		})


class CReportsImageSets(BaseModel):
	reports: Dict[str, CImageSet]

	def json_compatible(self):
		# Получаем каждый CImageSet в JSON-совместимом формате
		reports_json_compatible = {file_path: report_images.json_compatible() for file_path, report_images in
								   self.reports.items()}
		return jsonable_encoder({
			reports.key: reports_json_compatible
		})


def extract_images_from_docx(file, file_path: str) -> CImageSet:
	# Создаем объект CImageSet
	image_set = CImageSet()
	with zipfile.ZipFile(file, "r") as zip_ref:
		# Читаем файл отношений и строим словарь
		rels_data = zip_ref.read('word/_rels/document.xml.rels')
		rels_root = ET.fromstring(rels_data)
		relationships = {
			rel.attrib['Id']: rel.attrib['Target'].split('/')[-1]
			for rel in
			rels_root.findall('.//{http://schemas.openxmlformats.org/package/2006/relationships}Relationship')
		}

		# Создаем обратный словарь для быстрого поиска ID отношения по имени файла
		filename_to_rel_id = {target: rel_id for rel_id, target in relationships.items()}

		# Извлекаем изображения
		for filename in zip_ref.namelist():
			if filename.startswith("word/media/") and filename.count("/") == 2:
				# Проверяем расширение файла
				if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
					img_data = zip_ref.read(filename)
					img_filename = os.path.basename(filename)

					# Получаем relationship_id для изображения
					relationship_id = filename_to_rel_id.get(img_filename)

					# Если у изображения есть relationship_id, создаем объект CImage и добавляем в CImageSet
					if relationship_id:
						image_set.images[relationship_id] = CImage(
							filename=img_filename,
							data=img_data,
							size=len(img_data),
							hash=None
						)

	return image_set


def compare_image_sets(incoming_image_set: CImageSet, stored_image_set: CImageSet, method: str) -> CImageSet:

	if method == "Pixel-by-pixel comparison method":
		for incoming_image_id, incoming_image in incoming_image_set.images.items():
			max_similarity = -1  # Начальное значение минимальной схожести
			img_path_with_min_similarity = None

			for stored_image_id, stored_image in stored_image_set.images.items():
				similarity = compare_hash(incoming_image.hash, stored_image.hash)
				normalized_similarity = 1 - (similarity / 64)  # Нормализуем сходство
				if normalized_similarity > max_similarity:
					max_similarity = normalized_similarity
					img_path_with_min_similarity = stored_image_id + "/" + stored_image.filename

			incoming_image.max_similarity = max_similarity
			incoming_image.img_path_with_max_similarity = img_path_with_min_similarity

	if method == "Sizeof comparison method":
		for incoming_image_id, incoming_image in incoming_image_set.images.items():

			for stored_image_id, stored_image in stored_image_set.images.items():
				if incoming_image.size == stored_image.size:
					# Если размеры изображений совпадают, считаем их идентичными
					img_path_with_min_similarity = stored_image_id + "/" + stored_image.filename
					incoming_image.max_similarity = 1
					incoming_image.img_path_with_max_similarity = img_path_with_min_similarity
					break  # Прерываем цикл, так как нашли совпадение по размеру

	return incoming_image_set


# Функция вычисления хэша
def calc_image_hash(image_obj: CImage) -> str:
	image = Image.open(BytesIO(image_obj.data))
	if image.mode == 'RGBA':
		image = image.convert('RGB')
	image_np = array(image)

	resized = cv2.resize(image_np, (8, 8), interpolation=cv2.INTER_AREA)
	gray_image = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
	_, threshold_image = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

	_hash = ""
	for i in range(8):
		for j in range(8):
			pixel_value = threshold_image[i, j]
			if pixel_value > gray_image.mean():
				_hash += "1"
			else:
				_hash += "0"

	return _hash


def calc_image_set_hashes(imageset_obj: CImageSet) -> None:
	for img_name, img_obj in imageset_obj.images.items():
		img_obj.hash = calc_image_hash(img_obj)


def compare_hash(hash1, hash2):
	return count_nonzero(array(list(hash1)) != array(list(hash2)))
