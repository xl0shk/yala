# -*- coding: utf-8 -*-
import ldap
import os


class Config(object):
    PER_PAGE = 25
    SECRET_KEY = 'Your secret key.'
    UPLOAD_DIR = 'upload'

    LDAP_HOST = 'Your ldap host.'
    LDAP_BASE_DN = 'Your ldap base_dn.'
    LDAP_USERNAME = 'Your ldap username.'
    LDAP_PASSWORD = 'Your ldap password.'
    LDAP_LOGIN_VIEW = 'auth.auth_login'
    LDAP_CUSTOM_OPTIONS = {ldap.OPT_REFERRALS: 0}

    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    SQLALCHEMY_POOL_RECYCLE = 3600

    ACCESS_KEY_ID = "Your aliyun access_key_id"
    ACCESS_KEY_SECRET = "Your aliyun access_key_secret"

    SCHEDULER_API_ENABLED = True

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://test:test@127.0.0.1:3306/test'
    SQLALCHEMY_BINDS = {
    }

    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    INFO_LOG_PATH = os.path.join(BASE_DIR, 'logs/yala.log')
    ERROR_LOG_PATH = os.path.join(BASE_DIR, 'logs/yala_error.log')


class TestingConfig(Config):
    """
    :目前没有使用到测试环境
    """
    pass


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = ''
    SQLALCHEMY_BINDS = {
    }

    INFO_LOG_PATH = 'Your production env info log path.'
    ERROR_LOG_PATH = 'Your production env error log path.'


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}
