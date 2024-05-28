import xml.etree.ElementTree as ET
import zipfile
import json
import cv2
import os

from PIL import Image
from io import BytesIO
from fastapi.encoders import jsonable_encoder

from numpy import count_nonzero, array
from base64 import b64encode
from typing import Dict

from src.schemas.schemas import CImage
from src.schemas.schemas import CImageSet
from src.config import config


def extract_relationships(zip_ref: zipfile.ZipFile) -> Dict[str, str]:
	rels_data = zip_ref.read('word/_rels/document.xml.rels')
	rels_root = ET.fromstring(rels_data)
	return {
		rel.attrib['Id']: rel.attrib['Target'].split('/')[-1]
		for rel in rels_root.findall('.//{http://schemas.openxmlformats.org/package/2006/relationships}Relationship')
	}


def create_cimage(filename: str, img_data: bytes, rel_id: str) -> CImage:
	img_filename = os.path.basename(filename)
	img = CImage(
		document_ver_id=None,
		rel_id=rel_id,
		filename=img_filename,
		data=img_data,
		size=len(img_data),
		hash=None
	)
	img.hash = calc_image_hash(img)
	return img


def extract_images_from_docx(file) -> CImageSet:
	image_set = CImageSet()

	with zipfile.ZipFile(file, "r") as zip_ref:
		relationships = extract_relationships(zip_ref)
		filename_to_rel_id = {target: rel_id for rel_id, target in relationships.items()}

		for filename in zip_ref.namelist():
			if filename.startswith("word/media/") and filename.count("/") == 2:
				img_data = zip_ref.read(filename)
				img_filename = os.path.basename(filename)

				rel_id = filename_to_rel_id.get(img_filename)

				if rel_id:
					img = create_cimage(filename, img_data, rel_id)
					image_set.images[rel_id] = img

	return image_set


def avg_hash_comparison(incoming_image_set: CImageSet, stored_image_set: CImageSet):
	for incoming_image_id, incoming_image in incoming_image_set.images.items():
		max_similarity = -1
		img_path_with_min_similarity = None

		for stored_image_id, stored_image in stored_image_set.images.items():
			similarity = compare_hash(incoming_image.hash, stored_image.hash)
			normalized_similarity = 1 - (similarity / 64)
			if normalized_similarity > max_similarity:
				max_similarity = normalized_similarity
				img_path_with_min_similarity = config.minio_bucket_name + "/images/" + str(
					stored_image.document_ver_id) + "/" + str(stored_image.id) + ".png"

		incoming_image.max_similarity = max_similarity
		incoming_image.img_path_with_max_similarity = img_path_with_min_similarity


def sizeof_comparison(incoming_image_set: CImageSet, stored_image_set: CImageSet):
	for incoming_image_id, incoming_image in incoming_image_set.images.items():
		for stored_image_id, stored_image in stored_image_set.images.items():
			if incoming_image.size == stored_image.size:
				img_path_with_min_similarity = config.minio_bucket_name + "/images/" + str(
					stored_image.document_ver_id) + "/" + str(stored_image.id) + ".png"
				incoming_image.max_similarity = 1
				incoming_image.img_path_with_max_similarity = img_path_with_min_similarity
				break


def compare_image_sets(incoming_image_set: CImageSet, stored_image_set: CImageSet, method: str) -> CImageSet:
	if method == "AvgHash comparison method":
		avg_hash_comparison(incoming_image_set, stored_image_set)
	elif method == "Sizeof comparison method":
		sizeof_comparison(incoming_image_set, stored_image_set)

	return incoming_image_set


def calc_image_hash(image_obj: CImage) -> str:
	image = Image.open(BytesIO(image_obj.data))
	if image.mode == 'RGBA':
		image = image.convert('RGB')

	image_np = array(image)

	resized = cv2.resize(image_np, (8, 8), interpolation=cv2.INTER_AREA)
	gray_image = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
	_, threshold_image = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

	mean = gray_image.mean()

	_hash = ''.join(['1' if threshold_image[i, j] > mean else '0' for i in range(8) for j in range(8)])

	return _hash


def calc_image_set_hashes(imageset_obj: CImageSet) -> None:
	for img_name, img_obj in imageset_obj.images.items():
		img_obj.hash = calc_image_hash(img_obj)


def compare_hash(hash1, hash2):
	return count_nonzero(array(list(hash1)) != array(list(hash2)))
