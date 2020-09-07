from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField


class InfoForm(FlaskForm):
    a=0
    range= IntegerField('Maximum distance(in miles) you can around')
    timeToVsit=IntegerField(' Time to Visit')
    submit=SubmitField('Submit')
    # placeCoordinate=StringField('Address')