from flask import Flask, render_template, flash, request, redirect, url_for, get_flashed_messages, session
from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, logout_user, current_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField, ValidationError, TextAreaField, FileField, IntegerField
from wtforms.validators import DataRequired, EqualTo, Length
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
from flask_ckeditor import CKEditor, CKEditorField
from wtforms.widgets import TextArea
import uuid as uuid
import os

app = Flask(__name__)

#Old SQLite DB
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"

# Add CKEditor
ckeditor = CKEditor(app)

# Secret Key!
app.config['SECRET_KEY'] = "my super secret key"

# Initialize the Database
UPLOAD_FOLDER = 'static/imeges/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)
# migrate = Migrate(app, db, directory='my_migrations')
migrate = Migrate(app, db)


# Flask_Login Stuff
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

# Pass Stuff To Navbar
@app.context_processor
def base():
    form = SearchForm()
    return dict(form=form)


@app.route('/')
def index():
    return render_template('main.html')

# Create Admin Page
@app.route('/admin')
@login_required
def admin():
    p = Posts.query.order_by(Posts.date_added.desc()).first()

    if p:
        flash("Add a new post")

    id = current_user.id
    if id == 1:
        our_users = Users.query.order_by(Users.date_added)
        return render_template('admin.html', our_users=our_users, post=p)  # Pass 'p' to the template
    else:
        flash("Sorry, you must be the Admin to access the Admin Page")
        return redirect(url_for('dashboard'))

@app.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm()
    posts = Posts.query

    if form.validate_on_submit():
        # Get data from the submitted form
        searched = form.searched.data

        # Query the database
        posts = posts.filter(Posts.title.like('%' + searched + '%'))
        posts = posts.order_by(Posts.content).all()

        return render_template('search.html', form=form, searched=searched, posts=posts)

    # If the form is not submitted or validation fails, render the template without the posts
    return render_template('search.html', form=form)
    
@app.route('/posts/<int:id>')
def post(id):
    post = Posts.query.get_or_404(id)
    return render_template('post.html', post=post)
    

@app.route('/posts')
def posts():
    # Grab all the posts from the database
    posts = Posts.query.order_by(Posts.date_added.desc()).all()
    return render_template("posts.html", posts=posts)


@app.route('/post/delete/<int:id>')
@login_required
def delete_post(id):
    post_to_delete = Posts.query.get_or_404(id)
    id = current_user.id
    if id == post_to_delete.poster.id or id == 1:
        try:
            db.session.delete(post_to_delete)
            db.session.commit()

            # Return a message
            flash("Blog Post Was Deleted!")
            # Grab all the posts from the database
            posts = Posts.query.order_by(Posts.date_added.desc()).all()
            return render_template("posts.html", posts=posts)
        except:
            # Return an error message
            flash("Whoops! There was a problem deleting... Try again!")

            # Grab all the posts from the database
            # posts = Posts.query.order_by(Posts.date_added)
            posts = Posts.query.order_by(Posts.date_added.desc()).all()
            return render_template("posts.html", posts=posts)
    else:
        # Return a message
        flash("You Aren`t Authorized To Delete Thet Post!")

        # Grab all the posts from the database
        posts = Posts.query.order_by(Posts.date_added.desc()).all()
        return render_template("posts.html", posts=posts)
    
@app.route('/post/edit/<int:id>', methods=['POST', 'GET'])
@login_required
def edit_post(id):
    post = Posts.query.get_or_404(id)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data

        # Add To DB
        db.session.add(post)
        db.session.commit()
        flash("Post Has Been Updated")
        return redirect(url_for('post', id=post.id))
    id = current_user.id
    if id == post.user_id or id == 1:
        form.title.data = post.title
        form.content.data = post.content
        return render_template('edit_post.html', form=form)
    else:
        flash("You Aren`t Authorized To Edit Thet Post!")
        post = Posts.query.get_or_404(id)
        return render_template('post.html', post=post)
    
# Add Post Page
@app.route('/add_post', methods=['GET', 'POST'])
def add_post():
    form = PostForm()

    if form.validate_on_submit():
        poster = current_user.id
        post = Posts(title=form.title.data,
                     content=form.content.data,
                     user_id=poster)  # Use 'user_id' instead of 'poster_id'
        # Clear The Form
        form.title.data = ''
        form.content.data = ''

        # Add post data to the database
        db.session.add(post)
        db.session.commit()

        # Return a Message
        flash("Blog Post Submitted Successfully!")

    # Redirect to the webpage
    return render_template('add_post.html', form=form)

@app.route("/delete/<int:id>")
def delete(id):
    if id == id:
        user_to_delete = Users.query.get_or_404(id)
        name = None
        form = UserForm()

        try:
            db.session.delete(user_to_delete)
            db.session.commit()
            flash("User  Deleted Successfully!!")

            our_users = Users.query.order_by(Users.date_added)
            return render_template('add_user.html',
                                    form=form,
                                    name=name,
                                    our_users=our_users)
        except:
            flash("Whoops! There was a problem deleting user, try again...")
            return render_template('add_user.html',
                            form=form,
                            name=name,
                            our_users=our_users)
    else:
        flash("Sorry, you can`t delete this user!")
        return redirect(url_for('dashboard'))


@app.route("/delete_user/<int:id>")
def deleteUser(id):
    if id == current_user.id:
        user_to_delete = Users.query.get_or_404(id)
        name = None
        form = UserForm()

        try:
            db.session.delete(user_to_delete)
            db.session.commit()
            flash("User  Deleted Successfully!!")

            our_users = Users.query.order_by(Users.date_added)
            return render_template('add_user.html',
                                    form=form,
                                    name=name,
                                    our_users=our_users)
        except:
            flash("Whoops! There was a problem deleting user, try again...")
            return render_template('add_user.html',
                            form=form,
                            name=name,
                            our_users=our_users)
    else:
        flash("Sorry, you can`t delete this user!")
        return redirect(url_for('dashboard'))
    
