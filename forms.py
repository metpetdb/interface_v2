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
