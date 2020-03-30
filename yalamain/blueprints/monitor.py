# -*- coding: utf-8 -*-
from flask import Blueprint, current_app, render_template, request, redirect, url_for, jsonify
from flask_login import login_required, current_user
from datetime import timedelta
from sqlalchemy import exc, or_
import datetime
import json

from yalamain.models import MonitorDomainInfo, MonitorTcpConnectProbe
from yalamain.extensions import db

monitor_bp = Blueprint('monitor', __name__)


@monitor_bp.route('/domain', methods=['GET'])
@login_required
def monitor_domain():
    if request.method == 'GET':
        page = request.args.get('page', 1, type=int)
        search = ''

        try:
            pagination = MonitorDomainInfo.query.order_by(MonitorDomainInfo.id).paginate(page, per_page=50, error_out=False)
            domains = pagination.items
        except exc.SQLAlchemyError as sql_err:
            current_app.logger.error('MySQL ERROR: {}'.format(sql_err))
            pagination = None
            domains = None

        current_app.logger.info('{0} visit monitor_domain'.format(current_user.name))
        return render_template('monitor/domain.html', domains=domains, search=search, pagination=pagination, menu='monitor_domain')


@monitor_bp.route('/domain/search', methods=['GET', 'POST'])
@login_required
def monitor_domain_search():
    if request.method == 'GET':
        return redirect(url_for('monitor.monitor_domain'))

    if request.method == 'POST':
        search = request.form.get('search')

        if search == '':
            return redirect(url_for('monitor.monitor_domain'))
        try:
            domains = MonitorDomainInfo.query.filter(or_(MonitorDomainInfo.domain.like('%' + search + '%'),
                                                         MonitorDomainInfo.rd_maintainer.like('%' + search + '%'),
                                                         MonitorDomainInfo.cre_maintainer.like('%' + search + '%'),
                                                         MonitorDomainInfo.remark.like('%' + search + '%'),
                                                         MonitorDomainInfo.update_time.like('%' + search + '%'))).all()
        except exc.SQLAlchemyError as sql_err:
            current_app.logger.error('MySQL ERROR: {}'.format(sql_err))
            domains = ''

        current_app.logger.info('{0} search {1}'.format(current_user.name, search))
        return render_template('monitor/domain.html', domains=domains, search=search, menu='monitor_domain')


@monitor_bp.route('/tcp/connect/probe', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def monitor_tcp_connect_probe():
    if request.method == 'GET':
        page = request.args.get('page', 1, type=int)
        search = ''

        try:
            pagination = MonitorTcpConnectProbe.query.order_by(MonitorTcpConnectProbe.service_name).paginate(page, per_page=50,
                                                                                                             error_out=False)
            tcp_connect_probes = pagination.items
        except exc.SQLAlchemyError as sql_err:
            current_app.logger.error('MySQL ERROR: {}'.format(sql_err))
            pagination = None
            tcp_connect_probes = None

        current_app.logger.info('{0} visit monitor_tcp_connect_probe'.format(current_user.name))
        return render_template('monitor/tcp_connect_probe.html', tcp_connect_probes=tcp_connect_probes, search=search,
                               pagination=pagination, menu='monitor_tcp_connect_probe')


@monitor_bp.route('/tcp/connect/probe/search', methods=['GET', 'POST'])
@login_required
def monitor_tcp_connect_probe_search():
    if request.method == 'GET':
        return redirect(url_for('monitor.monitor_tcp_connect_probe'))

    if request.method == 'POST':
        search = request.form.get('search')

        if search == '':
            return redirect(url_for('monitor.monitor_tcp_connect_probe'))

        try:
            tcp_connect_probes = MonitorTcpConnectProbe.query.filter(or_(MonitorTcpConnectProbe.service_name.like('%' + search + '%'),
                                                                         MonitorTcpConnectProbe.target.like('%' + search + '%'),
                                                                         MonitorTcpConnectProbe.server_ip.like('%' + search + '%'),
                                                                         MonitorTcpConnectProbe.tcp_port.like('%' + search + '%'),
                                                                         MonitorTcpConnectProbe.service_owner.like('%' + search + '%'))).all()
        except exc.SQLAlchemyError as sql_err:
            current_app.logger.error('MySQL ERROR: {}'.format(sql_err))
            tcp_connect_probes = ''

        current_app.logger.info('{0} search {1}'.format(current_user.name, search))
        return render_template('monitor/tcp_connect_probe.html', tcp_connect_probes=tcp_connect_probes, search=search,
                               menu='monitor_tcp_connect_probe')
