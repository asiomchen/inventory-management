from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FileField, TextAreaField, FloatField, IntegerField, SelectField
from wtforms.validators import DataRequired, Length, Optional
from flask_wtf.file import FileAllowed, FileRequired


class ProductForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(min=1, max=255)], description="Title")
    category_idx = SelectField("Category", validators=[DataRequired()],)
    photo = FileField("Photo", validators=[Optional()])
    quantity = IntegerField("Quantity", validators=[DataRequired()], description="Quantity")
    weight = FloatField("Weight", validators=[DataRequired()], description="Weight in grams")
    purchase_price = FloatField("Purchase Price", validators=[DataRequired()], description="Purchase Price in USD")
    sale_price = FloatField("Sale Price", validators=[DataRequired()], description="Sale Price in USD")
    volume = FloatField("Volume", validators=[Optional()], description="Volume in ml(optional)")
    description = TextAreaField("Description", validators=[Optional()], description="Description", default="")
    submit = SubmitField("Submit")    


class CustomerForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(min=1, max=255)], description="Name")
    phone = StringField("Phone", validators=[DataRequired(), Length(min=1, max=255)], description="Phone")
    address = StringField("Address", validators=[DataRequired(), Length(min=1, max=255)], description="Address")
    email = StringField("Email", validators=[DataRequired(), Length(min=1, max=255)], description="Email")
    notes = TextAreaField("Notes", validators=[Optional()], description="Notes")
    submit = SubmitField("Submit")

class ImportForm(FlaskForm):
    file = FileField("File", validators=[FileRequired(), FileAllowed(["csv"], "CSV only!")])
    submit = SubmitField("Submit")