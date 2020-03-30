# -*- coding: utf-8 -*-
from flask import Blueprint
from flask import render_template, redirect, url_for, request, jsonify, current_app
from flask_login import login_required
from sqlalchemy import exc, or_, exists, not_
import uuid
import json

from yalamain.models import User, Role, Permission, role_permission
from yalamain.extensions import db

api_user_bp = Blueprint('api_user', __name__)


@api_user_bp.route('/user', methods=['POST', 'PUT', 'DELETE'])
@login_required
def api_user_user():
    if request.method == 'POST':
        role_id = request.form.get('role_id', '')
        username = request.form.get('username', '')
        fullname = request.form.get('fullname', '')
        password = request.form.get('password', '')
        email = request.form.get('email', '')

        if role_id == '' or username == '' or password == '' or email == '':
            return jsonify({
                'resCode': -1,
                'errMsg': u'提交的数据不全，请检查！',
            })

        # 判断用户是否已经存在
        try:
            is_exists = User.query.filter_by(name=username, email=email).first()
        except exc.SQLAlchemyError as sql_err:
            current_app.logger.error(sql_err)
            return jsonify({
                'resCode': -1,
                'errMsg': u'Query Error.',
            })
        except Exception as e:
            current_app.logger.error(e)
            return jsonify({
                'result': -1,
                'errMsg': str(e),
            })

        if is_exists:
            return jsonify({
                'resCode': -1,
                'errMsg': u'用户已存在!',
            })

        try:
            u = User()
            u.name = username
            u.fullname = fullname if fullname is not None else None
            u.password = password
            u.email = email
            u.status = True
            u.role_id = role_id
            # TODO: token是之前的设计，暂没有使用到，暂且保留，后续有时间统一处理掉
            u.token = str(uuid.uuid3(uuid.NAMESPACE_DNS, email))
            db.session.add(u)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify({
                'resCode': -1,
                'errMsg': str(e),
            })
        else:
            db.session.commit()
            return jsonify({
                'resCode': 1,
                'resData': u'添加成功!'
            })

    if request.method == 'PUT':
        role_id = request.form.get('role_id', '')
        user_id = request.form.get('user_id', '')
        username = request.form.get('username', '')
        fullname = request.form.get('fullname', '')
        email = request.form.get('email', '')

        if role_id == '' or username == '' or user_id == '' or email == '' or fullname == '':
            return jsonify({
                'resCode': -1,
                'errMsg': u'提交的数据不全，请检查！',
            })
        try:
            # 这个查询是为防止不修改造成数据库写入
            user = User.query.filter_by(id=user_id, name=username, fullname=fullname, email=email, role_id=role_id).first()

            # 如果有数据修改
            if user is None:
                u = User.query.get(user_id)
                u.name = username
                u.fullname = fullname
                u.email = email
                u.role_id = role_id
                db.session.merge(u)
                return jsonify({
                    'resCode': 1,
                    'resData': u'修改成功!',
                })
            else:
                return jsonify({
                    'resCode': 1,
                    'resData': u'数据未发生修改.',
                })
        except Exception as e:
            current_app.logger.error(e)
            return jsonify({
                'resCode': -1,
                'errMsg': str(e),
            })

    if request.method == 'DELETE':
        user_id = request.form.get('user_id', '')
        if user_id == '':
            return jsonify({
                'resCode': -1,
                'errMsg': '无法删除用户，因为user_id为空.',
            })
        try:
            u = User.query.get(user_id)
            db.session.delete(u)
            db.session.commit()
            return jsonify({
                'resCode': 1,
                'resData': u'删除成功.',
            })
        except Exception as e:
            current_app.logger.error(e)
            return jsonify({
                'resCode': -1,
                'errMsg': str(e),
            })


@api_user_bp.route('/user/list', methods=['GET'])
@login_required
def api_user_user_list():
    """
    :获取所有用户
    """
    try:
        users = User.query.all()
    except exc.SQLAlchemyError as sql_err:
        current_app.logger.error(sql_err)
        return jsonify({
            'resCode': -1,
            'errMsg': 'Query Error.',
        })
    except Exception as err:
        current_app.logger.error(err)
        return jsonify({
            'resCode': -1,
            'errMsg': 'Other Error.',
        })

    try:
        user_all = []
        for u in users:
            user_all.append({
                'id': u.id,
                'name': u.name,
                'fullname': u.fullname,
            })
        return jsonify({
            'resCode': 1,
            'resData': user_all
        })
    except Exception as e:
        current_app.logger.error(e)
        return jsonify({
            'resCode': -1,
            'errMsg': str(e),
        })


@api_user_bp.route('/role/list', methods=['GET'])
@login_required
def api_user_role_list():
    if request.method == 'GET':
        try:
            roles = Role.query.all()
        except exc.SQLAlchemyError as sql_err:
            current_app.logger.error(sql_err)
            roles = None
        except Exception as e:
            current_app.logger.error(e)
            roles = None

        role_list = []
        try:
            for r in roles:
                role_list.append({
                    'role_id': r.id,
                    'role_name': r.name,
                })
            return jsonify({
                'resCode': 1,
                'resData': role_list,
            })
        except Exception as e:
            current_app.logger.error(e)
            return jsonify({
                'resCode': -1,
                'errMsg': str(e),
            })


