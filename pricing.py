import email
from flask import render_template, request, url_for, redirect, send_from_directory, Blueprint, current_app, flash
from flask_login import login_required
from data import db , Pricing


pricing = Blueprint('pricing', __name__)

@pricing.route('/pricings/<int:pricing_id>')
@login_required
def details(pricing_id):
    pricing = Pricing.query.get(pricing_id)
    return render_template('pricings/details.html', pricing=pricing)

@pricing.route('/pricings')
@login_required
def pricings():
    pricings = Pricing.query.all()
    return render_template('pricings/table.html', pricings=pricings)

@pricing.route('/pricings/new', methods=['GET', 'POST'])
@login_required
def new():
    if request.method == 'POST':
        name = request.form['name']
        formula_online = request.form['formula_online']
        formula_teahouse = request.form['formula_teahouse']
        pricing = Pricing(name=name, formula_online=formula_online, formula_teahouse=formula_teahouse)
        db.session.add(pricing)
        db.session.commit()
        flash('pricing added successfully' , 'success')
        return redirect(url_for('pricing.pricings'))
    return render_template('pricings/new.html')

@pricing.route('/pricings/<int:pricing_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(pricing_id):
    pricing: Pricing = Pricing.query.get(pricing_id)
    if request.method == 'POST':
        pricing.name = request.form['name']
        pricing.formula_online = request.form['formula_online']
        pricing.formula_teahouse = request.form['formula_teahouse']
        db.session.commit()
        flash('pricing updated successfully', 'success')
        return redirect(url_for('pricing.pricings'))
    return render_template('pricings/edit.html', pricing=pricing)

@pricing.route('/pricings/<int:pricing_id>/delete', methods=['POST'])
@login_required
def delete(pricing_id):
    pricing = Pricing.query.get(pricing_id)
    db.session.delete(pricing)
    db.session.commit()
    flash('pricing deleted successfully', 'success')
    return redirect(url_for('pricing.pricings'))
