import os
import random
from venv import logger
from flask import Flask, render_template, request, url_for, redirect, send_from_directory , flash
from flask_login import LoginManager
from werkzeug.security import generate_password_hash
from utils import generate_random_image
from data import db, Product, InvoiceProduct, Invoice, User, Image
from dotenv import load_dotenv
load_dotenv()
from main import main
from images import upload_image, delete_image
from auth import auth as auth_blueprint
import logging
import sys
import pymysql
pymysql.install_as_MySQLdb()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)


def create_app():
    basedir = os.path.abspath(os.path.dirname(__file__))
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
    # app.config['SQLALCHEMY_DATABASE_URI'] =\
    #         'sqlite:///' + os.path.join(basedir, 'database.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config["MAIN_PASSWORD"] = generate_password_hash(os.environ['MAIN_PASSWORD'])
    UPLOAD_FOLDER = os.path.join(basedir)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    app.register_blueprint(main)
    app.register_blueprint(auth_blueprint)
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    #init database on first run
    with app.app_context():
        db.create_all()
        if not Product.query.all():
            for i in range(2):
                weight = round(random.random(), 2)
                purchase_price = random.randint(1, 100)
                sale_price = purchase_price + random.randint(1, 50)
                profit = sale_price - purchase_price
                photo = generate_random_image(f'uploads/test_product_{i}.png')
                secure_url, public_id = upload_image(f'uploads/test_product_{i}.png')
                image = Image(url=secure_url, public_id=public_id)
                db.session.add(image)
                db.session.commit()
                image = Image.query.filter_by(public_id=public_id).first()
                product = Product(title=f'Product {i}', 
                                description=f'Description {i}', 
                                quantity=i, 
                                photo_idx = image.idx,
                                weight=weight,
                                purchase_price=purchase_price,
                                sale_price=sale_price,
                                profit=profit)
                logging.info(f"image: {image}"
                                f"product: {product}")
                db.session.add(product)
                db.session.commit()
        if not User.query.all():
            user = User(username='admin', password=app.config["MAIN_PASSWORD"])
            db.session.add(user)
            db.session.commit()
        
    return app
                

