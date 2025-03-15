import os
import logging
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from app import app, db
from models import User, Product
from utils import save_image

logging.basicConfig(level=logging.DEBUG)

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
            # Get form data
            name = request.form.get('name')
            description = request.form.get('description')
            price = request.form.get('price')

            # Validate required fields
            if not name or not price:
                flash('لطفاً نام و قیمت محصول را وارد کنید')
                return render_template('product_form.html')

            try:
                price = float(price)
            except ValueError:
                flash('لطفاً قیمت معتبر وارد کنید')
                return render_template('product_form.html')

            # Handle image upload
            image = request.files.get('image')
            image_path = None
            if image and image.filename:
                image_path = save_image(image)
                if not image_path:
                    flash('خطا در آپلود تصویر. لطفاً دوباره تلاش کنید')
                    return render_template('product_form.html')

            # Create product
            product = Product(
                name=name,
                description=description,
                price=price,
                image_path=image_path,
                user_id=current_user.id
            )

            db.session.add(product)
            db.session.commit()

            flash('محصول با موفقیت ایجاد شد')
            return redirect(url_for('dashboard'))

        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating product: {str(e)}")
            flash('خطا در ایجاد محصول. لطفاً دوباره تلاش کنید')
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
            # Update basic info
            product.name = request.form.get('name')
            product.description = request.form.get('description')

            try:
                product.price = float(request.form.get('price'))
            except ValueError:
                flash('لطفاً قیمت معتبر وارد کنید')
                return render_template('product_form.html', product=product)

            # Handle image update
            image = request.files.get('image')
            if image and image.filename:
                new_image_path = save_image(image)
                if new_image_path:
                    # Remove old image if exists
                    if product.image_path:
                        old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], product.image_path)
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)
                    product.image_path = new_image_path
                else:
                    flash('خطا در آپلود تصویر جدید')
                    return render_template('product_form.html', product=product)

            db.session.commit()
            flash('محصول با موفقیت به‌روزرسانی شد')
            return redirect(url_for('dashboard'))

        except Exception as e:
            db.session.rollback()
            logging.error(f"Error updating product: {str(e)}")
            flash('خطا در به‌روزرسانی محصول. لطفاً دوباره تلاش کنید')
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
        # Remove image file if exists
        if product.image_path:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], product.image_path)
            if os.path.exists(image_path):
                os.remove(image_path)

        db.session.delete(product)
        db.session.commit()
        flash('محصول با موفقیت حذف شد')

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting product: {str(e)}")
        flash('خطا در حذف محصول. لطفاً دوباره تلاش کنید')

    return redirect(url_for('dashboard'))