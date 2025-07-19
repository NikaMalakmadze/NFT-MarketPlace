
from flask import send_from_directory

from config import settings

def get_nft_image(image_file):
    return send_from_directory(settings.db.UPLOAD_FOLDER / 'nft-images', image_file)

def get_category_image(image_file):
    return send_from_directory(settings.db.APP_FILES / 'category-icons', image_file)
