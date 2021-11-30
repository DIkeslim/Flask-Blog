from flask import Flask, render_template, flash, request, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, SearchField, BooleanField, ValidationError
from wtforms.validators import DataRequired, EqualTo, Length
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
from wtforms.widgets import TextArea
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user



#create a flask instance
app = Flask(__name__)

#Add a database
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///users.db'

#Secret key
app.config["SECRET_KEY"] = "My super Secret key"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

#Initialize the database
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#flask login stuff
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

#create search form
class SearchForm(FlaskForm):
    searched = StringField("Searched", validators=[DataRequired()])
    submit = SubmitField("Submit")

#Pass stuff to navbar
@app.context_processor
def base():
    form = SearchForm()
    return dict(form=form)


#Create Search function
@app.route('/search', methods=["POST"])
def search():
    form = SearchForm()
    posts = Posts.query
    if form.validate_on_submit():
        #Get data from submitted form
        post.searched = form.searched.data
        #Query the database
        posts = posts.filter(Posts.content.like('%' + post.searched + '%'))
        posts = posts.order_by(Posts.title).all()
        return render_template("search.html", form=form,
                               searched = post.searched,
                               posts = posts)


#create Loginform
class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("password", validators=[DataRequired()])
    submit = SubmitField("Submit")

#create login page
@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        if user:
            #check the hash
            if check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                flash("Login Successful")
                return redirect(url_for('dashboard'))
            else:
                flash("wrong password-try again")
        else:
            flash("That user doesnt exist try again")
    return render_template('login.html', form=form )

#create logout page
@app.route('/logout', methods=['GET','POST'])
@login_required
def logout():
    logout_user()
    flash("You have been logged out!")
    return redirect(url_for('login'))


#create dashboard page
@app.route('/dashboard', methods=['GET','POST'])
@login_required
def dashboard():
    form = UserForm()
    id = current_user.id
    name_to_update = Users.query.get_or_404(id)
    if request.method == "POST":
        name_to_update.name = request.form['name']
        name_to_update.email = request.form['email']
        name_to_update.favorite_color = request.form['favorite_color']
        name_to_update.username = request.form['username']
        try:
            db.session.commit()
            flash("User updated Successfully")
            return render_template("dashboard.html",
                                   form=form,
                                   name_to_update=name_to_update)
        except:
            db.session.commit()
            flash("Error! looks like there was")
            return render_template("dashboard.html",
                                   form=form,
                                   name_to_update=name_to_update)
    else:
        return render_template("dashboard.html",
                               form=form,
                               name_to_update=name_to_update,
                               id=id)

    return render_template('dashboard.html')




#create a Blog Post Model
class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    content = db.Column(db.Text)
    #author = db.Column(db.String(255))
    date_posted = db.Column(db.DateTime, default=datetime.utcnow())
    slug = db.Column(db.String(255))
    #Foreign key to link users (refer to the primary key of the user)
    poster_id = db.Column(db.Integer, db.ForeignKey("users.id"))

#Create a Posts form
class PostForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    content = StringField("Content", validators=[DataRequired()], widget=TextArea())
    author = StringField("Author")
    slug = StringField("Slug", validators=[DataRequired()])
    submit = SubmitField("Submit", validators=[DataRequired()])

@app.route('/posts/delete/<int:id>')
@login_required
def delete_post(id):
    post_to_delete = Posts.query.get_or_404(id)



    try:
        db.session.delete(post_to_delete)
        db.session.commit()

        #Return a message
        flash("Blog Post was deleted")
        # Grab all the Posts from the database
        posts = Posts.query.order_by(Posts.date_posted)
        return render_template("posts.html", posts=posts)

    except:
        flash("there was a problem deleting post try agaain")

        # Grab all the Posts from the database
        posts = Posts.query.order_by(Posts.date_posted)
        return render_template("posts.html", posts=posts)


@app.route('/posts')
def posts():
    #Grab all the Posts from the database
    posts = Posts.query.order_by(Posts.date_posted)
    return render_template("posts.html", posts=posts)

@app.route('/posts/<int:id>')
def post(id):
    post = Posts.query.get_or_404(id)
    return render_template('post.html', post=post)

@app.route('/posts/edit/<int:id>', methods=['GET','POST'])
@login_required
def edit_post(id):
    post = Posts.query.get_or_404(id)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        #post.author = form.author.data
        post.slug = form.slug.data
        post.content = form.content.data
        #update Database
        db.session.add(post)
        db.session.commit()
        flash("Post has been updated")
        return redirect(url_for('post', id=post.id))

    form.title.data = post.title
    #form.author.data = post.author
    form.slug.data = post.slug
    form.content.data = post.content
    return render_template('edit_post.html', form=form)

#Add Post page
@app.route('/add-post', methods=['GET','POST'])
def add_post():
    form = PostForm()

    if form.validate_on_submit():
        poster = current_user.id
        post = Posts(title=form.title.data, content=form.content.data, poster_id=poster, slug=form.slug.data)
        #clear the form
        form.title.data = ''
        #form.content.data = ''
        form.slug.data = ''

       #Add post data to database
        db.session.add(post)
        db.session.commit()

        flash("Blog Post submitted successfully")
        #redirect to the webpage
    return render_template("add_post.html", form=form)

