# -*- coding: utf-8 -*-
from flask import Blueprint
from flask import abort, url_for, g, jsonify, current_app
from functools import wraps
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth, MultiAuth
from sqlalchemy.exc import SQLAlchemyError

from yalamain.models import Host, IPPool, User, AnonymousUser


basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth('Bearer')
multi_auth = MultiAuth(basic_auth, token_auth)

api_v2_bp = Blueprint('api_v2', __name__)


@basic_auth.verify_password
def verify_password(token_or_username, password):
    """
    :basic_auth verify_password
    """
    if not token_or_username:
        g.current_user = AnonymousUser()
        return True

    if not password:
        g.current_user = User.verify_auth_token(token_or_username)
        g.token_used = True
        return g.current_user is not None

    try:
        user = User.query.filter_by(name=token_or_username).first()
    except SQLAlchemyError as sql_err:
        current_app.logger.error(sql_err)
        return False
    else:
        if not user:
            return False

        g.current_user = user
        g.token_used = False

        return user.verify_password(password)


@token_auth.verify_token
def verify_token(token):
    """
    :token_auth verify_token
    """
    g.current_user = None
    g.current_user_role = None
    try:
        data = User.get_auth_token_data(token)
    except Exception as err:
        current_app.logger.error(err)
        return False
    if data is not None:
        if 'username' in data and 'role' in data:
            g.current_user = data['username']
            g.current_user_role = data['role']
            return User.query.get(data['id'])
    return False


@token_auth.error_handler
def token_auth_failed():
    return jsonify({'resCode': '403', 'resMsg': 'token auth failed.'}), 403


def roles_required(*roles):
    """Decorator which specifies that a user must have at least one of the
    specified roles. Example::

        @app.route('/create_post')
        @roles_accepted('editor', 'author')
        def create_post():
            return 'Create Post'

    The current user must have either the `editor` role or `author` role in
    order to view the page.

    :param args: The possible roles.
    """

    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if g.current_user_role not in roles:
                return forbidden('unauthorized to access to this api')
            return fn(*args, **kwargs)

        return decorated_view

    return wrapper


@token_auth.error_handler
def token_auth_failed():
    return jsonify({'code': '403', 'msg': 'token认证失败'}), 403


@basic_auth.error_handler
def auth_error():
    return unauthorized('Invalid credentials')


def page_not_found(e):
    response = jsonify({'error': 'not found'})
    response.status_code = 404
    return response


def forbidden(message):
    response = jsonify({'error': 'forbidden', 'message': message})
    response.status_code = 403
    return response


def unauthorized(message):
    response = jsonify({'error': 'unauthorized', 'message': message})
    response.status_code = 401
    return response


@api_v2_bp.route('/token', methods=['GET'])
@basic_auth.login_required
def api_v2_token():
    """
    TODO：后续用户登录成功后，直接返回token信息.
    """
    if g.current_user.is_anonymous or g.token_used:
        return unauthorized('Invalid credentials')
    token = g.current_user.generate_auth_token(expiration=3600)
    return jsonify({
        'token': token.decode('utf-8'),
        'expiration': 3600
    })


@api_v2_bp.route('/assets/host/list', methods=['GET'])
@basic_auth.login_required
def api_v2_assets_host_list():
    """
    :获取主机列表
    """
    host_list = []

    if g.current_user.is_anonymous or g.token_used:
        return unauthorized('Invalid Credentials.')

    try:
        hosts = Host.query.all()
    except SQLAlchemyError as err:
        current_app.logger.error(err)
        return jsonify({
            'resCode': -1,
            'errMsg': 'Query Error.',
        })
    except Exception as err:
        current_app.logger.error(err)
        return jsonify({
            'result': -1,
            'errMsg': 'Other Error.',
        })

    if hosts is None:
        abort(404)
    else:
        try:
            for host in hosts:
                try:
                    ippool = IPPool.query.get(host.innerIP)
                    # TODO：针对每个innerIP进行查询，会存在性能问题，待优化.
                except SQLAlchemyError as err:
                    current_app.logger.error(err)
                    ippool = None
                except Exception as err:
                    current_app.logger.error(err)
                    ippool = None

                host_list.append({
                    'url': url_for('api.get_host', host_id=host.id, _external=True),
                    'innerIP': ippool.IP if ippool is not None else '',
                    'outerIP': host.outerIP,
                    'elasticIP': host.elasticIP,
                    'hostname': host.hostname,
                    'cpu': host.cpu,
                    'memory': host.memory,
                    'disk': host.disk,
                    'os': host.os,
                    'device': host.device.type if host.device is not None else '',
                    'use_dpt': host.user_dpt.name if host.user_dpt is not None else '',
                    'user': host.users.fullname if host.users is not None else '',
                    'owner_dpt': host.owner_dpt.name if host.owner_dpt is not None else '',
                    'operator': host.operator.name if host.operator is not None else '',
                    'host_model': host.host_model,
                    'service': host.service.name if host.service is not None else '',
                    'cabinet': host.cabinet.code if host.cabinet is not None else '',
                    'create_date': host.create_date,
                    'payment': host.payment,
                    'host_status': host.status,
                    'comment': host.comment,
                })
            return jsonify({
                'resCode': 1,
                'resData': host_list
            })
        except Exception as err:
            return jsonify({
                'resCode': -1,
                'errMsg': str(err),
            })


@api_v2_bp.route('/assets/host/<int:host_id>', methods=['GET'])
@token_auth.login_required
@roles_required('Admin', 'Ops')
def api_v2_assets_host_id(host_id):
    try:
        host = Host.query.get(host_id)
        if host is None:
            abort(404)
        ippool = IPPool.query.get(host.innerIP)
        host_info = {
            'url': url_for('api.get_host', host_id=host.id, _external=True),
            'innerIP': ippool.IP if ippool is not None else '',
            'outerIP': host.outerIP,
            'elasticIP': host.elasticIP,
            'hostname': host.hostname,
            'cpu': host.cpu,
            'memory': host.memory,
            'disk': host.disk,
            'os': host.os,
            'device': host.device.type if host.device is not None else '',
            'use_dpt': host.user_dpt.name if host.user_dpt is not None else '',
            'user': host.users.name if host.users is not None else '',
            'owner_dpt': host.owner_dpt.name if host.owner_dpt is not None else '',
            'operator': host.operator.name if host.operator is not None else '',
            'host_model': host.host_model,
            'service': host.service.name if host.service is not None else '',
            'cabinet': host.cabinet.code if host.cabinet is not None else '',
            'create_date': host.create_date,
            'payment': host.payment,
            'host_status': host.status,
            'comment': host.comment,
        }
        return jsonify({
            'resCode': 1,
            'resData': host_info,
        })
    except Exception as e:
        return jsonify({
            'resCode': -1,
            'errMsg': str(e),
        })