# Update Database Record
@app.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    form = UserForm()
    name_to_update = Users.query.get_or_404(id)
    if request.method == 'POST':
        name_to_update.username = request.form['username']
        name_to_update.email = request.form['email']
        try:
            db.session.commit()
            flash("User Update Successfully!")  
            return render_template('update.html',
                                   form=form,
                                   name_to_update=name_to_update,
                                   id=id)
        except:
            flash("Error! Looks like there was a problem... try again!")    
            return render_template('update.html',
                                   form=form,
                                   name_to_update=name_to_update, 
                                   id=id)
    else:
        flash("Error! Looks like there was a problem... try again!")  
        return render_template('update.html', form=form, 
                               name_to_update=name_to_update, 
                               id=id)
    

# Create Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        if user:
            # Check the hash
            if check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                flash("Login Successfull!")
                return redirect(url_for('dashboard'))
            else:
                flash("Wrong Password!")
        else:
            flash("Thet User Doesn`t Exist!")
    return render_template('login.html', form=form)

# Create Logout Page
@app.route('/logou', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash("You Have Been Logged Out!")
    return redirect(url_for('login'))


# Create Dashboard Page
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    form = UserForm()
    id = current_user.id
    name_to_update = Users.query.get_or_404(id)
    if request.method == 'POST':
        name_to_update.username = request.form['username']
        name_to_update.email = request.form['email']
        
        # Check for pofile pic
        if request.files['profile_pic']:
            name_to_update.profile_pic = request.files['profile_pic']
            # Grab Image Name
            pic_filename = secure_filename(name_to_update.profile_pic.filename)
            # Set UUID
            pic_name = str(uuid.uuid1()) + "_" + pic_filename
            # Save That Image
            saver = request.files['profile_pic']

            # Change it to a string to save to db
            name_to_update.profile_pic = pic_name
            try:
                db.session.commit()
                saver.save(os.path.join(app.config['UPLOAD_FOLDER'], pic_name))
                flash("User Update Successfully!")  
                return render_template('dashboard.html',
                                    form=form,
                                    name_to_update=name_to_update)
            except:
                flash("Error! Looks like there was a problem... try again!")    
                return render_template('dashboard.html',
                                    form=form,
                                    name_to_update=name_to_update)
        else:
            db.session.commit()
            flash("User Update Successfully!")  
            return render_template('dashboard.html',
                                form=form,
                                name_to_update=name_to_update)
    else:
        flash("Error! Looks like there was a problem... try again!")  
        return render_template('dashboard.html',
                        form=form,
                        name_to_update=name_to_update,
                        id=id)
    # return render_template('dashboard.html')


@app.route('/registration', methods=["GET", "POST"])
def registration():
    username = None
    form = UserForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user is None:
            # Hash the password!
            hashed_pw = generate_password_hash(form.password_hash.data, "sha256")
            user = Users(username=form.username.data, 
                         email= form.email.data, 
                         password_hash=hashed_pw)
            db.session.add(user)
            db.session.commit()
        username = form.username.data
        form.username.data = ''
        form.email.data = ''
        form.password_hash = ''
        flash('Welcome in PostApp ')
        return redirect(url_for('login'))
    our_users = Users.query.order_by(Users.date_added)
    return render_template('add_user.html',
                           form=form,
                           username=username,
                           our_users=our_users)


#INVALID URL
@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

#Internal Server Error
@app.errorhandler(500)
def page_not_found(error):
    return render_template('500.html'), 500


#########################      MODEL DB     #################################### 

# Create Model
class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    date_added =db.Column(db.DateTime, default=datetime.utcnow)
    profile_pic = db.Column(db.String(), nullable=True)
    # Do some password stuff!
    password_hash = db.Column(db.String(128))
    # User Can Have Many Posts
    posts = db.relationship('Posts', backref='poster')


    @property
    def password(self):
        raise AttributeError('passwod is not a readable!')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)


    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)   

    # Create a String
    def __repr__(self):
        return '<Name %r>' % self.name
    
# Create Model
class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    content = db.Column(db.Text)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # Create a String
    def __repr__(self):
        return '<Post %r>' % self.id
        
# with app.app_context():
#     # Create DB
#     db.create_all()

    
###############################################################################################


###########################       FORMS      ##################################################
# Create a Form Class
class UserForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    password_hash = PasswordField('Password', validators=[DataRequired(), EqualTo('password_hash2', message='Password Must Match!')])
    password_hash2 = PasswordField('Confirm Password', validators=[DataRequired()])
    profile_pic = FileField("Profile Pic")
    submit = SubmitField("Submit")

    def validate_username(self, field):
        user = Users.query.filter_by(username=field.data).first()
        if user:
            raise ValidationError(flash('Username already exists. Please choose a different username.'))
        
    def validate_email(self, field):
        user = Users.query.filter_by(email=field.data).first()
        if user:
            raise ValidationError(flash('Email already exists. Please choose a different username.'))
        
# Create a Posts Form
class PostForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    content = StringField("Content", validators=[DataRequired()], widget=TextArea())
    submit = SubmitField("Submit")


# Create Login Form
class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password =PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Submit")

# # Create A Search Form
# class SearchForm(FlaskForm):
#     searched = StringField("Searched", validators=[DataRequired()])
#     submit = SubmitField("Submit")

class SearchForm(FlaskForm):
    searched = StringField("Searched", validators=[DataRequired()])
    search_by_id = IntegerField("Search by ID")
    submit = SubmitField("Submit")


########################################################################################################


if __name__ == '__main__':
    app.run(debug=True)