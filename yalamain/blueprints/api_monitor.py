# -*- coding: utf-8 -*-
from flask import Blueprint, current_app, render_template, request, redirect, url_for, jsonify
from flask_login import login_required, current_user
from datetime import timedelta
from sqlalchemy import exc, or_
import datetime
import json

from yalamain.models import MonitorDomainInfo, MonitorTcpConnectProbe
from yalamain.extensions import db

api_monitor_bp = Blueprint('api_monitor', __name__)


@api_monitor_bp.route('/domain', methods=['POST', 'PUT', 'DELETE'])
@login_required
def api_monitor_domain():
    if request.method == 'POST':
        domain = request.form.get('domain')
        rd_maintainer = request.form.get('rd_maintainer')
        cre_maintainer = request.form.get('cre_maintainer')
        remark = request.form.get('remark')
        update_time = datetime.datetime.now()

        try:
            query_domain = MonitorDomainInfo.query.filter_by(domain=domain).first()
        except exc.SQLAlchemyError as sql_err:
            current_app.logger.error('MySQL ERROR: {}.'.format(sql_err))
            return jsonify({
                'resCode': 3,
                'resMsg': 'Query MySQL ERROR.'
            })
        if query_domain is not None:
            return jsonify({
                'resCode': 2,
                'resMsg': 'Domain Exist.'
            })

        try:
            mdi = MonitorDomainInfo(domain, rd_maintainer, cre_maintainer, remark, update_time)
            db.session.add(mdi)
            db.session.commit()
        except exc.SQLAlchemyError as sql_err:
            current_app.logger.error('MySQL ERROR: {}.'.format(sql_err))
            return jsonify({
                'resCode': 4,
                'resMsg': 'Insert MySQL ERROR.'
            })

        current_app.logger.info('{0} Create Domain {1}.'.format(current_user.name, domain))
        return jsonify({
            'resCode': 1,
            'resMsg': 'Create Domain Success.'
        })

    if request.method == 'PUT':
        domain_id = request.form.get('domain_id')
        domain = request.form.get('domain')
        rd_maintainer = request.form.get('rd_maintainer')
        cre_maintainer = request.form.get('cre_maintainer')
        remark = request.form.get('remark')

        try:
            query_domain = MonitorDomainInfo.query.filter_by(id=domain_id, domain=domain, rd_maintainer=rd_maintainer,
                                                             cre_maintainer=cre_maintainer, remark=remark).first()
        except exc.SQLAlchemyError as sql_err:
            current_app.logger.error('MySQL ERROR: {}'.format(sql_err))
            return jsonify({
                'resCode': 4,
                'resMsg': 'Query ERROR.'
            })

        if query_domain is not None:
            return jsonify({
                'resCode': 2,
                'resMsg': 'Data Not Changed.'
            })

        update_time = datetime.datetime.now()
        try:
            d = MonitorDomainInfo.query.filter_by(id=domain_id).first()
            d.domain = domain
            d.rd_maintainer = rd_maintainer
            d.cre_maintainer = cre_maintainer
            d.remark = remark
            d.update_time = update_time
        except exc.SQLAlchemyError as sql_err:
            current_app.logger.error('MySQL ERROR: {}'.format(sql_err))
            return jsonify({
                'resCode': 3,
                'resMsg': 'Update ERROR.'
            })
        else:
            db.session.commit()
            current_app.logger.info('{0} UPDATE Domain {1}.'.format(current_user.name, domain))
            return jsonify({
                'resCode': 1,
                'resMsg': 'Success.'
            })

    if request.method == 'DELETE':
        domain_id = request.form.get('domain_id')

        try:
            query_domain = MonitorDomainInfo.query.filter_by(id=domain_id).first()
        except exc.SQLAlchemyError as sql_err:
            current_app.logger.error('MySQL ERROR: {}.'.format(sql_err))
            return jsonify({
                'resCode': 2,
                'resMsg': ''
            })

        if query_domain is None:
            return jsonify({
                'resCode': 3,
                'resMsg': 'Domain not Exist.'
            })
        domain = query_domain.domain

        try:
            MonitorDomainInfo.query.filter_by(id=domain_id).delete()
            db.session.commit()
        except exc.SQLAlchemyError as sql_err:
            current_app.logger.error('MySQL ERROR: {}.'.format(sql_err))
            return jsonify({
                'resCode': 4,
                'resMsg': 'Delete ERROR.'
            })

        current_app.logger.info('{0} DELETE Domain {1}'.format(current_user.name, domain))
        return jsonify({
            'resCode': 1,
            'resMsg': 'Delete Success.'
        })


