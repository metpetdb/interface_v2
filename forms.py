from flask.ext.wtf import Form
from wtforms import TextField, PasswordField
from wtforms.validators import Required

class LoginForm(Form):
    email = TextField('email', validators = [Required()])
    password = PasswordField('password')
