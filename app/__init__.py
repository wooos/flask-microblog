import os
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
from email.utils import formataddr
from flask import Flask, current_app, request
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_babel import Babel
from flask_babel import lazy_gettext as _l
from elasticsearch import Elasticsearch
from redis import Redis
import rq


db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'
login.login_message = _l('Please log in to access this page.')
mail = Mail()
bootstrap = Bootstrap()
moment = Moment()
babel = Babel()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    bootstrap.init_app(app)
    moment.init_app(app)
    babel.init_app(app)

    app.elasticsearch = Elasticsearch([app.config['ELASTICSEARCH_URL']]) if app.config['ELASTICSEARCH_URL'] else None
    app.redis = Redis.from_url(app.config['REDIS_URL'])
    app.task_queue = rq.Queue('flask-microblog-tasks', connection=app.redis)

    from app.errors import bp as errors_bp
    from app.auth import bp as auth_bp
    from app.main import bp as main_bp
    from app.api import bp as api_bp

    app.register_blueprint(errors_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    if not app.debug and not app.testing:    
        if app.config['MAIL_SERVER']:
            auth = None
            if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
                auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            secret = None
            if app.config['MAIL_USE_TLS']:
                secret = ()
            mail_handler = SMTPHandler(
                mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                fromaddr=formataddr(('Flask Microblog', app.config['MAIL_USERNAME'])),
                toaddrs=app.config['ADMINS'],
                subject='Flask Microblog Failure',
                credentials=auth,
                secure=secret
            )
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)
        
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler('logs/flask-microblog.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('Flask Microblog startup')

    return app


@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(current_app.config['LANGUAGES'])


from app import models