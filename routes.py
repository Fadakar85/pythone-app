from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from app import app, db
from models import User, Product
from utils import save_image

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
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        image = request.files.get('image')

        image_path = None
        if image:
            image_path = save_image(image)

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

    return render_template('product_form.html')

@app.route('/product/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    if product.user_id != current_user.id:
        flash('شما اجازه ویرایش این محصول را ندارید')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        product.name = request.form['name']
        product.description = request.form['description']
        product.price = float(request.form['price'])

        image = request.files.get('image')
        if image:
            image_path = save_image(image)
            if image_path:
                product.image_path = image_path

        db.session.commit()
        flash('محصول با موفقیت به‌روزرسانی شد')
        return redirect(url_for('dashboard'))

    return render_template('product_form.html', product=product)

@app.route('/product/<int:id>/delete', methods=['POST'])
@login_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    if product.user_id != current_user.id:
        flash('شما اجازه حذف این محصول را ندارید')
        return redirect(url_for('dashboard'))

    db.session.delete(product)
    db.session.commit()
    flash('محصول با موفقیت حذف شد')
    return redirect(url_for('dashboard'))