from fastapi import UploadFile, File
from docx import Document
import os
def my_sum(x, y):
    return x + y

def my_extract_images(file: UploadFile = File(...)):
    if file.filename.endswith('.docx'):
        document = Document(file.file)
        images = []
        for image in document.inline_shapes:
            if image.has_picture:
                images.append(image)

        # Создаем новую папку для сохранения изображений
        dir_name = "extracted_images"
        if not os.path.exists(dir_name):
            os.mkdir(dir_name)

        for i, image in enumerate(images):
            with open(f"{dir_name}/image_{i}.jpg", "wb") as f:
                f.write(image.picture.blob)

        return {"images": images}
    else:
        return {"error": "File type not supported."}