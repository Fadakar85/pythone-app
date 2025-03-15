import os
import logging
from flask import render_template, redirect, url_for, flash, request, Blueprint
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from app import db
from models import User, Product
from utils import save_image

logging.basicConfig(level=logging.DEBUG)

# Create blueprint
bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    products = Product.query.all()
    return render_template('products.html', products=products)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user is None or not user.check_password(request.form['password']):
            flash('نام کاربری یا رمز عبور نامعتبر است')
            return redirect(url_for('main.login'))

        login_user(user)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)

    return render_template('login.html')

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/dashboard')
@login_required
def dashboard():
    products = Product.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', products=products)

@bp.route('/product/new', methods=['GET', 'POST'])
@login_required
def new_product():
    if request.method == 'POST':
        logging.info("Received POST request for new product")
        logging.info(f"Form data: {request.form}")
        logging.info(f"Files: {request.files}")

        try:
            # Get form data
            name = request.form.get('name')
            description = request.form.get('description')
            price = request.form.get('price')

            logging.info(f"Parsed form data - Name: {name}, Description: {description}, Price: {price}")

            if not name or not price:
                flash('لطفاً نام و قیمت محصول را وارد کنید')
                return render_template('product_form.html')

            try:
                price = float(price)
            except ValueError:
                flash('لطفاً قیمت معتبر وارد کنید')
                return render_template('product_form.html')

            # Handle image upload
            image_path = None
            if 'image' in request.files:
                image = request.files['image']
                if image and image.filename:
                    logging.info(f"Processing image upload: {image.filename}")
                    image_path = save_image(image)
                    if not image_path:
                        logging.error("Image upload failed")
                        flash('خطا در آپلود تصویر')
                        return render_template('product_form.html')
                    logging.info(f"Image saved successfully: {image_path}")

            # Create new product
            try:
                product = Product(
                    name=name,
                    description=description,
                    price=price,
                    image_path=image_path,
                    user_id=current_user.id
                )
                logging.info("Product object created")

                # Try to add to database
                db.session.add(product)
                logging.info("Product added to session")

                # Try to commit
                db.session.commit()
                logging.info(f"Product committed to database successfully with ID: {product.id}")

                flash('محصول با موفقیت ایجاد شد')
                return redirect(url_for('main.dashboard'))

            except Exception as db_error:
                db.session.rollback()
                logging.error(f"Database error while creating product: {str(db_error)}")
                logging.exception("Database error details:")
                flash('خطا در ذخیره محصول در پایگاه داده')
                return render_template('product_form.html')

        except Exception as e:
            logging.error(f"General error in new_product route: {str(e)}")
            logging.exception("Full error details:")
            flash('خطا در ایجاد محصول')
            return render_template('product_form.html')

    return render_template('product_form.html')

@bp.route('/product/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    if product.user_id != current_user.id:
        flash('شما اجازه ویرایش این محصول را ندارید')
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        try:
            product.name = request.form.get('name')
            product.description = request.form.get('description')
            try:
                product.price = float(request.form.get('price'))
            except ValueError:
                flash('لطفاً قیمت معتبر وارد کنید')
                return render_template('product_form.html', product=product)

            # Handle image upload
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

            db.session.commit()
            flash('محصول با موفقیت به‌روزرسانی شد')
            return redirect(url_for('main.dashboard'))

        except Exception as e:
            db.session.rollback()
            logging.error(f"Error updating product: {str(e)}")
            flash('خطا در به‌روزرسانی محصول')
            return render_template('product_form.html', product=product)

    return render_template('product_form.html', product=product)

@bp.route('/product/<int:id>/delete', methods=['POST'])
@login_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    if product.user_id != current_user.id:
        flash('شما اجازه حذف این محصول را ندارید')
        return redirect(url_for('main.dashboard'))

    try:
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
        flash('خطا در حذف محصول')

    return redirect(url_for('main.dashboard'))

@bp.route('/messages')
@login_required
def messages():
    received_messages = Message.query.filter_by(receiver_id=current_user.id).order_by(Message.created_at.desc()).all()
    sent_messages = Message.query.filter_by(sender_id=current_user.id).order_by(Message.created_at.desc()).all()
    return render_template('messages.html', received_messages=received_messages, sent_messages=sent_messages)

@bp.route('/send_message/<int:product_id>', methods=['POST'])
@login_required
def send_message(product_id):
    product = Product.query.get_or_404(product_id)
    content = request.form.get('content')
    if not content:
        flash('متن پیام نمی‌تواند خالی باشد')
        return redirect(url_for('main.index'))
    
    message = Message(
        content=content,
        sender_id=current_user.id,
        receiver_id=product.user_id,
        product_id=product_id
    )
    db.session.add(message)
    db.session.commit()
    flash('پیام شما با موفقیت ارسال شد')
    return redirect(url_for('main.index'))

@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        try:
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')

            if not username or not email or not password:
                flash('لطفاً تمام فیلدها را پر کنید')
                return render_template('signup.html')

            if User.query.filter_by(username=username).first():
                flash('این نام کاربری قبلاً استفاده شده است')
                return render_template('signup.html')

            if User.query.filter_by(email=email).first():
                flash('این ایمیل قبلاً استفاده شده است')
                return render_template('signup.html')

            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            flash('ثبت‌نام با موفقیت انجام شد. اکنون می‌توانید وارد شوید')
            return redirect(url_for('main.login'))

        except Exception as e:
            db.session.rollback()
            logging.error(f"Error in signup: {str(e)}")
            flash('خطا در ثبت‌نام. لطفاً دوباره تلاش کنید')
            return render_template('signup.html')

    return render_template('signup.html')