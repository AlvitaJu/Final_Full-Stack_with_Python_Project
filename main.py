import os
import secrets
from PIL import Image

from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, current_user, login_required, logout_user
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView


basedir = os.path.abspath(os.path.dirname(__file__))

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'sign_in'
login_manager.login_message_category = 'info'

app = Flask(__name__)
app.config['SECRET_KEY'] = "?``§=)()%``ÄLÖkhKLWDO=?)(_:;LKADHJATZQERZRuzeru3rkjsdfLJFÖSJ"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite?check_same_thread=False')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

login_manager.init_app(app)
db.init_app(app)

admin = Admin(app, name='microblog', template_mode='bootstrap3')


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    categories = db.relationship("Category")


class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.String, unique=True, nullable=False)
    description = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship("User")
    entries = db.relationship('Entry')

    def __init__(self, category_id, description, user_id):
        self.category_id = category_id
        self.description = description
        self.user_id = user_id


class Entry(db.Model):
    __tablename__ = 'entry'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    foto = db.Column(db.String(20), nullable=False, default='default.jpg')
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship('Category')

    def __init__(self, title, description, category_id, foto):
        self.title = title
        self.description = description
        self.category_id = category_id
        self.foto = foto


class ManoModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated


admin.add_view(ManoModelView(User, db.session))
admin.add_view(ManoModelView(Category, db.session))
admin.add_view(ManoModelView(Entry, db.session))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


with app.app_context():
    import forms

    db.create_all()


@app.route('/')
def index():
    return render_template('homepage.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = forms.SignUpForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, password=form.password1.data, email=form.email.data)
        db.session.add(user)
        db.session.commit()
        flash(f'Welcome, {user.username}!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = forms.SignInForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if not user:
            flash(f'User {form.email.data} does not exist!', 'danger')
            return redirect(url_for('login'))
        if not form.password.data == user.password:
            flash(f'User / password do not math!', 'danger')
            return redirect(url_for('login'))
        login_user(user)
        flash(f'Welcome, {user.email}', 'success')
        return redirect(url_for('index'))
    return render_template('login.html', form=form)


@app.route('/categories', methods=['GET', 'POST'])
@login_required
def categories():
    all_categories = Category.query.all()
    form = forms.CategoriesForm()
    if form.validate_on_submit():
        new_category = Category(
            category_id=form.category_id.data, description=form.description.data, user_id=current_user.id
        )
        if not new_category:
            flash(f' Category ID {form.category_id.data} already exists!', 'danger')
            return redirect(url_for('categories'))
        flash(f' New category ID: {form.category_id.data}', 'success')
        for entry in form.entries.data:
            added_entry = Entry.query.get(entry.id)
            new_category.entries.append(added_entry)
        db.session.add(new_category)
        db.session.commit()
        return redirect(url_for('entries', category_id=new_category.id))
    return render_template('categories.html', form=form, all_categories=all_categories)


@app.route('/entries/<category_id>', methods=['GET', 'POST'])
@login_required
def entries(category_id):
    all_entries = Entry.query.filter_by(category_id=category_id)
    form = forms.EntriesForm()
    if form.validate_on_submit():
        new_entry = Entry(
            title=form.title.data, description=form.description.data, foto=form.foto.data, category_id=category_id
        )
        db.session.add(new_entry)
        db.session.commit()
        return redirect(url_for('entries', category_id=category_id))
    return render_template('entries.html', form=form, all_entries=all_entries)


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(basedir, 'static/foto', picture_fn)

    output_size = (50, 50)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route('/edit_entry/<entry_id>', methods=['GET', 'POST'])
@login_required
def edit_entry(entry_id):
    form = forms.EditEntriesForm()
    entry = Entry.query.filter_by(id=entry_id).first()

    if form.validate_on_submit():
        if form.foto.data:
            foto = save_picture(form.foto.data)
            entry.foto = foto
        entry.title = form.title.data
        entry.description = form.description.data
        db.session.add(entry)
        db.session.commit()
        return redirect(f'/entries/{entry.category_id}')

    elif request.method == 'GET':
        form.title.data = entry.title
        form.description.data = entry.description
        form.foto.data = entry.foto
    foto = url_for('static', filename='foto/' + entry.foto)
    return render_template('edit_entry.html', form=form, foto=foto)


@app.route('/delete_entry/<entry_id>', methods=['GET', 'POST'])
@login_required
def delete_entry(entry_id):
    entry = Entry.query.filter_by(id=entry_id).first()

    if request.method == 'POST':
        if entry:
            db.session.delete(entry)
            db.session.commit()
            return redirect('/categories')
        # abort(404)
    return render_template('delete_entry.html')


@app.route('/edit_category/<category_id>', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    form = forms.EditCategoriesForm()
    category = Category.query.filter_by(id=category_id).first()

    if form.validate_on_submit():
        category.description = form.description.data
        db.session.add(category)
        db.session.commit()
        return redirect('/categories')

    elif request.method == 'GET':
        form.description.data = category.description
    return render_template('edit_category.html', form=form)


@app.route('/delete_category/<category_id>', methods=['GET', 'POST'])
@login_required
def delete_category(category_id):
    category = Category.query.filter_by(id=category_id).first()

    if request.method == 'POST':
        if category:
            db.session.delete(category)
            db.session.commit()
            return redirect('/categories')
        # abort(404)
    return render_template('delete_category.html')


@app.route('/sign_out')
@login_required
def sign_out():
    flash(f'See you next time, {current_user.username}')
    logout_user()
    return redirect(url_for('index'))


@app.context_processor
def base():
    form = forms.SearchForm()
    return dict(form=form)


@app.route('/search', methods=['POST'])
@login_required
def search():
    form = forms.SearchForm()
    posts = Entry.query
    if form.validate_on_submit():
        entry_searched = form.searched.data
        posts = posts.filter(Entry.description.like('%' + entry_searched + '%'))
        posts = posts.order_by(Entry.id).all()
    return render_template('search.html',
                           form=form,
                           searched=entry_searched,
                           posts=posts)


if __name__ == "__main__":
    app.run()
