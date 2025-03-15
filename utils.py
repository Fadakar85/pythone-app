import os
import logging
from PIL import Image
from werkzeug.utils import secure_filename
from flask import current_app

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(file):
    logging.info(f"Starting to save image: {file.filename if file else 'No file'}")

    if not file:
        logging.error("No file provided")
        return None

    if not allowed_file(file.filename):
        logging.error(f"File type not allowed: {file.filename}")
        return None

    try:
        # Create a secure filename
        filename = secure_filename(file.filename)
        logging.info(f"Secure filename created: {filename}")

        # Ensure the upload folder exists
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        logging.info(f"Upload folder verified: {upload_folder}")

        # Generate the full file path
        filepath = os.path.join(upload_folder, filename)
        logging.info(f"Full filepath: {filepath}")

        # Save and optimize the image
        image = Image.open(file)
        logging.info("Image opened successfully")

        image = image.convert('RGB')
        logging.info("Image converted to RGB")

        image.thumbnail((800, 800))
        logging.info("Image resized")

        image.save(filepath, optimize=True, quality=85)
        logging.info(f"Image saved successfully to: {filepath}")

        return filename

    except Exception as e:
        logging.error(f"Error saving image: {str(e)}")
        logging.exception("Full error traceback:")
        return None