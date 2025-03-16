from datetime import datetime
from app_main import db_instance, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db_instance.Model):
    id = db_instance.Column(db_instance.Integer, primary_key=True)
    username = db_instance.Column(db_instance.String(64), unique=True, nullable=False)
    email = db_instance.Column(db_instance.String(120), unique=True, nullable=False)
    password_hash = db_instance.Column(db_instance.String(256))
    products = db_instance.relationship('Product', backref='owner', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Category(db_instance.Model):
    id = db_instance.Column(db_instance.Integer, primary_key=True)
    name = db_instance.Column(db_instance.String(50), nullable=False)
    products = db_instance.relationship('Product', backref='category', lazy=True)

class Product(db_instance.Model):
    id = db_instance.Column(db_instance.Integer, primary_key=True)
    name = db_instance.Column(db_instance.String(100), nullable=False)
    description = db_instance.Column(db_instance.Text)
    price = db_instance.Column(db_instance.Float, nullable=False)
    category_id = db_instance.Column(db_instance.Integer, db_instance.ForeignKey('category.id'), nullable=True)
    image_path = db_instance.Column(db_instance.String(255))
    created_at = db_instance.Column(db_instance.DateTime, default=datetime.utcnow)
    updated_at = db_instance.Column(db_instance.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db_instance.Column(db_instance.Integer, db_instance.ForeignKey('user.id'), nullable=False)


def __repr__(self):
        return f"<Product {self.name}>"