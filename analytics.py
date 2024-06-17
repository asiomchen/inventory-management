import logging
from flask import Blueprint, render_template, request, current_app
from flask import make_response
from data import Product, InvoiceProduct, Invoice
from sqlalchemy import func
import pandas as pd
import json
import plotly
import plotly.express as px

dashboard = Blueprint(
    "analytics",
    __name__,
    template_folder="templates/analytics/",
)


@dashboard.route("/dashboard")
def dash():
    return render_template("analytics/dashboard.html")


@dashboard.route("/dashboard/best_selling_products")
def best_selling_products():
    query = Product.query
    query = query.join(InvoiceProduct, Product.idx == InvoiceProduct.product_idx)
    query = query.with_entities(
        Product.idx,
        Product.title,
        func.sum(InvoiceProduct.quantity).label("total_quantity"),
    )
    query = query.group_by(Product.idx)
    query = query.order_by(func.sum(InvoiceProduct.quantity).desc())
    lim = request.args.get("limit", 5)
    bestsellers = query.limit(lim).all()
    bestsellers = pd.DataFrame(bestsellers)
    bestsellers.columns = ["idx", "Title", "Total Quantity"]
    bestsellers = bestsellers.iloc[::-1]
    fig = px.bar(
        bestsellers,
        x="Total Quantity",
        y="Title",
        title=f"Top {lim} Best Selling Products",
        hover_data=["Total Quantity"],
    )
    resp = prepare_response(fig)
    return resp


@dashboard.route("/dashboard/profit")
def get_profit():
    query = Invoice.query
    query = query.with_entities(
        Invoice.date, func.sum(Invoice.total_customer_price).label("total_profit")
    )
    query = query.group_by(Invoice.date)
    query = query.order_by(Invoice.date)
    logging.info(f"Query: {request.args}")
    profit_by = request.args.get("profit_by", "month")
    logging.info(f"Grouping profit by {profit_by}")
    # if sqlite is used, use strftime to extract month and year
    if current_app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite"):
        if profit_by == "day":
            format = "%Y-%m-%d"
        elif profit_by == "month":
            format = "%Y-%m"
        elif profit_by == "year":
            format = "%Y"
        logging.info(f"Using format {format}")
        query = query.with_entities(
            func.strftime(format, Invoice.date).label("sort_date"),
            func.sum(Invoice.total_customer_price).label("total_profit"),
        )
        query = query.order_by("sort_date")
    start_date = request.args.get("start_date", None)
    end_date = request.args.get("end_date", None)
    if start_date:
        query = query.filter(Invoice.date >= start_date)
    if end_date:
        query = query.filter(Invoice.date <= end_date)
    profit = query.all()
    profit = pd.DataFrame(profit)
    profit = profit.groupby("sort_date").sum().reset_index()
    profit.columns = ["Date", "Total profit (USD)"]
    profit["Date"] = pd.to_datetime(profit["Date"])
    if profit_by == "month":
        profit["Date"] = profit["Date"].dt.strftime("%B %Y")
    elif profit_by == "year":
        profit["Date"] = profit["Date"].dt.strftime("%Y")
    else:
        profit["Date"] = profit["Date"].dt.strftime("%Y-%m-%d")
    fig = px.bar(profit, x="Date", y="Total profit (USD)", title="profit")
    return prepare_response(fig)


def prepare_response(data):
    data = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)
    resp = make_response(data)
    resp.mimetype = "application/json"
    return resp
