# -*- coding: utf-8 -*-
from flask import Blueprint
from flask import render_template, send_file, current_app, Markup
from flask_login import login_required
import os
from sqlalchemy import exc
from datetime import datetime, timedelta
import datetime

from yalamain.extensions import ldap
from yalamain.models import MonitorDomainInfo, MonitorTcpConnectProbe
from yalamain.models import Host, User, CronLog

index_bp = Blueprint('index', __name__)


@index_bp.route('/')
@ldap.login_required
def login():
    return render_template('auth/login.html')


@index_bp.route('/index')
@login_required
def index():
    try:
        host_count = Host.query.count()
        monitor_domain_count = MonitorDomainInfo.query.count()
        monitor_probe_count = MonitorTcpConnectProbe.query.count()
        users_count = User.query.count()
    except exc.SQLAlchemyError as sql_err:
        current_app.logger.error(sql_err)
        host_count = 0
        monitor_domain_count = 0
        monitor_probe_count = 0
        users_count = 0

    try:
        chart_list = []
        for i in reversed(range(15)):
            chart_dict = {}
            update_date = (datetime.datetime.now() - datetime.timedelta(days=i))
            update_date = update_date.strftime('%Y-%m-%d')
            cron_logs = CronLog.query.filter(CronLog.update_date == update_date).all()
            for c in cron_logs:
                chart_dict['update_date'] = update_date
                chart_dict[c.asset] = c.count
            if (len(chart_dict)) == 5:
                chart_list.append(chart_dict)
    except exc.SQLAlchemyError as sql_err:
        chart_list = []

    return render_template('index.html', menu='dashboard', host_count=host_count, monitor_domain_count=monitor_domain_count,
                           monitor_probe_count=monitor_probe_count, users_count=users_count,
                           chart_list=Markup(chart_list))


@index_bp.route('/changeLog')
@login_required
def changelog():
    return render_template('changelog.html')


@index_bp.route('/ChangeLog.md')
@login_required
def get_changelog_md():
    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    return send_file(os.path.join(base_dir, 'ChangeLog.md'))
