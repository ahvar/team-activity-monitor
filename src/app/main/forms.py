from flask import request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import ValidationError, DataRequired, Length


class QuestionForm(FlaskForm):
    post = TextAreaField(
        "Ask About the Team", validators=[DataRequired(), Length(min=1, max=140)]
    )
    submit = SubmitField("Submit")


class EmptyForm(FlaskForm):
    submit = SubmitField("Submit")


class SearchForm(FlaskForm):
    q = StringField("Search", validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        if "formdata" not in kwargs:
            kwargs["formdata"] = request.args
        if "meta" not in kwargs:
            kwargs["meta"] = {"csrf": False}
        super(SearchForm, self).__init__(*args, **kwargs)