@api_monitor_bp.route('/domain/list', methods=['GET'])
def api_monitor_domain_list():
    try:
        domain_list = MonitorDomainInfo.query.all()
    except exc.SQLAlchemyError as sql_err:
        current_app.logger.error(sql_err)
        return json.dumps({})
    else:
        domain_res = {}
        for domain_one in domain_list:
            domain = domain_one.domain
            rd_maintainer = domain_one.rd_maintainer
            cre_maintainer = domain_one.cre_maintainer
            domain_res[domain] = {'rd_maintainer': rd_maintainer, 'cre_maintainer': cre_maintainer}
        return json.dumps(domain_res)


@api_monitor_bp.route('/tcp/connect/probe', methods=['POST', 'PUT', 'DELETE'])
@login_required
def api_monitor_tcp_connect_probe():
    if request.method == 'POST':
        service_name = request.form.get('service_name')
        server_ip = request.form.get('server_ip')
        tcp_port = request.form.get('tcp_port')
        service_owner = request.form.get('service_owner')

        target = '{0}:{1}'.format(server_ip, tcp_port)
        update_date = datetime.datetime.strftime(datetime.datetime.now() - timedelta(1), '%Y-%m-%d')

        try:
            query_tcp_connect_probe = MonitorTcpConnectProbe.query.filter_by(target=target).first()
        except exc.SQLAlchemyError as sql_err:
            current_app.logger.error('MySQL ERROR: {}.'.format(sql_err))
            return jsonify({
                'resCode': 3,
                'resMsg': 'Query MySQL ERROR.'
            })
        if query_tcp_connect_probe is not None:
            return jsonify({
                'resCode': 2,
                'resMsg': 'Target Exist.'
            })

        try:
            mt = MonitorTcpConnectProbe(service_name, target, server_ip, tcp_port, service_owner, update_date)
            db.session.add(mt)
            db.session.commit()
        except exc.SQLAlchemyError as sql_err:
            current_app.logger.error('MySQL ERROR: {}.'.format(sql_err))
            return jsonify({
                'resCode': 4,
                'resMsg': 'Insert MySQL ERROR.'
            })

        current_app.logger.info('{0} Create TCP Connect Probe {1}.'.format(current_user.name, target))
        return jsonify({
            'resCode': 1,
            'resMsg': 'Create Monitor Service Success.'
        })

    if request.method == 'PUT':
        tcp_connect_probe_id = request.form.get('tcp_connect_probe_id')
        service_name = request.form.get('service_name')
        target = request.form.get('target')
        server_ip = request.form.get('server_ip')
        tcp_port = request.form.get('tcp_port')
        service_owner = request.form.get('service_owner')

        try:
            query_tcp_connect_probe = MonitorTcpConnectProbe.query.filter_by(id=tcp_connect_probe_id, service_name=service_name,
                                                                             target=target, server_ip=server_ip, tcp_port=tcp_port,
                                                                             service_owner=service_owner).first()
        except exc.SQLAlchemyError as sql_err:
            current_app.logger.error('MySQL ERROR: {}'.format(sql_err))
            return jsonify({
                'resCode': 4,
                'resMsg': 'Query ERROR.'
            })

        if query_tcp_connect_probe is not None:
            return jsonify({
                'resCode': 2,
                'resMsg': 'Data Not Changed.'
            })

        update_date = datetime.datetime.strftime(datetime.datetime.now() - timedelta(1), '%Y-%m-%d')
        target = '{0}:{1}'.format(server_ip, tcp_port)

        try:
            tc = MonitorTcpConnectProbe.query.filter_by(id=tcp_connect_probe_id).first()
            tc.service_name = service_name
            tc.target = target
            tc.server_ip = server_ip
            tc.tcp_port = tcp_port
            tc.service_owner = service_owner
            tc.update_date = update_date
        except exc.SQLAlchemyError as sql_err:
            current_app.logger.error('MySQL ERROR: {}'.format(sql_err))
            return jsonify({
                'resCode': 3,
                'resMsg': 'Update ERROR.'
            })
        else:
            db.session.commit()
            current_app.logger.info('{0} UPDATE Tcp Connect Probe {1} {2}.'.format(current_user.name, service_name, target))
            return jsonify({
                'resCode': 1,
                'resMsg': 'Success.'
            })

    if request.method == 'DELETE':
        tcp_connect_probe_id = request.form.get('tcp_connect_probe_id')
        target = request.form.get('target')

        try:
            query_tcp_connect_probe = MonitorTcpConnectProbe.query.filter_by(target=target).first()
        except exc.SQLAlchemyError as sql_err:
            current_app.logger.error('MySQL ERROR: {}.'.format(sql_err))
            return jsonify({
                'resCode': 2,
                'resMsg': ''
            })

        if query_tcp_connect_probe is None:
            return jsonify({
                'resCode': 3,
                'resMsg': 'Target not Exist.'
            })

        try:
            MonitorTcpConnectProbe.query.filter_by(target=target).delete()
            db.session.commit()
        except exc.SQLAlchemyError as sql_err:
            current_app.logger.error('MySQL ERROR: {}.'.format(sql_err))
            return jsonify({
                'resCode': 4,
                'resMsg': 'Delete ERROR.'
            })

        current_app.logger.info('{0} DELETE Domain {1}'.format(current_user.name, target))
        return jsonify({
            'resCode': 1,
            'resMsg': 'Delete Success.'
        })


