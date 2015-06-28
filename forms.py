from flask.ext.wtf import Form
from wtforms import widgets, TextField, PasswordField, HiddenField, FormField, FieldList, RadioField, DateField, SelectField, BooleanField, SelectMultipleField
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
  rock_type = SelectField('Rock Type', validators = [Required()])
  public = RadioField('Public', choices=[('Y','Y'), ('N','N')], validators = [Required()])
  country = TextField('Country')
  location_text = TextField('Location')
  collector = TextField('Collector')
  region = FieldList(TextField('Region'))
  metamorphic_grades = SelectField('Metamorphic Grade')
  longitude = TextField('Longitude', validators = [Required()])
  latitude = TextField('Latitude', validators = [Required()])
  minerals = SelectMultipleField('Minerals', option_widget=widgets.CheckboxInput(),
                                  widget=widgets.ListWidget(prefix_label=False))
  mineral2 = BooleanField('Minerals')

class EditChemForm(Form):
  owner = TextField('Owner', validators=[Required()])
  public = RadioField('Public', choices=[('Y','Y'), ('N','N')])
  analyst = TextField('Analyst')
  analysis_material = TextField('Analyst')
  total = TextField('Total')
  StageX = TextField('Stage X')
  StageY = TextField('Stage Y')

class NewSample(Form):
  owner = TextField('Owner')#, validators=[Required()])
  isgn = TextField('ISGN')
  aliases = TextField('Aliases')
  date_collected = TextField('Date Collected')
  rock_type = SelectField('Rock Type')#, validators = [Required()])
  country = TextField('Country')
  location_text = TextField('Location')
  collector = TextField('Collector')
  region = FieldList(TextField('Region'))
  metamorphic_grades = SelectField('Metamorphic Grade')
  longitude = TextField('Longitude')#, validators = [Required()])
  latitude = TextField('Latitude')#, validators = [Required()])
  public = RadioField('Public', choices=[('Y','Y'),('N','N')])
  met_region = TextField('Metamorphic Regions')
  pub_references = TextField('Publication References')

class NewChem(Form):
  owner = TextField('Owner')
  point_number = TextField('Point Number')
  public = RadioField('Public', choices=[('Y','Y'),('N','N')])
  analysis_method = TextField('Analysis Method')
  analyst = TextField('Analyst')
  analysis_location = TextField('Analysis Location')
  description = TextField('Description')
  analysis_material = TextField('Analysis Material')
  total = TextField('Total')
  StageX = TextField('Stage X')
  StageY = TextField('Stage Y')
