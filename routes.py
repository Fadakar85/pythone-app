import logging
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from app import app, db
from models import User, Product
from utils import save_image
import os

logging.basicConfig(level=logging.INFO) # Add this line to configure logging

@app.route('/')
def index():
    products = Product.query.all()
    return render_template('products.html', products=products)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user is None or not user.check_password(request.form['password']):
            flash('نام کاربری یا رمز عبور نامعتبر است')
            return redirect(url_for('login'))

        login_user(user)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)

    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    products = Product.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', products=products)

@app.route('/product/new', methods=['GET', 'POST'])
@login_required
def new_product():
    if request.method == 'POST':
        try:
            logging.info("Starting new product creation")
            name = request.form['name']
            description = request.form['description']
            price = float(request.form['price'])
            image = request.files.get('image')

            logging.info(f"Received product data - Name: {name}, Image: {image.filename if image else 'No image'}")

            # Handle image upload
            image_path = None
            if image:
                logging.info("Processing image upload")
                image_path = save_image(image)
                if not image_path:
                    logging.error("Image upload failed")
                    flash('خطا در آپلود تصویر. لطفا مطمئن شوید که فایل معتبر است')
                    return render_template('product_form.html')
                logging.info(f"Image saved successfully with path: {image_path}")

            product = Product(
                name=name,
                description=description,
                price=price,
                image_path=image_path,
                user_id=current_user.id
            )

            db.session.add(product)
            db.session.commit()
            logging.info("Product created successfully")
            flash('محصول با موفقیت ایجاد شد')
            return redirect(url_for('dashboard'))

        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating product: {str(e)}")
            logging.exception("Full error traceback:")
            flash('خطا در ایجاد محصول. لطفا دوباره تلاش کنید')
            return render_template('product_form.html')

    return render_template('product_form.html')

@app.route('/product/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    if product.user_id != current_user.id:
        flash('شما اجازه ویرایش این محصول را ندارید')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        try:
            logging.info(f"Starting product update for ID: {id}")
            product.name = request.form['name']
            product.description = request.form['description']
            product.price = float(request.form['price'])

            image = request.files.get('image')
            if image:
                logging.info("Processing new image upload for product update")
                image_path = save_image(image)
                if image_path:
                    # Remove old image if it exists
                    if product.image_path:
                        old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], product.image_path)
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)
                            logging.info(f"Old image removed: {old_image_path}")
                    product.image_path = image_path
                    logging.info(f"New image saved: {image_path}")

            db.session.commit()
            logging.info("Product updated successfully")
            flash('محصول با موفقیت به‌روزرسانی شد')
            return redirect(url_for('dashboard'))

        except Exception as e:
            db.session.rollback()
            logging.error(f"Error updating product: {str(e)}")
            logging.exception("Full error traceback:")
            flash('خطا در به‌روزرسانی محصول. لطفا دوباره تلاش کنید')
            return render_template('product_form.html', product=product)

    return render_template('product_form.html', product=product)

@app.route('/product/<int:id>/delete', methods=['POST'])
@login_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    if product.user_id != current_user.id:
        flash('شما اجازه حذف این محصول را ندارید')
        return redirect(url_for('dashboard'))

    try:
        logging.info(f"Starting product deletion for ID: {id}")
        # Remove the image file if it exists
        if product.image_path:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], product.image_path)
            if os.path.exists(image_path):
                os.remove(image_path)
                logging.info(f"Image file removed: {image_path}")

        db.session.delete(product)
        db.session.commit()
        logging.info("Product deleted successfully")
        flash('محصول با موفقیت حذف شد')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting product: {str(e)}")
        logging.exception("Full error traceback:")
        flash('خطا در حذف محصول. لطفا دوباره تلاش کنید')

    return redirect(url_for('dashboard'))