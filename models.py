from app import db, login_manager
from flask_login import UserMixin, current_user
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash

# Python abstraction of the Users table that extends the UserMixin class for
# user authentication


class User(db.Model, UserMixin):
    __tablename__ = 'Users'
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(150), nullable=False, unique=True)
    user_type = db.Column(db.Enum('teacher', 'student'))
    #classes = db.relationship('Classes', backref='users', lazy=True)
    #enrollments = db.relationship('Enrollment', backref='users', lazy=True)

    def check_password(self, cleartext):
        if check_password_hash(self.password_hash, cleartext):
            return True
        else:
            return False

    def get_id(self):
        return self.user_id

    def get_user_type(self):
        return self.user_type
    
    def __repr__(self):
        return "(ID {user_id}) {user_type} | {name}".format(
            user_id=self.user_id, 
            name=self.name,
            user_type=self.user_type
        )

# function responsible for handling the user during the current
# session. Handles the logging in and out of users
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# Defined a custom user login_required decorator
# to implement roles for the applications
# ie restricting dashboards based on user type


def login_required(role="ANY"):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated:
                return login_manager.unauthorized()

            user_type = current_user.get_user_type()
            if ((user_type != role) and (role != "ANY")):
                return login_manager.unauthorized()
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper


class Classes(db.Model):
    """Flask SQLAlchemy class representing Classes table in database"""
    __tablename__ = 'Classes'
    class_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    section = db.Column(db.String(50), nullable=False)
    attendance_code = db.Column(db.String(50), nullable=True)
    enrollment_code = db.Column(db.String(50), nullable=False)
    professor_id = db.Column(db.Integer, db.ForeignKey(
        'Users.user_id'), nullable=False)
    #enrollments = db.relationship('Enrollment', backref='classes', lazy=True)

    def get_id(self):
        return self.class_id

    def get_name(self):
        return self.name

    def get_section(self):
        return self.section

    def get_enrollment_code(self):
        return self.enrollment_code

    def get_attendance_code(self):
        return self.attendance_code
    
    def __repr__(self):
        return "(ID {user_id}) {name}".format(
            user_id=self.class_id, 
            name=self.name
        )

class Enrollment(db.Model):
    """Flask SQLAlchemy class representing Enrollment table in database"""
    __tablename__ = 'Enrollment'
    class_id = db.Column(db.Integer, db.ForeignKey(
        'Classes.class_id'), nullable=False, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(
        'Users.user_id'), nullable=False, primary_key=True)
    dropped = db.Column(db.Boolean, nullable=False, default=False)

    def get_class_id(self):
        return self.class_id

    def get_user_id(self):
        return self.user_id
    
    def __repr__(self):
        linked_class = Classes.query.get(self.class_id)
        student = User.query.get(self.user_id)
        return "Class: {linked_class} | Student: {student}".format(
            linked_class=linked_class, 
            student=student
        )


class Attendance(db.Model):
    """Flask SQLAlchemy class representing Attendance table in database"""
    __tablename__ = 'Attendance'
    class_id = db.Column(db.Integer, db.ForeignKey(
        'Classes.class_id'), nullable=False, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(
        'Users.user_id'), nullable=False, primary_key=True)
    date = db.Column(db.Date, default=db.func.now(),
                     nullable=False, primary_key=True)

    def get_id(self):
        return self.class_id + self.user_id + self.date
    
    def __repr__(self):
        linked_class = Classes.query.get(self.class_id)
        student = User.query.get(self.user_id)
        return "Class: {linked_class} | Student: {student} | Date: {date}".format(
            linked_class=linked_class, 
            student=student,
            date = self.date
        )
