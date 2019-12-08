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


class Enrollment(db.Model):
    """Flask SQLAlchemy class representing Enrollment table in database"""
    __tablename__ = 'Enrollment'
    class_id = db.Column(db.Integer, db.ForeignKey(
        'Classes.class_id'), nullable=False, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(
        'Users.user_id'), nullable=False, primary_key=True)
    dropped = db.Column(db.Boolean, nullable=False)

    def get_id(self):
        return self.class_id + self.user_id


class Attendance(db.Model):
    """Flask SQLAlchemy class representing Enrollment table in database"""
    __tablename__ = 'Attendance'
    class_id = db.Column(db.Integer, db.ForeignKey(
        'Classes.class_id'), nullable=False, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(
        'Users.user_id'), nullable=False, primary_key=True)
    date = db.Column(db.Date, nullable=False, primary_key=True)

    def get_id(self):
        return self.class_id + self.user_id
