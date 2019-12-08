from forms import LoginForm, RegistrationForm
from models import db, login_manager, login_required, User
from flask import Blueprint, flash, get_flashed_messages, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

# Blueprint that will register 'auth' or authentication routes
# Routes that will require user authentication or depend on
# user authentication
auth = Blueprint('auth', __name__, template_folder='templates')

# Handles the login of users
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('common.index'))

    form = LoginForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            # Queries datebase to make sure a user with that email exists
            # then checks hashed password from field against User object
            # password_hash
            user = User.query.filter_by(email=form.email.data).first()

            if user is None or not user.check_password(form.password.data):
                flash('Invalid Credentials.', category='failure')
                return redirect(url_for('auth.login'))

            login_user(user)

            if user.user_type == 'student':
                return redirect(url_for('auth.student_dashboard'))
            elif user.user_type == 'teacher':
                return redirect(url_for('auth.teacher_dashboard'))

    return render_template('login.html', form=form, title='Login')

# Handles the registrations of users
@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            # Query database for existing user if this query returns a user then
            # let the user know an account with that email exists and give them
            # the option to login
            # Otherwise create a user and store them in the database.
            user_exists = User.query.filter(
                User.email == form.email.data).first()

            if user_exists:
                flash('A user with that email already exists', category='failure')
                return redirect(url_for('auth.register'))

            hashed_pass = generate_password_hash(form.password.data)
            new_user = User(name=form.name.data,
                            email=form.email.data,
                            password_hash=hashed_pass,
                            user_type=request.form['user_type'])

            db.session.add(new_user)
            db.session.commit()

            flash('User account created successfully!', category='success')
            return redirect(url_for('auth.login'))

    return render_template('register.html', form=form, title='Register')

# Handles the logout of users
@auth.route('/logout')
@login_required(role="ANY")
def logout():
    logout_user()
    return redirect(url_for('common.index'))

# The route for student dashboard
# See logic/models.py for more infor on @login_required decorator
@auth.route('/student_dashboard')
@login_required(role='student')
def student_dashboard():
    return render_template('base_dashboard.html', title='Student Dashboard')

# The route for teacher dashboard
# See logic/models.py for more infor on @login_required decorator
@auth.route('/teacher_dashboard')
@login_required(role='teacher')
def teacher_dashboard():
    return render_template('base_dashboard.html', title='Teacher Dashboard')
