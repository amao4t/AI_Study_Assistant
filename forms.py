from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FileField, SelectField, BooleanField
from wtforms.validators import InputRequired

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    remember_me = BooleanField('Remember Me')

class SignupForm(FlaskForm):
    new_username = StringField('Username', validators=[InputRequired()])
    new_password = PasswordField('Password', validators=[InputRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[InputRequired()])

class UploadForm(FlaskForm):
    studyMaterial = FileField('Study Material', validators=[InputRequired()])