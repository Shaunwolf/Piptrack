import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import generate_csrf
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

from runtime_env import ON_VERCEL, database_url

# Configure logging
logging.basicConfig(level=logging.INFO)

class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
if ON_VERCEL and "SESSION_SECRET" not in os.environ:
    logging.warning("SESSION_SECRET is not set: logins use an insecure default key. Set it in the Vercel project settings.")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database configuration
# Postgres in production; a local SQLite file when DATABASE_URL is unset (in /tmp on Vercel,
# where it is wiped whenever the function restarts, so add a Postgres database there)
app.config["SQLALCHEMY_DATABASE_URI"] = database_url()
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize extensions with app
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Please log in to access this page."

# Make csrf_token() available in templates that don't use a FlaskForm
app.jinja_env.globals['csrf_token'] = generate_csrf

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Create database tables
with app.app_context():
    import models  # Import models to register them
    db.create_all()
    logging.info("Database tables initialized")