@api_user_bp.route('/role', methods=['POST', 'PUT', 'DELETE'])
@login_required
def api_user_role():
    if request.method == 'POST':
        role_name = request.form.get('role_name', '')
        if not role_name:
            return jsonify({
                'resCode': -1,
                'errMsg': u'角色增加失败，role_name为空.',
            })
        try:
            r = Role()
            r.name = role_name
            db.session.add(r)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify({
                'resCode': -1,
                'errMsg': str(e),
            })
        else:
            db.session.commit()
            return jsonify({
                'resCode': 1,
                'resData': 'Add Success.',
            })

    if request.method == 'PUT':
        role_id = request.form.get('role_id', '')
        grant_list = request.form.get('grant_list', '')
        if not role_id:
            return jsonify({
                'resCode': -1,
                'errMsg': u'角色权限修改失败，role_id为空.',
            })
        try:
            grant_list_json = json.loads(grant_list)
            r = Role.query.get(role_id)
            permissions = r.permissions.all()
            if permissions:
                for p in permissions:
                    r.permissions.remove(p)
                    db.session.add(r)
            for p_id in grant_list_json:
                p = Permission.query.get(p_id)
                r.permissions.append(p)
                db.session.add(r)
            return jsonify({
                'resCode': 1,
                'resData': 'Modify Success.'
            })
        except Exception as e:
            current_app.logger.error(e)
            return jsonify({
                'resCode': -1,
                'errMsg': str(e),
            })

    if request.method == 'DELETE':
        role_id = request.form.get('role_id', '')
        if not role_id:
            return jsonify({
                'resCode': -1,
                'errMsg': u'删除角色失败，role_id为空.',
            })
        try:
            role = Role.query.get(role_id)
            db.session.delete(role)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify({
                'resCode': -1,
                'errMsg': str(e),
            })
        else:
            db.session.commit()
            return jsonify({
                'resCode': 1,
                'resData': 'Delete Success.',
            })


@api_user_bp.route('/role/permissions', methods=['GET'])
@login_required
def api_user_role_permissions():
    if request.method == 'GET':
        role_id = request.args.get('role_id', '')
        if role_id == '':
            return jsonify({
                'resCode': -1,
                'errMsg': u'获取权限列表失败，role_id为空.',
            })
        try:
            permissions_list = []
            permission_id_list = []
            rp = db.session.query(role_permission).filter_by(role_id=role_id)
            for p in rp:
                permission_id_list.append(p.permission_id)
                permission = Permission.query.get(p.permission_id)
                permissions_list.append({
                    'role_id': role_id,
                    'permission_id': p.permission_id,
                    'permission_name': permission.name,
                    'permission_alias_name': permission.alias_name,
                    'permission_rw': 2,
                })
            permission = Permission.query.filter(not_(Permission.id.in_(permission_id_list)))
            for p in permission:
                permissions_list.append({
                    'role_id': role_id,
                    'permission_id': p.id,
                    'permission_name': p.name,
                    'permission_alias_name': p.alias_name,
                    'permission_rw': 0,
                })
            return jsonify({
                'resCode': 1,
                'resData': permissions_list
            })
        except Exception as e:
            current_app.logger.error(e)
            return jsonify({
                'resCode': -1,
                'errMsg': str(e),
            })


@api_user_bp.route('/permission', methods=['POST', 'PUT', 'DELETE'])
@login_required
def api_user_permission():
    if request.method == 'POST':
        permission_name = request.form.get('permission_name', '')
        permission_alias_name = request.form.get('permission_alias_name', '')
        if permission_name == '' or permission_alias_name == '':
            return jsonify({
                'resCode': -1,
                'errMsg': u'权限新增失败，permission_name or permission_alias_name为空.'
            })
        try:
            is_exists = Permission.query.filter(
                or_(Permission.name == permission_name, Permission.alias_name == permission_alias_name)).first()
            if is_exists is not None:
                return jsonify({
                    'resCode': -1,
                    'errMsg': u'权限名称或者权限说明已经存在，请重新添加！',
                })
            else:
                p = Permission()
                p.name = permission_name
                p.alias_name = permission_alias_name
                db.session.add(p)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify({
                'resCode': -1,
                'errMsg': str(e),
            })
        else:
            db.session.commit()
            return jsonify({
                'resCode': 1,
                'resData': 'Add Success.'
            })

    if request.method == 'PUT':
        permission_id = request.form.get('permission_id', '')
        permission_name = request.form.get('permission_name', '')
        permission_alias_name = request.form.get('permission_alias_name', '')

        if not permission_id:
            return jsonify({
                'resCode': -1,
                'errMsg': u'权限修改失败，permission_id为空',
            })
        try:
            p = Permission.query.get(permission_id)
            p.name = permission_name
            p.alias_name = permission_alias_name
            db.session.merge(p)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify({
                'resCode': -1,
                'errMsg': str(e),
            })
        else:
            db.session.commit()
            return jsonify({
                'resCode': 1,
                'resData': 'Modify Success.'
            })

    if request.method == 'DELETE':
        permission_id = request.form.get('permission_id', '')
        if not permission_id:
            return jsonify({
                'resCode': -1,
                'errMsg': u'删除权限失败，permission_id为空'
            })
        try:
            p = Permission.query.get(permission_id)
            db.session.delete(p)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify({
                'resCode': -1,
                'errMsg': str(e),
            })
        else:
            db.session.commit()
            return jsonify({
                'resCode': 1,
                'resData': 'Delete Success.',
            })
