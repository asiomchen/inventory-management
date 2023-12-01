import os
import random
from flask import Flask, render_template, request, url_for, redirect, send_from_directory , flash
from werkzeug.utils import secure_filename
from utils import generate_random_image
from data import db, Product, InvoiceProduct, Invoice, User
from main import main

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SECRET_KEY'] = "dev"
app.config['SQLALCHEMY_DATABASE_URI'] =\
        'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#app.config["MAIN_PASSWORD"] = generate_password_hash(os.environ['MAIN_PASSWORD'])
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.register_blueprint(main)
db.init_app(app)

    
#init database on first run
with app.app_context():
    db.create_all()
    if not Product.query.all():
        for i in range(10):
            weight = round(random.random(), 2)
            purchase_price = random.randint(1, 100)
            sale_price = purchase_price + random.randint(1, 50)
            profit = sale_price - purchase_price
            product = Product(title=f'Product {i}', 
                              description=f'Description {i}', 
                              quantity=i, 
                              photo=generate_random_image(f'uploads/test_product_{i}.png'),
                              weight=weight,
                              purchase_price=purchase_price,
                              sale_price=sale_price,
                              profit=profit)
            db.session.add(product)
            db.session.commit()
            

