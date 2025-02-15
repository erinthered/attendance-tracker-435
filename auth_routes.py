from forms import LoginForm, RegistrationForm
from models import db, login_manager, login_required, User, Classes, Enrollment, Attendance
from flask import Blueprint, flash, get_flashed_messages, redirect, render_template, request, url_for, jsonify
from flask_login import current_user, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
import random
import string
import datetime

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
@auth.route('/student_dashboard', methods=['POST', 'GET'])
@login_required(role='student')
def student_dashboard():
    enrollment_obj = Enrollment.query.filter_by(user_id=current_user.user_id).all()
    classes = [Classes.query.get(enroll.get_class_id()) 
               for enroll in enrollment_obj]
    if request.method == 'POST':
        enrollment_code = request.form['enrollment_code']
        # Add a new enrollment to the Enrollment table
        class_id = Classes.query.filter_by(
            enrollment_code=enrollment_code).first().get_id()
        new_enrollment = Enrollment(
            class_id=class_id,
            user_id=current_user.user_id,
            dropped=False
        )
        db.session.add(new_enrollment)
        db.session.commit()
        flash('Registration Successful!', category='success')
        return redirect(url_for('auth.student_class_page', id=class_id))

    return render_template('student_dashboard.html', title='Student Dashboard', classes=classes)

# The route for teacher dashboard
# See logic/models.py for more infor on @login_required decorator
@auth.route('/teacher_dashboard', methods=['POST', 'GET'])
@login_required(role='teacher')
def teacher_dashboard():
    class_obj = Classes.query.filter_by(
        professor_id=current_user.user_id)

    class_list = []
    for c in class_obj:
        class_info = (c.get_id(), c.get_name(), c.get_section())
        class_list.append(class_info)

    if request.method == 'POST':
        # if add_class is clicked
        # get class name and section, generate registration code, and add a new class to database, redirect
        if 'add_class' in request.form:
            # generate random registration code
            registration_code = get_code()

            # add class to database
            new_class = Classes(
                name=request.form['class_name'],
                section=request.form['class_section'],
                enrollment_code=registration_code,
                professor_id=current_user.user_id
            )
            db.session.add(new_class)
            db.session.commit()

            class_added = Classes.query.filter_by(
                professor_id=current_user.user_id, name=new_class.name, section=new_class.section).first()
            class_id = class_added.get_id()
            return redirect(url_for('auth.teacher_class_page', id=class_id))
        else:
            class_id = request.form[class_id]
            return redirect(url_for('auth.teacher_class_page', id=class_id))
    return render_template('teacher_dashboard.html', title='Teacher Dashboard', class_list=class_list)

# Route for teacher metrics and information for an individual clas
@auth.route('/teacher_class_page/<id>', methods=['GET', 'POST'])
@login_required(role='teacher')
def teacher_class_page(id):
    # Get current class info
    current_class = Classes.query.filter_by(class_id=id).first()
    # Get registration code to display in template
    registration_code = current_class.get_enrollment_code()
    attendance_code = None

    if request.method == 'POST':
        # Generate attendance code button pressed
        if 'gen_code' in request.form:
            if current_class.get_attendance_code():
                # there is already an attendance code, delete it
                current_class.attendance_code = None
                db.session.commit()
            else:
                # there is no code, generate it
                attendance_code = get_code()
                current_class.attendance_code = attendance_code
                db.session.commit()
        if 'del_class' in request.form:
            db.session.delete(current_class)
            db.session.commit()
            return redirect(url_for('auth.teacher_dashboard'))

    return render_template('teacher_class_page.html', current_class=current_class, registration_code=registration_code, attendance_code=attendance_code)


@auth.route('/student_class_page/<id>', methods=['GET', 'POST'])
@login_required(role='student')
def student_class_page(id):
    #query classes and get class info
    current_class = Classes.query.filter_by(class_id=id).first()
    if request.method=="POST": 
    #     if 'enrollment_code' in request.form:
    #         #attendance_code = request.form['enrollment_code']
    #         attendance_code = "RcgesoTWuRKMvHajYgqIjlZnYbThBDgrrRweSvwXWnlNSVAKHA"
    #         # Add a new attendance to the Attendance table
            # new_attendance = Attendance(
            #     class_id=id,
            #     user_id=current_user.user_id,
            #     date=date.today()
            # )
            # db.session.add(new_attendance)
            # db.session.commit()
    #         return redirect(url_for('auth.student_class_page', id=id))
    #     else:
        # Unenroll from a class
        Enrollment.query.filter_by(class_id=id, user_id=current_user.user_id).delete()
        db.session.commit()
        return redirect(url_for('auth.student_dashboard'))
    return render_template('student_class_page.html', current_class=current_class)

@auth.route('/mark_attendance/<id>', methods=['GET'])
@login_required(role='student')
def mark_attendance(id):
    class_id, user_id, date = id, current_user.user_id, datetime.date.today()
    response = {
        'class_id': class_id,
        'user_id': user_id,
        'date': date,
        'already_marked': False
    }
    
    def is_enrolled():
        enroll = Enrollment.query.filter_by(user_id=user_id, class_id=id, dropped=False).all()
        if enroll:
            return True
        return False
    if not is_enrolled():
        response['success'] = False
        return jsonify(response)
        
    if not Attendance.query.filter_by(
        class_id=class_id, user_id=user_id, date=date).all():
        
        new_attendance = Attendance(
            class_id=id,
            user_id=current_user.user_id,
            date=datetime.date.today()
        )
        db.session.add(new_attendance)
        db.session.commit()
        response['success'] = True
    else:
        response['success'] = True
        response['already_marked'] = True
    return jsonify(response)
        

# generate random registration or attendance code: helper_code
def get_code():
    code = ""
    for i in range(50):
        code += (random.choice(string.ascii_letters))
    code = check_unique_code(code)
    return code

# check for unique registration code when generating


def check_unique_code(code):
    duplicate = Classes.query.filter_by(enrollment_code=code).first()
    while duplicate:
        code = get_code()
        duplicate = Classes.query.filter_by(enrollment_code=new_code).first()
    return code


def validate_registration(code):
    valid_class = Classes.query.filter_by(enrollment_code=code).first()
    if not valid_class:
        return None
