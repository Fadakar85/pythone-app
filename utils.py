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

        # Save the original file first
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        logging.info(f"Original file saved to: {file_path}")

        # Now open with PIL and process
        with Image.open(file_path) as image:
            logging.info("Image opened successfully with PIL")

            # Convert to RGB (if needed)
            if image.mode != 'RGB':
                image = image.convert('RGB')
                logging.info("Image converted to RGB")

            # Resize the image
            image.thumbnail((800, 800))
            logging.info("Image resized")

            # Save the processed image
            image.save(file_path, optimize=True, quality=85)
            logging.info(f"Processed image saved successfully to: {file_path}")

        return filename

    except Exception as e:
        logging.error(f"Error saving image: {str(e)}")
        logging.exception("Full error traceback:")
        # If there was an error and we created a file, try to remove it
        if 'file_path' in locals() and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logging.info("Cleaned up partial file after error")
            except Exception as cleanup_error:
                logging.error(f"Error cleaning up file: {str(cleanup_error)}")
        return None