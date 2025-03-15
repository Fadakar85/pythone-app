import os
import logging
from PIL import Image
from werkzeug.utils import secure_filename
from flask import current_app

logging.basicConfig(level=logging.DEBUG)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_IMAGE_SIZE = (800, 800)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(file):
    """
    Save and process an uploaded image file.
    Returns the filename if successful, None if failed.
    """
    try:
        if not file:
            logging.warning("No file provided")
            return None

        if not file.filename:
            logging.warning("Empty filename")
            return None

        if not allowed_file(file.filename):
            logging.warning(f"File type not allowed: {file.filename}")
            return None

        # Create a secure filename
        filename = secure_filename(file.filename)

        # Ensure upload directory exists
        upload_dir = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)

        # Full path for the file
        file_path = os.path.join(upload_dir, filename)

        # First save the uploaded file
        file.save(file_path)
        logging.info(f"Original file saved: {file_path}")

        # Process the image with PIL
        with Image.open(file_path) as img:
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Resize if larger than MAX_IMAGE_SIZE
            if img.size[0] > MAX_IMAGE_SIZE[0] or img.size[1] > MAX_IMAGE_SIZE[1]:
                img.thumbnail(MAX_IMAGE_SIZE)

            # Save the processed image
            img.save(file_path, 'JPEG', quality=85, optimize=True)
            logging.info(f"Image processed and saved: {file_path}")

        return filename

    except Exception as e:
        logging.error(f"Error saving image: {str(e)}")
        # Clean up if file was created
        if 'file_path' in locals() and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logging.info(f"Cleaned up failed upload: {file_path}")
            except Exception as cleanup_error:
                logging.error(f"Error during cleanup: {str(cleanup_error)}")
        return None