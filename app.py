import os
import requests
from flask import Flask, render_template, request, flash, redirect, url_for, g, jsonify
from models import db, connect_db, User, FavoriteMovie
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user, LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from forms import EditProfileForm
from flask_debugtoolbar import DebugToolbarExtension

##############################################################################
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = (os.environ.get(DATABASE_URL, 'postgresql://movies_ko3c_user:WZCR47o2I8LnTbLYCrCkrnMEDGG8qeEq@dpg-cpadmusf7o1s73afa9k0-a.oregon-postgres.render.com/movies_ko3c')
migrate = Migrate(app, db)

app.config['DEBUG'] = False
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
toolbar = DebugToolbarExtension(app)


login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))



connect_db(app)
##############################################################################




##############################################################################
## Routes for Movie App

@app.route('/', methods=['GET', 'POST'])
@login_required
def home():

    return render_template("home.html", user=current_user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()

        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('home'))
            else: 
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template('login.html', user=current_user)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        username = request.form.get('username')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(email=email).first()

        if user:
            flash('Email already exists.', category='error')
        elif len(email) < 9:
            flash('Email must be greater than 8 characters.', category='error')
        elif len(first_name) < 3:
            flash('First name must be greater than 2 characters.', category='error')
        elif len(username) < 5:
            flash('Username must be greater than 4 character.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 6 characters.', category='error')
        else:
            new_user = User(email=email, first_name=first_name, username=username, password=generate_password_hash(
                password1, method='sha256'))
            
            db.session.add(new_user)
            db.session.commit()

            login_user(new_user, remember=True)
            flash('Account created!', category='success')
            return redirect(url_for('home'))

    return render_template("sign_up.html", user=current_user)

@app.route('/favorite')
@login_required
def favorite_page():
    return render_template('favorite.html', user=current_user)

@app.route('/favorites', methods=['POST'])
def add_favorite_movie():
    movie_id = request.json.get('movie_id')
    user_id = current_user.id
    favorite_movie = FavoriteMovie(movie_id=movie_id, user_id=user_id)
    db.session.add(favorite_movie)
    db.session.commit()
    return jsonify({'message': 'Favorite movie added successfully'})

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal Server Error"}), 500

@app.route('/favorites', methods=['GET'])
@login_required
def get_favorite_movies():
    favorite_movies = FavoriteMovie.query.filter_by(user_id=current_user.id).all()
    movie_ids = [fav.movie_id for fav in favorite_movies]
    return jsonify(movie_ids)
@app.route('/details')
@login_required
def profile():

    return render_template('details.html', user=current_user)

@app.route('/edit', methods=["GET", "POST"])
@login_required
def edit():
    """Update profile for current user."""
    form = EditProfileForm(obj=current_user)
    if form.validate_on_submit():
        if check_password_hash(current_user.password, form.password.data):
            current_user.username = form.username.data
            current_user.email = form.email.data
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
        else:
            flash('Invalid password.', 'danger')
    return render_template('edit.html', form=form, user=current_user)
    #if not current_user:
        #flash('User ID not found in session.', 'danger')
        #return redirect('/')
    
    #user = current_user
    #form = EditProfileForm(obj=user)
    
    #if form.validate_on_submit():
        #if User.authenticate(user.username, form.password.data):
            #user.username = form.username.data
            #user.email = form.email.data
        
            #db.session.commit()
            #return redirect(f'/home{user.id}')
        
        #flash('Invaild Password', 'danger')
        
    
    #return render_template('edit.html', form=form, user=current_user)

##############################################################################
# Turn off all caching in Flask

@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req


