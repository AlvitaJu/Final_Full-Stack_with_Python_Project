from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo, ValidationError
from wtforms_sqlalchemy.fields import QuerySelectMultipleField
import main


def get_pk(obj):
    return str(obj)


def entry_query():
    return main.Entry.query


def category_query():
    return main.Category.query


class SignUpForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    password1 = PasswordField('Password 1', validators=[DataRequired()])
    password2 = PasswordField('Confirm password', validators=[DataRequired(), EqualTo('password1')])

    def validate_email(self, email):
        user = main.User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('User email is bad :(')


class SignInForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])


class EntriesForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])
    foto = FileField('New foto', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Add')


class CategoriesForm(FlaskForm):
    category_id = StringField('Category_id', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])
    entries = QuerySelectMultipleField(query_factory=main.Entry.query.all, get_label="description",
                                       get_pk=lambda obj: str(obj))
    user = QuerySelectMultipleField(query_factory=main.User.query.all, get_label="Username",
                                    get_pk=lambda obj: str(obj))
    submit = SubmitField('Add')

    def validate_category_id(self, category_id):
        category = main.Category.query.filter_by(category_id=category_id.data).first()
        if category:
            raise ValidationError('Category ID already exists!')



class EditEntriesForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])
    foto = FileField('New foto', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Edit entry')


class EditCategoriesForm(FlaskForm):
    description = StringField('Description', validators=[DataRequired()])
    submit = SubmitField('Edit entry')


class SearchForm(FlaskForm):
    searched = StringField('Searched')
    submit = SubmitField('Search!')