#json thing
@app.route('/date')
def get_current_date():
    favorite_pizza = {
        "John" : "Pepperoni",
        "Mary" : "cheese",
        "Tim" : "Mushrooms"
    }
    return favorite_pizza
    #return {"Date": date.today()}




#create model
class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False, unique=True)
    favorite_color = db.Column(db.String(120))
    date_added = db.Column(db.DateTime, default=datetime.utcnow())

    #Do some password stuff
    password_hash = db.Column(db.String(128))
    #User can have many posts
    posts = db.relationship('Posts', backref='poster')

    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
         return check_password_hash(self.password_hash, password)

    #create a string
    def __repr__(self):
        return '<Name %r>' % self.name

@app.route('/delete/<int:id>')
def delete(id):
    global our_users
    user_to_delete = Users.query.get_or_404(id)
    name = None
    form = UserForm()

    try:
        db.session.delete(user_to_delete)
        db.session.commit()
        flash("User Deleted Successfully")

        our_users = Users.query.order_by(Users.date_added)
        return render_template("add_user.html",
                           form=form,
                           name=name,
                           our_users=our_users
                           )
    except:
        flash("Whoops, there was a problem deleting user..try again")
        return render_template("add_user.html",
                               form=form,
                               name=name,
                               our_users=our_users
                               )


#Create a form class
class UserForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    favorite_color = StringField("Favorite Color")
    password_hash = PasswordField('Password', validators=[DataRequired(), EqualTo('password_hash2', message='Passwords Must Match')])
    password_hash2 = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField("Submit")


#update database record
@app.route('/update/<int:id>', methods=['GET','POST'])
@login_required
def update(id):
    form = UserForm()
    name_to_update  = Users.query.get_or_404(id)
    if request.method == "POST":
        name_to_update.name = request.form['name']
        name_to_update.email = request.form['email']
        name_to_update.favorite_color = request.form['favorite_color']
        name_to_update.username = request.form['username']
        try:
            db.session.commit()
            flash("User updated Successfully")
            return render_template("update.html",
                                   form = form,
                                   name_to_update = name_to_update)
        except:
            db.session.commit()
            flash("Error! looks like there was")
            return render_template("update.html",
                                   form=form,
            name_to_update = name_to_update)
    else:
        return render_template("update.html",
                               form=form,
                               name_to_update = name_to_update,
                               id = id)


class PasswordForm(FlaskForm):
    email = StringField('Whats your Email', validators=[DataRequired()])
    password_hash = PasswordField('Whats your Password', validators=[DataRequired()])
    submit = SubmitField("Submit")


#Create a form class
class NamerForm(FlaskForm):
    name = StringField('Whats your name', validators=[DataRequired()])
    submit = SubmitField("Submit")




@app.route('/user/add', methods=['GET', 'POST'])
def add_user():
    name = None
    form = UserForm()
    #print(form.email)
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user is None:
            #hash the password
            hashed_pw = generate_password_hash(form.password_hash.data, "sha256")
            user = Users(username=form.username.data,name=form.name.data, email=form.email.data,
                         favorite_color=form.favorite_color.data, password_hash=hashed_pw)
            db.session.add(user)
            db.session.commit()
        name = form.name.data
        form.name.data = ''
        form.username.data = ''
        form.email.data = ''
        form.favorite_color.data = ''
        form.password_hash = ''
        flash("User Added Successfully!")
    our_users = Users.query.order_by(Users.date_added)
    return render_template("add_user.html",
                           form=form,
                           name=name,
                           our_users=our_users
                           )

@app.route("/")
def index():
    return render_template("base.html")


@app.route("/user/<name>")
def user(name):
    return render_template("user.html", name=name)

#create custom error pages

#invalid url
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

#internal server error
@app.errorhandler(500)
def page_not_found(e):
    return render_template("500.html"), 500

#Create Password Test Page
@app.route("/test_pw", methods=["GET","POST"])
def test_pw():
    email = None
    password = None
    pw_to_check = None
    passed = None
    form = PasswordForm()
    #validate form
    if form.validate_on_submit():
        email = form.email.data
        password = form.password_hash.data
        form.email.data = ""
        form.password_hash.data = ''

        #Look up user by email address
        pw_to_check = Users.query.filter_by(email=email).first()

        #check hashed password
        passed = check_password_hash(pw_to_check.password_hash, password)
        #flash("Form Submitted Successfully!")
    return render_template("test_pw.html",
                           email = email,
                           password = password,
                           pw_to_check = pw_to_check,
                           passed = passed,
                           form = form)


#Create Name Page
@app.route("/name", methods=["GET","POST"])
def name():
    name = None
    form = NamerForm()

    #validate form
    if form.validate_on_submit():
        name = form.name.data
        form.name.data = ""
        flash("Form Submitted Successfully!")
    return render_template("name.html",
                           name = name,
                           form = form)


#to run flask on a server
if __name__ == '__main__':
    app.run(debug=True)