@api_monitor_bp.route('/tcp/connect/probe/clone', methods=['POST'])
@login_required
def api_monitor_tcp_connect_probe_clone():
    if request.method == 'POST':
        service_name = request.form.get('service_name')
        target = request.form.get('target')
        server_ip = request.form.get('server_ip')
        tcp_port = request.form.get('tcp_port')
        service_owner = request.form.get('service_owner')

        new_target = '{0}:{1}'.format(server_ip, tcp_port)
        update_date = datetime.datetime.strftime(datetime.datetime.now() - timedelta(1), '%Y-%m-%d')

        if target == new_target:
            return jsonify({
                'resCode': 5,
                'resMsg': 'Target not Changed.'
            })

        try:
            query_tcp_connect_probe = MonitorTcpConnectProbe.query.filter_by(target=new_target).first()
        except exc.SQLAlchemyError as sql_err:
            current_app.logger.error('MySQL ERROR: {}.'.format(sql_err))
            return jsonify({
                'resCode': 3,
                'resMsg': 'Query MySQL ERROR.'
            })
        if query_tcp_connect_probe is not None:
            return jsonify({
                'resCode': 2,
                'resMsg': 'Target Exist.'
            })

        try:
            mt = MonitorTcpConnectProbe(service_name, new_target, server_ip, tcp_port, service_owner, update_date)
            db.session.add(mt)
            db.session.commit()
        except exc.SQLAlchemyError as sql_err:
            current_app.logger.error('MySQL ERROR: {}.'.format(sql_err))
            return jsonify({
                'resCode': 4,
                'resMsg': 'Insert MySQL ERROR.'
            })

        current_app.logger.info('{0} Clone TCP Connect Probe {1} from {2}.'.format(current_user.name, new_target, target))
        return jsonify({
            'resCode': 1,
            'resMsg': 'Clone Monitor Service Success.'
        })


@api_monitor_bp.route('/tcp/connect/probe/list', methods=['GET'])
def api_monitor_tcp_connect_probe_list():
    try:
        tcp_connect_probe_list = MonitorTcpConnectProbe.query.all()
    except exc.SQLAlchemyError as sql_err:
        current_app.logger.error(sql_err)
        return jsonify({
            'resCode': 2,
            'errMsg': str(sql_err),
        })

    tc_list = []
    try:
        for tc in tcp_connect_probe_list:
            tc_list.append({
                'service_name': tc.service_name,
                'target': tc.target,
                'server_ip': tc.server_ip,
                'tcp_port': tc.tcp_port,
                'service_owner': tc.service_owner,
            })
    except Exception as err:
        return jsonify({
            'resCode': 3,
            'errMsg': str(err)
        })

    return jsonify({
        'resCode': 1,
        'data': tc_list
    })
