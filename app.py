import os
from pydoc import describe
import re
from flask import Flask, render_template, request, url_for, redirect, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

from sqlalchemy.sql import func


basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] =\
        'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
db = SQLAlchemy(app)

class Product(db.Model):
    idx = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    photo = db.Column(db.String(255))
    quantity = db.Column(db.Integer)
    weight = db.Column(db.Float)
    purchase_price = db.Column(db.Float)
    sale_price = db.Column(db.Float)
    profit = db.Column(db.Float)

    def __repr__(self):
        return '<Product %r>' % self.title

@app.route('/')
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)
    

@app.route('/<int:product_id>/')
def product(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product.html', product=product)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

@app.route('/create/', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        quantity = int(request.form['quantity'])
        photo = request.files['photo']
        weight = float(request.form['weight'])
        purchase_price = float(request.form['purchase_price'])
        sale_price = float(request.form['sale_price'])
        profit = sale_price - purchase_price

        if photo:
            filename = secure_filename(photo.filename)
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            photo = filename
        else:
            photo = 'No photo'

        product = Product(title=title, 
                          description=description, 
                          quantity=quantity, 
                          photo=photo, 
                          weight=weight, 
                          purchase_price=purchase_price, 
                          sale_price=sale_price, 
                          profit=profit)
        db.session.add(product)
        db.session.commit()

        return redirect(url_for('index'))
    return render_template('create.html')

@app.route('/<int:product_id>/edit/', methods=('GET', 'POST'))
def edit(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        product.title = request.form['title']
        product.description = request.form['description']
        product.quantity = int(request.form['quantity'])
        product.weight = float(request.form['weight'])
        product.purchase_price = float(request.form['purchase_price'])
        product.sale_price = float(request.form['sale_price'])
        product.profit = product.sale_price - product.purchase_price

        # Check if a new photo was uploaded in the form
        if 'photo' in request.files:
            new_photo = request.files['photo']
            if new_photo.filename:
                # Process the new photo and update the product's photo field
                filename = secure_filename(new_photo.filename)
                new_photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                product.photo = filename

        db.session.add(product)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template('edit.html', product=product)

@app.route('/about/')
def about():
    return render_template('about.html')

@app.post('/<int:product_id>/delete/')
def delete(product_id):
    product = product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/table/')
def table():
    products = Product.query.all()
    return render_template('table.html', products=products)

@app.route('/add2invoice/<int:product_id>/')
def add2invoice(product_id):
    return redirect(url_for('table'))