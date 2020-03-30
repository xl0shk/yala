# -*-coding:utf-8-*-
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_simpleldap import LDAP
from flask_apscheduler import APScheduler

db = SQLAlchemy()
ldap = LDAP()
apscheduler = APScheduler()

login_manager = LoginManager()
login_manager.login_view = 'auth.login'


from yalamain.models import AnonymousUser, User
login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
