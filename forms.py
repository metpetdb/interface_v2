from flask.ext.wtf import Form
from wtforms import (
  widgets,
  TextField,
  PasswordField,
  HiddenField,
  FormField,
  FieldList,
  RadioField,
  DateField,
  SelectField,
  BooleanField,
  SelectMultipleField
)
from wtforms.validators import (
  Required,
  Email,
  EqualTo,
  NumberRange
)

class LoginForm(Form):
  email = TextField('email', validators=[Required(), Email()])
  password = PasswordField('password')

class RequestPasswordResetForm(Form):
  email = TextField('email', validators=[Required(), Email()])

class PasswordResetForm(Form):
  token = HiddenField()
  password = PasswordField('password', validators=[
    Required(),
    EqualTo('confirm', message='Passwords must match')
  ])
  confirm = PasswordField('confirm')

class EditForm(Form):
  owner = TextField('Owner', validators=[Required()])
  igsn = TextField('ISGN')
  aliases = TextField('Aliases')
  date_collected = TextField('Date Collected')
  rock_type = SelectField('Rock Type', validators=[Required()])
  public = RadioField('Public', choices=[('Y','Y'), ('N','N')], validators=[Required()])
  country = TextField('Country')
  location_text = TextField('Location')
  collector = TextField('Collector')
  region = FieldList(TextField('Region'))
  metamorphic_regions = SelectField('Metamorphic Region')
  metamorphic_grades = SelectField('Metamorphic Grade')
  longitude = TextField('Longitude', validators=[
    Required(),
    NumberRange(min=-180, max=180, message="Please enter a number between -180 and 180")
  ])
  latitude = TextField('Latitude', validators=[
    Required(),
    NumberRange(min=-90, max=90, message="Please enter a number between -90 and 90")
  ])
  minerals = SelectMultipleField('Minerals', option_widget=widgets.CheckboxInput(),
    widget=widgets.ListWidget(prefix_label=False))
  pub_references = TextField('Publication References')

class EditChemForm(Form):
  owner = TextField('Owner', validators=[Required()])
  point_number = TextField('Point Number')
  public = RadioField('Public', choices=[('Y','Y'),('N','N')])
  analysis_method = TextField('Analysis Method')
  analyst = TextField('Analyst')
  analysis_location = TextField('Analysis Location')
  description = TextField('Description')
  analysis_material = TextField('Analysis Material')
  minerals = SelectField('Mineral')
  oxides = FieldList(TextField('Oxides'))
  elements = FieldList(TextField('Elements'))
  total = TextField('Total')
  StageX = TextField('Stage X')
  StageY = TextField('Stage Y')
