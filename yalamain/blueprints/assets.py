# -*- coding: utf-8 -*-
from flask import Blueprint
from flask import render_template, request, jsonify
from flask_login import login_required
from sqlalchemy import exc

from yalamain.models import *

assets_bp = Blueprint('assets', __name__)


@assets_bp.route('/host', methods=['GET'])
@login_required
def assets_host():
    """
    :主机管理页面
    """
    if request.method == 'GET':
        return render_template('assets/host.html', menu='host_list')


@assets_bp.route('/host/detail/', methods=['GET'])
@login_required
def assets_host_detail():
    """
    :TODO: 仅仅返回单个主机的详细信息，没必要使用分页。后续修改.
    """
    try:
        host_id = request.args.get('host_id')
        page = request.args.get('page', 1, type=int)
        pagination = Host.query.filter_by(id=host_id).paginate(page, per_page=current_app.config['PER_PAGE'],
                                                               error_out=False)
        hosts = pagination.items
        return render_template('assets/host_detail.html', hosts=hosts, menu='host_detail', pagination=pagination)
    except Exception as e:
        return jsonify({
            'resCode': -1,
            'errMsg': str(e),
        })


@assets_bp.route('/service', methods=['GET'])
@login_required
def assets_service():
    if request.method == 'GET':
        page = request.args.get('page', 1, type=int)
        try:
            pagination = Service.query.paginate(page, per_page=current_app.config['PER_PAGE'], error_out=False)
            services = pagination.items
        except exc.SQLAlchemyError as sql_err:
            current_app.logger.error(sql_err)
            pagination = None
            services = None
        except Exception as e:
            current_app.logger.error(e)
            pagination = None
            services = None

        return render_template('assets/service.html', services=services, menu='service_list', pagination=pagination)


@assets_bp.route('/department', methods=['GET'])
@login_required
def assets_department():
    if request.method == 'GET':
        page = request.args.get('page', 1, type=int)
        try:
            pagination = Department.query.paginate(page, per_page=current_app.config['PER_PAGE'], error_out=False)
            dpts = pagination.items
        except exc.SQLAlchemyError as sql_err:
            current_app.logger.error(sql_err)
            pagination = None
            dpts = None
        except Exception as e:
            current_app.logger.error(e)
            pagination = None
            dpts = None
        return render_template('assets/department.html', dpts=dpts, menu='department_list', pagination=pagination)


@assets_bp.route('/ip/pool', methods=['GET'])
@login_required
def assets_ip_pool():
    """
    :IP地址池列表页面
    """
    if request.method == 'GET':
        page = request.args.get('page', 1, type=int)
        try:
            pagination = IPSegment.query.paginate(page, per_page=current_app.config['PER_PAGE'], error_out=False)
            ip_segments = pagination.items
        except exc.SQLAlchemyError as sql_err:
            current_app.logger.error(sql_err)
            ip_segments = None
            pagination = None
        except Exception as err:
            current_app.logger.error(err)
            ip_segments = None
            pagination = None
        return render_template('assets/ip_pool.html', ip_segments=ip_segments, menu='ip_pool_list', pagination=pagination)


@assets_bp.route('/ip/pool/detail', methods=['GET'])
@login_required
def asset_ip_pool_detail():
    """
    :查看某IP地址段详细的IP地址列表
    """
    try:
        ip_segment_id = request.args.get('ip_segment_id')
        page = request.args.get('page', 1, type=int)
        page_size = current_app.config['PER_PAGE']
        pagination = IPPool.query.filter_by(ip_segment_id=ip_segment_id).paginate(page, per_page=page_size, error_out=False)
        ip_pools = pagination.items
    except Exception as e:
        return jsonify({
            'result': -1,
            'errMsg': str(e),
        })
    return render_template('assets/ip_pool_detail.html', ippools=ip_pools, ip_segment_id=ip_segment_id,
                           menu='ip_pool_detail_list', pagination=pagination)
