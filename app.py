from os import environ
from flask import Flask, url_for
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

# connection to database that is accessible by other parts of the application
# mysql_db = Database()

login_manager = LoginManager()

app = Flask(__name__)

# Config for generating form hidden tags
app.config['SECRET_KEY'] = environ.get('SECRET_KEY')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://{username}:{password}@{host}:{port}/{db}".format(
    username=environ.get('MYSQL_USER'),
    password=environ.get('MYSQL_PASSWORD'),
    host=environ.get('MYSQL_HOST'),
    port=3306,
    db=environ.get('MYSQL_DB')
)

db = SQLAlchemy(app)

# Initializes all necessary items for app to function
with app.app_context():
    from auth_routes import auth
    from common_routes import common

    app.register_blueprint(auth)
    app.register_blueprint(common)

    # db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
