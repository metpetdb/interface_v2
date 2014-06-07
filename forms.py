from flask.ext.wtf import Form
from wtforms import TextField, PasswordField, HiddenField
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
