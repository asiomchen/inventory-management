from collections.abc import Iterator
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FileField, TextAreaField, FloatField, IntegerField, SelectField
from wtforms.fields.core import Field
from wtforms.validators import DataRequired, Length, Optional


class Form(FlaskForm):
    _order = []

    def __iter__(self) -> Iterator[Field]:
        for field_name in ["csrf_token", *self._order]:
            field = getattr(self, field_name)
            yield field


class ProductForm(Form):
    title = StringField("Title", validators=[DataRequired(), Length(min=1, max=255)], description="Title")
    category_idx = SelectField("Category", validators=[DataRequired()],)
    description = TextAreaField("Description", validators=[Optional()], description="Description", default="")
    photo = FileField("Photo", validators=[Optional()])
    quantity = IntegerField("Quantity", validators=[DataRequired()], description="Quantity")
    weight = FloatField("Weight", validators=[DataRequired()], description="Weight in grams")
    purchase_price = FloatField("Purchase Price", validators=[DataRequired()], description="Purchase Price in USD")
    sale_price = FloatField("Sale Price", validators=[DataRequired()], description="Sale Price in USD")
    volume = FloatField("Volume", validators=[Optional()], description="Volume in ml(optional)")
    submit = SubmitField("Submit")
    _order = ["title", "category_idx", "photo", "quantity", "weight", "purchase_price", "sale_price", "volume", "description", "submit"]
    