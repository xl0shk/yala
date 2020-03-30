# -*- coding: utf-8 -*-
from flask import Blueprint
from flask import render_template, redirect, url_for, request, jsonify, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
import uuid
import re

from yalamain.models import User, Role
from yalamain.extensions import db, ldap

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def auth_login():
    if request.method == 'GET':
        return render_template('auth/login.html')

    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        remember_me = request.form.get('remember_me', False)
        next = request.args.get('next', '')
        if username and password:
            try:
                ldap_username = username + '@dadaabc.net'
                # STEP1: 向LDAP查询username和password
                ldap_user = ldap.bind_user(ldap_username, password)
                if ldap_user is None:
                    # STEP2: 认证错误处理
                    current_app.logger.info('{0} login error.'.format(username))
                    return jsonify({
                        'resCode': -1,
                        'errMsg': u'用户没有权限登录系统，请联系AD管理员处理！'
                    })
                else:
                    # STEP3: LDAP认证成功后，通过username查询MySQL
                    user = User.query.filter_by(name=username).first()
                    user_ad_name = ldap.get_object_details(ldap_username).get('cn')[0].decode('utf-8')
                    fullname = re.findall(r'[(](.*?)[)]', user_ad_name)[0] if user_ad_name.find(
                        '(') >= 0 and user_ad_name.find(')') >= 0 else user_ad_name

                    # STEP4: MySQL查询username为空后，插入username数据
                    if user is None:
                        u = User()
                        u.name = username
                        u.fullname = fullname if fullname is not None else None
                        u.password = password
                        u.email = ldap_username
                        u.status = True
                        u.role_id = Role.query.filter_by(name='RD').first().id
                        u.token = str(uuid.uuid3(uuid.NAMESPACE_DNS, ldap_username))
                        db.session.add(u)

                    # STEP5: username信息写入session
                    user = User.query.filter_by(name=username).first()
                    login_user(user, remember_me)
                    session['username'] = username

                    current_app.logger.info('{0} login success.'.format(username))
                    return jsonify({
                        'resCode': 1,
                        'next': next
                    })
            except Exception as e:
                return jsonify({
                    'resCode': -1,
                    'errMsg': str(e),
                })


@auth_bp.route('/logout/')
@login_required
def auth_logout():
    current_app.logger.info('{0} logout.'.format(current_user.name))
    logout_user()
    return redirect(url_for('auth.login'))
