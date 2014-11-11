from flask.ext.wtf import Form
from wtforms import TextField, PasswordField, HiddenField, FormField, FieldList, RadioField, DateField, SelectField, BooleanField, SelectMultipleField
from wtforms.validators import Required, Email, EqualTo

class LoginForm(Form):
    email = TextField('email', validators = [Required(), Email()])
    password = PasswordField('password')

class RequestPasswordResetForm(Form):
    email = TextField('email', validators = [Required(), Email()])

class PasswordResetForm(Form):
    token = HiddenField()
    password = PasswordField('password', validators = [
        Required(),
        EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('confirm')

class EditForm(Form):
  owner = TextField('Owner', validators = [Required()])
  aliases = TextField('Aliases')
  date_collected = TextField('Date Collected')
  #date_collected = DateField('Date')
  rock_type = SelectField('Rock Type', validators = [Required()])
  public = RadioField('Public', choices=[('Y','Y'), ('N','N')], validators = [Required()])
  country = TextField('Country')
  location_text = TextField('Location')
  collector = TextField('Collector')
  region = FieldList(TextField('Region'), min_entries = 1)
  metamorphic_grades = SelectField('Metamorphic Grade')
  longitude = TextField('Longitude', validators = [Required()])
  latitude = TextField('Latitude', validators = [Required()])
  minerals = SelectMultipleField('Minerals')

class EditChemForm(Form):
  owner = TextField('Owner', validators=[Required()])
  public = RadioField('Public', choices=[('Y','Y'), ('N','N')])
  analyst = TextField('Analyst')
  analysis_material = TextField('Analyst')
  total = TextField('Total')
  StageX = TextField('Stage X')
  StageY = TextField('Stage Y')
