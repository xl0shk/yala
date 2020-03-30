# -*- coding: utf-8 -*-
import os
import logging
from flask import Flask, g, session, request
from logging.handlers import TimedRotatingFileHandler

from yalamain.config import config
from yalamain.extensions import db, ldap, login_manager, apscheduler

from yalamain.blueprints.api_assets import api_assets_bp
from yalamain.blueprints.api_user import api_user_bp
from yalamain.blueprints.api_monitor import api_monitor_bp
from yalamain.blueprints.api_v2 import api_v2_bp
from yalamain.blueprints.assets import assets_bp
from yalamain.blueprints.user import user_bp
from yalamain.blueprints.monitor import monitor_bp
from yalamain.blueprints.index import index_bp
from yalamain.blueprints.auth import auth_bp
from yalamain.cron.cornlog import update_cron_log


def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('YALA_CONFIG', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])
    app.config['JSON_AS_ASCII'] = False

    register_logging(app)
    register_blueprints(app)
    register_extensions(app)
    register_hooks(app)

    return app


def register_extensions(app):
    ldap.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    apscheduler.init_app(app)
    apscheduler.start()


def register_blueprints(app):
    app.register_blueprint(api_assets_bp, url_prefix='/api/assets')
    app.register_blueprint(api_user_bp, url_prefix='/api/user')
    app.register_blueprint(api_monitor_bp, url_prefix='/api/monitor')
    app.register_blueprint(api_v2_bp, url_prefix='/api/v2')
    app.register_blueprint(assets_bp, url_prefix='/assets')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(monitor_bp, url_prefix='/monitor')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(index_bp, url_prefix='/')


def register_hooks(app):
    @app.before_request
    def before_request():
        g.user = None
        if 'user_id' in session:
            g.user = {}
            g.ldap_groups = ldap.get_user_groups(user=session['user_id'])


def register_logging(app):
    formatter = logging.Formatter('%(asctime)s - %(thread)s - %(levelname)s - %(funcName)s - %(message)s')

    file_handler_info = TimedRotatingFileHandler(app.config.get('INFO_LOG_PATH'), when="midnight", backupCount=10, encoding='UTF-8')
    file_handler_info.setFormatter(formatter)
    file_handler_info.setLevel(logging.INFO)
    app.logger.addHandler(file_handler_info)
    app.logger.setLevel(logging.INFO)
