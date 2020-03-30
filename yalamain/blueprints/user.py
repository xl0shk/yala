# -*- coding: utf-8 -*-
from flask import Blueprint
from flask import render_template, redirect, url_for, request, jsonify, current_app
from flask_login import login_required
from sqlalchemy import exc, or_, exists, not_
import uuid
import json

from yalamain.models import User, Role, Permission, role_permission
from yalamain.extensions import db

user_bp = Blueprint('user', __name__)


@user_bp.route('/user', methods=['GET', 'POST'])
@login_required
def user_user():
    if request.method == 'GET':
        page = request.args.get('page', 1, type=int)
        search = ''
        try:
            pagination = User.query.paginate(page, per_page=current_app.config['PER_PAGE'], error_out=False)
            users = pagination.items
        except exc.SQLAlchemyError as sql_err:
            current_app.logger.error(sql_err)
            users = None
            pagination = None
        except Exception as e:
            current_app.logger.error(e)
            users = None
            pagination = None
        return render_template('user/users.html', users=users, search=search, menu='user_list', pagination=pagination)

    if request.method == 'POST':
        search = request.form.get('search', '')

        if not search:
            return redirect(url_for('user.user_user'))

        try:
            users = User.query.filter(
                or_(User.name.like('%' + search + '%'),
                    User.fullname.like('%' + search + '%'),
                    exists().where(Role.id == User.role_id).where(Role.name.like('%' + search + '%')),
                    User.email.like('%' + search + '%'))).all()
        except exc.SQLAlchemyError as sql_err:
            current_app.logger.error(sql_err)
            users = None
            pagination = None
        except Exception as e:
            current_app.logger.error(e)
            users = None
            pagination = None
        return render_template('user/users.html', users=users, search=search, menu='user_list')


@user_bp.route('/role', methods=['GET'])
@login_required
def user_role():
    if request.method == 'GET':
        page = request.args.get('page', 1, type=int)
        page_size = current_app.config['PER_PAGE']
        try:
            pagination = Role.query.paginate(page, per_page=page_size, error_out=False)
            roles = pagination.items
        except exc.SQLAlchemyError as sql_err:
            current_app.logger.error(sql_err)
            roles = None
            pagination = None
        except Exception as e:
            current_app.logger.error(e)
            roles = None
            pagination = None
        return render_template('user/roles.html', roles=roles, menu='role_list', pagination=pagination)


@user_bp.route('/permission', methods=['GET'])
@login_required
def user_permission():
    if request.method == 'GET':
        page = request.args.get('page', 1, type=int)
        page_size = current_app.config['PER_PAGE']
        try:
            pagination = Permission.query.paginate(page, per_page=page_size, error_out=False)
            permissions = pagination.items
        except exc.SQLAlchemyError as sql_err:
            current_app.logger.error(sql_err)
            permissions = None
            pagination = None
        except Exception as e:
            current_app.logger.error(e)
            permissions = None
            pagination = None
        return render_template('user/permission.html', permissions=permissions, menu='permission_list', pagination=pagination)
