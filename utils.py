import os
from PIL import Image
from werkzeug.utils import secure_filename
from flask import current_app

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        # Create upload directory if it doesn't exist
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Save and optimize image
        image = Image.open(file)
        image = image.convert('RGB')
        image.thumbnail((800, 800))  # Resize while maintaining aspect ratio
        image.save(filepath, optimize=True, quality=85)
        
        return filename
    return None
