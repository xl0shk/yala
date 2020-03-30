# -*- coding: utf-8 -*-
from flask import Blueprint
from flask import jsonify, send_from_directory, request, current_app, session, make_response, send_file, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from xlrd import xldate_as_tuple
from sqlalchemy import exc, func
from datetime import datetime
from IPy import IP
import uuid
import tablib
import os
import xlrd
import json
import time

from yalamain.models import IPPool, Service, User, Department, Host, Device, Cabinet, Operator
from yalamain.models import Brand, Model, IPSegment
from yalamain.extensions import db

api_assets_bp = Blueprint('api_assets', __name__)


@api_assets_bp.route('/host/list', methods=['GET'])
@login_required
def api_assets_host_list():
    """
    :查询主机列表，根据传入的参数service和use_dpt判断是查询所有或指定部门或指定服务
    """
    service = request.args.get('service', '')
    use_dpt = request.args.get('use_dpt', '')

    use_department_id_list = []
    service_id_list = []
    query_sql = Host.query

    if use_dpt:
        try:
            dpt = Department.query.filter(Department.name == use_dpt).first()
        except exc.SQLAlchemyError as sql_err:
            current_app.logger.error(sql_err)
            dpt = None
        except Exception as err:
            current_app.logger.error(err)
            dpt = None

        if dpt is not None:
            use_department_id_list.append(dpt.id)

        query_sql = query_sql.filter(Host.user_dpt_id.in_(use_department_id_list))

    if service:
        try:
            srv = Service.query.filter(Service.name == service).first()
        except exc.SQLAlchemyError as sql_err:
            current_app.logger.error(sql_err)
            srv = None
        except Exception as err:
            current_app.logger.error(err)
            srv = None

        if srv is not None:
            service_id_list.append(srv.id)

        query_sql = query_sql.filter(Host.service_id.in_(service_id_list))

    try:
        hosts = query_sql.all()
    except exc.SQLAlchemyError as sql_err:
        current_app.logger.error(sql_err)
        return jsonify({
            'resCode': -1,
            'errMsg': 'Host Query Error.',
        })
    except Exception as err:
        current_app.logger.error(err)
        return jsonify({
            'resCode': -1,
            'errMsg': 'Host Other Error.',
        })

    try:
        hosts_list = []
        for host in hosts:
            # TODO：这么查询是因为一开始设计了IP地址池，后续考虑去掉
            if host is not None:
                try:
                    ippool = IPPool.query.get(host.innerIP)
                except exc.SQLAlchemyError as sql_err:
                    current_app.logger.error(sql_err)
                    ippool = None
                except Exception as err:
                    current_app.logger.error(err)
                    ippool = None
            else:
                ippool = None

            hosts_list.append({
                'id': host.id,
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
                'service_id': host.service_id,
                'user_id': host.user_id,
                'cabinet': host.cabinet.code if host.cabinet is not None else '',
                'create_date': host.create_date,
                'payment': host.payment,
                'host_status': host.status,
                'comment': host.comment,
                'instance_id': host.instance_id,
                'pretax_amount': host.bill.pretax_amount if host.bill is not None else '',
                'op': '',
            })
        return jsonify({
            'resCode': 1,
            'resData': hosts_list
        })
    except Exception as e:
        return jsonify({
            'resCode': -1,
            'errMsg': str(e),
        })


@api_assets_bp.route('/host', methods=['GET', 'POST', 'DELETE', 'PUT'])
@login_required
def api_assets_host():
    """
    :restful api形式实现host操作
    """
    if request.method == 'GET':
        host_id = request.args.get('host_id', '')
        if not host_id:
            current_app.logger.error('Load Host Info failed. host_id is None.')
            return jsonify({
                'resCode': -1,
                'errMsg': 'Load Host Info failed. host_id is None.',
            })
        try:
            host = Host.query.get(host_id)
            ippool = IPPool.query.get(host.innerIP)
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
        else:
            return jsonify({
                'resCode': 1,
                'resData': {
                    "innerIP": ippool.IP,
                    "outerIP": host.outerIP,
                    "elasticIP": host.elasticIP,
                    "hostname": host.hostname,
                    "cpu": host.cpu,
                    "memory": host.memory,
                    "disk": host.disk,
                    "os": host.os,
                    "device": host.device_id,
                    "use_dpt": host.user_dpt_id,
                    "user": host.user_id,
                    "owner_dpt": host.owner_dpt_id,
                    "operator": host.ops_id,
                    "host_model": host.host_model,
                    "service": host.service_id,
                    "cabinet": host.cabinet_id,
                    "create_date": host.create_date,
                    "payment": host.payment,
                    "host_status": host.status,
                    "comment": host.comment,
                },
            })

    if request.method == 'POST':
        data = request.form.get('data')
        if not data:
            current_app.logger.error('{0} Add Host post form data is None.'.format(current_user.name))
            return jsonify({
                'resCode': -1,
                'errMsg': 'Add Host Post Data is None.',
            })
        try:
            json_data = json.loads(data)

            _outerIP = json_data.get('outerIP', '')
            _elasticIP = json_data.get('elasticIP', '')
            _cpu = json_data.get('cpu', '')
            _memory = json_data.get('memory', '')
            _disk = json_data.get('disk', '')
            _device = json_data.get('device', '')
            _cabinet = json_data.get('cabinet', '')
            _payment = json_data.get('payment', '')
            _comment = json_data.get('comment', '')
            _innerIP = json_data.get('innerIP', '')

            ippool = IPPool.query.filter(IPPool.IP == _innerIP).first()

            host = Host()
            host.innerIP = ippool.id
            host.outerIP = None if _outerIP == '' else _outerIP
            host.elasticIP = None if _elasticIP == '' else _elasticIP
            host.hostname = json_data.get('hostname', '')
            host.cpu = None if _cpu == '' else _cpu
            host.memory = None if _memory == '' else _memory
            host.disk = None if _disk == '' else _disk
            host.device_id = None if _device == '' else _device
            host.user_dpt_id = json_data.get('use_dpt', '')
            host.user_id = json_data.get('user', '')
            host.ops_id = json_data.get('operator', '')
            host.owner_dpt_id = json_data.get('owner_dpt', '')
            host.service_id = json_data.get('service', '')
            host.cabinet_id = None if _cabinet == '' else _cabinet
            host.create_date = json_data.get('create_date', '')
            host.payment = None if _payment == '' else _payment
            host.status = json_data.get('status', '')
            host.comment = None if _comment == '' else _comment
        except Exception as err:
            current_app.logger.error('err')
            return jsonify({
                'resCode': -1,
                'errMsg': str(err),
            })
        else:
            try:
                db.session.add(host)
                # 更新IP地址池
                IPPool.query.filter_by(id=ippool.id).update({'status': u'不可用'})
                db.session.commit()
            except exc.SQLAlchemyError as err:
                current_app.logger.error('SQLAlchemyError: {}'.format(err))
                db.session.rollback()
                return jsonify({
                    'resCode': -1,
                    'errMsg': 'ADD HOST SQLAlchemyError',
                })
            except:
                current_app.logger.error('SQLOtherError.')
                db.session.rollback()
                return jsonify({
                    'resCode': -1,
                    'errMsg': 'ADD HOST SQLOtherError',
                })
            current_app.logger.info('{0} add host {1}.'.format(current_user.name, _innerIP))
            return jsonify({
                'resCode': 1,
                'Msg': 'ADD HOST SUCCESS.'
            })

    if request.method == 'PUT':
        data = request.form.get('data', '')

        if not data:
            current_app.logger.error('Modify Host post form data is None.')
            return jsonify({
                'resCode': -1,
                'errMsg': 'Modify Host Post Data is None.',
            })
        try:
            json_data = json.loads(data)

            _outerIP = json_data.get('outerIP', '')
            _elasticIP = json_data.get('elasticIP', '')
            _cpu = json_data.get('cpu', '')
            _memory = json_data.get('memory', '')
            _disk = json_data.get('disk', '')
            _device = json_data.get('device', '')
            _cabinet = json_data.get('cabinet', '')
            _payment = json_data.get('payment', '')
            _comment = json_data.get('comment', '')

            host = Host.query.get(json_data.get('host_id'))

            host.outerIP = None if _outerIP == '' else _outerIP
            host.hostname = json_data.get('hostname', '')
            host.elasticIP = None if _elasticIP == '' else _elasticIP
            host.cpu = None if _cpu == '' else _cpu
            host.memory = None if _memory == '' else _memory
            host.disk = None if _disk == '' else _disk
            host.device_id = None if _device == '' else _device
            host.user_dpt_id = json_data.get('use_dpt', '')
            host.user_id = json_data.get('user', '')
            host.owner_dpt_id = json_data.get('owner_dpt', '')
            host.ops_id = json_data.get('operator', '')
            host.service_id = json_data.get('service', '')
            host.cabinet_id = None if _cabinet == '' else _cabinet
            host.create_date = json_data.get('create_date', '')
            host.payment = None if _payment == '' else _payment
            host.status = json_data.get('host_status', '')
            host.comment = None if _comment == '' else _comment
        except Exception as err:
            current_app.logger.error('err')
            return jsonify({
                'resCode': -1,
                'errMsg': str(err),
            })
        else:
            try:
                db.session.merge(host)
                db.session.commit()
            except exc.SQLAlchemyError as sql_err:
                current_app.logger.error(sql_err)
                return jsonify({
                    'resCode': -1,
                    'errMsg': 'Modify HOST SQLAlchemyError',
                })
            except Exception as err:
                current_app.logger.error(err)
                return jsonify({
                    'resCode': -1,
                    'errMsg': 'Modify HOST SQLOtherError',
                })
            current_app.logger.info('{0} modify host {1}'.format(current_user.name, json_data.get('host_id')))
            return jsonify({
                'resCode': 1,
                'resData': 'Modify Host Success.'
            })

    if request.method == 'DELETE':
        host_id = request.form.get('host_id', '')
        if not host_id:
            current_app.logger.error('Delete Host Failed. host_id is None.')
            return jsonify({
                'resCode': -1,
                'errMsg': 'Delete Host Failed. host_id is None.',
            })
        try:
            host = Host.query.get(host_id)
            delete_inner_ip = host.innerIP
            db.session.delete(host)
            # 释放IP地址池中的IP
            IPPool.query.filter_by(id=host.innerIP).update({'status': u'可用'})
            db.session.commit()
        except exc.SQLAlchemyError as sql_err:
            current_app.logger.error(sql_err)
            db.session.rollback()
            return jsonify({
                'resCode': -1,
                'errMsg': 'DELETE HOST SQLAlchemyError',
            })
        except Exception as err:
            current_app.logger.error(err)
            db.session.rollback()
            return jsonify({
                'resCode': -1,
                'errMsg': 'DELETE HOST SQLOtherError',
            })
        else:
            current_app.logger.info('{0} delete host {1}'.format(current_user.name, delete_inner_ip))
            return jsonify({
                'resCode': 1,
                'resData': 'DELETE HOST SUCCESS.'
            })


@api_assets_bp.route('/host/file', methods=['POST'])
@login_required
def api_assets_host_file():
    """
    :批量上传主机信息
    """
    file = request.files.get('upload_file')
    if not file:
        current_app.logger.error('Upload File is None.')
        return jsonify({
            'resCode': -1,
            'errMsg': 'Upload File is None.',
        })

    if file:
        """
        :从Excel导入数据
        """
        if allowed_file(file.filename):
            try:
                filename = secure_filename(file.filename)
                host_template = os.path.join(os.getcwd(), "%s/%s" % (current_app.config['UPLOAD_DIR'], filename))
                file.save(host_template)
                data = xlrd.open_workbook(host_template)
                table = data.sheets()[0]
                rows = table.nrows
                if int(rows) > 1:
                    for i in range(1, int(rows)):
                        host_info = table.row_values(i)
                        host = Host()
                        ippool = IPPool.query.filter(IPPool.IP == str(host_info[0]).strip()).first()
                        if ippool:
                            if ippool.status == u'不可用':
                                continue
                            else:
                                host.innerIP = ippool.id
                        else:
                            continue

                        host.outerIP = str(host_info[1]).strip()
                        host.elasticIP = str(host_info[2]).strip()
                        host.hostname = str(host_info[3]).strip()
                        host.cpu = str(host_info[4] if host_info[4] == '' else int(host_info[4])).strip()
                        host.memory = str(host_info[5] if host_info[5] == '' else int(host_info[5])).strip()
                        host.disk = str(host_info[6] if host_info[6] == '' else int(host_info[6])).strip()
                        device = Device.query.filter_by(sn=str(host_info[7]).strip()).first()
                        host.device_id = device.id if device is not None else None
                        use_dpt = Department.query.filter_by(name=str(host_info[8]).strip()).first()
                        host.user_dpt_id = use_dpt.id if use_dpt is not None else None
                        user = User.query.filter_by(fullname=str(host_info[9]).strip()).first()
                        host.user_id = user.id if user is not None else None
                        operator = Operator.query.filter_by(name=str(host_info[10]).strip()).first()
                        host.ops_id = operator.id if operator is not None else None
                        owner_dpt = Department.query.filter_by(name=str(host_info[11]).strip()).first()
                        host.owner_dpt_id = owner_dpt.id if owner_dpt is not None else None
                        service = Service.query.filter_by(name=str(host_info[12]).strip()).first()
                        host.service_id = service.id if service is not None else None
                        cabinet = Cabinet.query.filter_by(code=str(host_info[13]).strip()).first()
                        host.cabinet_id = cabinet.id if cabinet is not None else None
                        host.create_date = str(datetime(*xldate_as_tuple(host_info[14], 0)).strftime('%Y-%m-%d')).strip()
                        host.payment = str(host_info[15]).strip()
                        host.status = str(host_info[16]).strip()
                        host.comment = str(host_info[17]).strip()
                        db.session.add(host)
                        # 更新IP池中IP的状态
                        IPPool.query.filter_by(id=ippool.id).update({'status': u'不可用'})
                    os.remove(host_template)
                    return jsonify({
                        'resCode': 1,
                        'resData': '上传成功',
                    })
            except Exception as e:
                return jsonify({
                    'resCode': -1,
                    'errMsg': str(e),
                })


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ['xls', 'xlsx']


@api_assets_bp.route('/download/', methods=['GET'])
def api_assets_show_attachment():
    """
    :导出主机Excel模版
    """
    try:
        filename = request.args.get('filename')
        return send_from_directory(os.path.join(os.getcwd(), current_app.config['UPLOAD_DIR']), filename, as_attachment=True)
    except Exception as e:
        return jsonify({
            'resCode': -1,
            'errMsg': str(e),
        })


@api_assets_bp.route('/host/export/', methods=['GET', 'POST'])
@login_required
def api_assets_export_host():
    """
    :导出主机列表
    """
    headers = (
        u'内网IP', u'外网IP', u'弹性IP', u'主机名', 'CPU', u'内存', u'硬盘', u'设备信息', u'使用部门', u'使用人',
        u'运维人员', u'所属部门', u'服务', u'位置信息', u'创建日期', u'支付方式', u'状态', u'备注')
    hosts = Host.query.all()
    host_info = []
    try:
        if hosts is not None:
            inner_ip = ''
            device_type = ''
            brand_name = ''
            model_name = ''
            use_dpt_name = ''
            user_name = ''
            operator_name = ''
            owner_dpt_name = ''
            service_name = ''
            cabinet_code = ''
            for host in hosts:
                if host.innerIP is not None:
                    ippool = IPPool.query.get(host.innerIP)
                    inner_ip = ippool.IP
                if host.device_id is not None:
                    device = Device.query.get(host.device_id)
                    device_type = device.type
                    if device.brand_id is not None:
                        brand = Brand.query.get(device.brand_id)
                        brand_name = brand.name
                    if device.model_id is not None:
                        model = Model.query.get(device.model_id)
                        model_name = model.name
                xls_device_info = device_type + ' ' + brand_name + ' ' + model_name
                if host.user_dpt_id is not None:
                    use_dpt = Department.query.get(host.user_dpt_id)
                    use_dpt_name = use_dpt.name
                if host.user_id is not None:
                    user = User.query.get(host.user_id)
                    user_name = user.fullname
                if host.ops_id is not None:
                    operator = Operator.query.get(host.ops_id)
                    operator_name = operator.name
                if host.owner_dpt_id is not None:
                    owner_dpt = Department.query.get(host.owner_dpt_id)
                    owner_dpt_name = owner_dpt.name
                if host.service_id is not None:
                    service = Service.query.get(host.service_id)
                    service_name = service.name
                if host.cabinet_id is not None:
                    cabinet = Cabinet.query.get(host.cabinet_id)
                    cabinet_code = cabinet.code

                host_info.append(
                    [inner_ip, host.outerIP, host.elasticIP, host.hostname, host.cpu, host.memory, host.disk,
                     xls_device_info,
                     use_dpt_name, user_name, operator_name, owner_dpt_name, service_name, cabinet_code, host.create_date,
                     host.payment, host.status, host.comment])
            print("------------")
            print(inner_ip)
            data = tablib.Dataset(*host_info, headers=headers, title='host')
            download_filename = 'upload/host_%s.xls' % int(time.time())
            f = open(download_filename, 'wb')
            f.write(data.xls)
            f.close()
            download_file = os.path.join(os.getcwd(), download_filename)
            response = make_response(send_file(download_file))
            response.headers["Content-Disposition"] = "attachment; filename=%s;" % os.path.basename(download_filename)
            return response
    except Exception as e:
        return jsonify({
            'resCode': -1,
            'errMsg': str(e),
        })


@api_assets_bp.route('/tree/node/list/', methods=['GET'])
@login_required
def api_assets_tree_node_list():
    """
    :Service为服务表，Department为部门表；在树形结构中，服务表在部门表的下一级
    :return: 树形结构节点列表信息
    """
    try:
        services = Service.query.all()
        departments = Department.query.all()
    except exc.SQLAlchemyError as err:
        current_app.logger.error(err)
        return jsonify({
            'resCode': -1,
            'errMsg': 'Query Error.',
        })
    except Exception as err:
        current_app.logger.error(err)
        return jsonify({
            'resCode': -1,
            'errMsg': 'Other Error',
        })

    try:
        service_info_list = []
        department_info_list = []

        for service in services:
            # 获取每个服务包含的主机数目
            service_hosts_amount = Host.query.join(Service, Host.service_id == Service.id).join(
                Department, Service.dpt_id == Department.id).filter(Host.service_id == service.id).filter(
                Host.user_dpt_id == service.dpt_id).count()
            service_info_list.append({
                'id': str(service.id) + ':' + str(service.name),
                'key': service.tree_id,
                'value': service.name,
                'assets_amount': service_hosts_amount,
                'is_node': 'true',
                'org_id': '',
                'tree_id': service.tree_id,
                'tree_parent': service.tree_parent,
            })

        for department in departments:
            # 获取每个部门包含的主机数
            department_hosts_amount = Host.query.filter(Host.user_dpt_id == department.id).count()
            department_info_list.append({
                'id': str(department.id) + ':' + str(department.name),
                'key': department.tree_id,
                'value': department.name,
                'assets_amount': department_hosts_amount,
                'is_node': 'true',
                'org_id': '',
                'tree_id': department.tree_id,
                'tree_parent': department.tree_parent,
            })

        tree_node_list = service_info_list + department_info_list
        tree_node_list.append({
            "id": "0:Default",
            "key": "0",
            "value": "YALA",
            "assets_amount": len(Host.query.all()),
            "is_node": 'true',
            "org_id": "",
            "tree_id": "0",
            "tree_parent": ""
        })
        return jsonify({
            'resCode': 1,
            'data': tree_node_list
        })
    except Exception as e:
        return jsonify({
            'resCode': -1,
            'errMsg': str(e),
        })


@api_assets_bp.route('/service', methods=['POST', 'PUT', 'DELETE'])
@login_required
def api_assets_service():
    """
    :restful api形式实现service操作
    """
    if request.method == 'POST':
        """
        add_service存在两套逻辑入口
        1是主机管理页面，右键添加，传入的表单key为parent_id，service_name为系统生成
        2是在管理员配置--服务管理添加，传入的表单key为service_name、dpt_id
        """
        parent_id = request.form.get('parent_id', '')
        service_name = request.form.get('service_name', '')
        dpt_id = request.form.get('dpt_id', '')

        if parent_id == '' and (service_name == '' or dpt_id == ''):
            return jsonify({
                'resCode': -1,
                'errMsg': u'服务添加失败，提交的数据为空!',
            })
        try:
            if parent_id != '':
                gen_service_name = u'新节点{}'.format(int(session.get('addCount')) + 1)
                dpt_id = str(parent_id).split(':')[1]
            else:
                gen_service_name = service_name
                dpt_id = dpt_id
                par_id = '0:' + dpt_id

            service = Service()
            service.name = gen_service_name

            is_exists = Service.query.filter_by(name=gen_service_name).first()
            if is_exists is not None:
                return jsonify({
                    'resCode': -1,
                    'errMsg': u'服务已存在!',
                })

            service.dpt_id = dpt_id
            service.tree_parent = parent_id
            db.session.add(service)

            # 更新服务的tree_id
            new_service_id = db.session.query(func.max(Service.id)).one()[0]
            tree_id = str(parent_id) + ':' + str(new_service_id)
            Service.query.filter_by(id=new_service_id).update({'tree_id': tree_id})

            session['addCount'] += 1
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            return jsonify({
                'resCode': -1,
                'errMsg': str(e),
            })
        else:
            db.session.commit()
            service_info = {
                "id": str(new_service_id) + ':' + gen_service_name,
                "key": tree_id,
                "value": gen_service_name
            }
            return jsonify({
                'resCode': 1,
                'resData': service_info
            })

    if request.method == 'PUT':
        modify_name = request.form.get('modify_name', '')
        modify_id = request.form.get('modify_id', '')

        if modify_name == '' or modify_id == '':
            return jsonify({
                'resCode': -1,
                'errMsg': u'modify_name or modify_id为空.'
            })

        try:
            svc_id = str(modify_id).split(':')[2]
            svc_name = modify_name

            service = Service.query.get(svc_id)
            if service is not None:
                service.name = svc_name
                db.session.merge(service)
                db.session.commit()
                return jsonify({
                    'resCode': 1,
                    'resData': 'Modify Success.'
                })
            else:
                abort(404)
        except Exception as e:
            return jsonify({
                'resCode': -1,
                'errMsg': str(e),
            })

    if request.method == 'DELETE':
        """
        :delete_service存在两套逻辑入口，需要做逻辑上区分
        :1是主机管理页面，右键删除，传入参数为del_id，del_id携带":"
        :2是在管理员配置--服务管理删除，传入参数为del_id，不带":"，就是service_id      
        """
        del_id = request.form.get('delete_id', '')

        if del_id == '':
            return jsonify({
                'resCode': -1,
                'errMsg': u'删除服务失败，del_id为空.',
            })
        try:
            if ':' in del_id:
                svc_id = str(del_id).split(':')[2]
            else:
                svc_id = del_id
            service = Service.query.get(svc_id)
            db.session.delete(service)
        except exc.IntegrityError as sql_err:
            current_app.logger.error(sql_err)
            db.session.rollback()
            return jsonify({
                'resCode': -1,
                'errMsg': 'Integrity Error.'
            })
        except exc.InvalidRequestError as sql_err:
            current_app.logger.error(sql_err)
            db.session.rollback()
            return jsonify({
                'resCode': -1,
                'errMsg': 'Invalid Request Error.'
            })
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify({
                'resCode': -1,
                'errMsg': str(e)
            })
        else:
            db.session.commit()
            return jsonify({
                'resCode': 1,
                'resData': 'Delete Success.'
            })


@api_assets_bp.route('/service/list', methods=['GET'])
@login_required
def api_assets_service_list():
    """
    :获取所有service的信息
    """
    try:
        services = Service.query.all()
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
        service_all = []
        for svc in services:
            if svc.dpt_id is not None:
                dpt = Department.query.get(svc.dpt_id)
            else:
                continue
            service_all.append({
                'id': svc.id,
                'name': svc.name,
                'dpt_name': dpt.name if dpt is not None else None,
                'dpt_id': dpt.id if dpt is not None else None,
            })
        return jsonify({
            'resCode': 1,
            'resData': service_all
        })
    except Exception as e:
        current_app.logger.error(e)
        return jsonify({
            'resCode': -1,
            'errMsg': str(e),
        })


@api_assets_bp.route('/service/move', methods=['POST'])
@login_required
def api_assets_service_move():
    """
    :树型结构上的节点移动
    """
    if request.method == 'POST':
        old_service_id = request.form.get('old_service_id', '')
        new_department_id = request.form.get('new_department_id', '')

        if old_service_id == '' or new_department_id == '':
            current_app.logger.error('Tree ID Error.')
            return jsonify({
                'resCode': -1,
                'errMsg': 'Tree ID Error.',
            })

        try:
            # 判断被移动节点的service id，防止部门被移动
            old_service_id_list = str(old_service_id).split(':')
            if len(old_service_id_list) == 2:
                return jsonify({
                    'resCode': -1,
                    'errMsg': u'不能移动部门!',
                })
            elif len(old_service_id_list) != 3:
                return jsonify({
                    'resCode': -1,
                    'errMsg': 'old_service_id error.',
                })

            # 判断接收节点信息，不能移动到service节点下
            new_department_id_list = str(new_department_id).split(':')
            if len(new_department_id_list) == 3:
                return jsonify({
                    'resCode': -1,
                    'errMsg': u'不能移动到服务下!'
                })
            elif len(new_department_id_list) != 2:
                return jsonify({
                    'resCode': -1,
                    'errMsg': 'new_department_id error.',
                })
        except Exception as err:
            current_app.logger.error(err)
            return jsonify({
                'resCode': -1,
                'errMsg': 'old_service_id or new_department_id error.',
            })

        service_detail_id = str(old_service_id).split(':')[2]
        new_department_detail_id = str(new_department_id).split(':')[1]

        dpt_id = new_department_detail_id
        tree_parent = '0:' + dpt_id
        tree_id = tree_parent + ':' + service_detail_id

        try:
            service = Service.query.filter_by(id=service_detail_id).first()
            service.dpt_id = dpt_id
            service.tree_parent = tree_parent
            service.tree_id = tree_id

            for host in Host.query.filter_by(service_id=service_detail_id).all():
                host.user_dpt_id = dpt_id

        except exc.SQLAlchemyError as sql_err:
            current_app.logger.error(sql_err)
            return jsonify({
                'resCode': -1,
                'errMsg': u'数据提交失败.',
            })
        else:
            db.session.commit()
            return jsonify({
                'resCode': 1,
                'resData': u'移动成功!'
            })


@api_assets_bp.route('/operators/list', methods=['GET'])
@login_required
def api_assets_operator_list():
    try:
        ops = Operator.query.all()
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
        operator_all = []
        for op in ops:
            operator_all.append({
                'id': op.id,
                'name': op.name,
            })
        return jsonify({
            'resCode': 1,
            'resData': operator_all
        })
    except Exception as e:
        return jsonify({
            'resCode': -1,
            'errMsg': str(e),
        })


@api_assets_bp.route('/operator', methods=['POST'])
@login_required
def api_assets_operator():
    if request.method == 'POST':
        data = request.form.get('data', '')
        try:
            json_data = json.loads(data)
            op = Operator()
            op.name = json_data.get('operator_name', '')
            db.session.add(op)
            return jsonify({
                'resCode': 1,
                'resData': '新增成功.'
            })
        except Exception as e:
            return jsonify({
                'resCode': -1,
                'errMsg': str(e),
            })


# asset_department
@api_assets_bp.route('/department', methods=['POST', 'PUT', 'DELETE'])
@login_required
def api_assets_department():
    """
    :restful api形式实现service操作
    """
    if request.method == 'POST':
        """
        add_department存在两套逻辑入口
        1是主机管理页面，右键添加
        2是在管理员配置--服务管理添加，传入的表单key为department_name
        """
        department_name = request.form.get('department_name', '')

        if department_name:
            gen_department_name = department_name
        else:
            gen_department_name = u'新节点{}'.format(int(session.get('addCount')) + 1)

        # 判断新增的部门是否已经存在
        try:
            is_exists = Department.query.filter_by(name=gen_department_name).first()
        except exc.SQLAlchemyError as sql_err:
            current_app.logger.error(sql_err)
            return jsonify({
                'resCode': -1,
                'errMsg': u'Query Error.',
            })
        except Exception as err:
            current_app.logger.error(err)
            return jsonify({
                'resCode': -1,
                'errMsg': u'Other Error.',
            })

        if is_exists:
            return jsonify({
                'resCode': -1,
                'errMsg': u'部门已存在!',
            })

        try:
            department = Department()
            department.name = gen_department_name
            # TODO: 使用token是一开始的设计失误，暂且保留，对项目没有功能影响
            department.token = str(uuid.uuid3(uuid.NAMESPACE_DNS, gen_department_name))
            department.tree_parent = '0'
            db.session.add(department)

            # 更新部门的tree_id
            new_dpt_id = db.session.query(func.max(Department.id)).one()[0]
            tree_id = '0' + ':' + str(new_dpt_id)
            Department.query.filter_by(id=new_dpt_id).update({'tree_id': tree_id})
            session['addCount'] += 1
        except Exception as err:
            db.session.rollback()
            current_app.logger.error(err)
            return jsonify({
                'resCode': -1,
                'errMsg': str(err)
            })
        else:
            db.session.commit()
            department_info = {
                "id": str(new_dpt_id) + ':' + gen_department_name,
                "key": tree_id,
                "value": gen_department_name
            }
            return jsonify({
                'resCode': 1,
                'resData': department_info
            })

    if request.method == 'PUT':
        modify_name = request.form.get('modify_name', '')
        modify_id = request.form.get('modify_id', '')

        if modify_name == '' or modify_id == '':
            return jsonify({
                'resCode': -1,
                'errMsg': u'modify_name or modify_id为空.'
            })

        try:
            if ':' in str(modify_id):
                dpt_id = str(modify_id).split(':')[1]
            else:
                dpt_id = modify_id

            dpt = Department.query.get(dpt_id)
            if dpt is not None:
                dpt.name = modify_name
                db.session.merge(dpt)
                db.session.commit()
                return jsonify({
                    'resCode': 1,
                    'resData': 'Modify Success.'
                })
            else:
                abort(404)
        except Exception as err:
            current_app.logger.error(err)
            return jsonify({
                'resCode': -1,
                'errMsg': str(err)
            })

    if request.method == 'DELETE':
        del_id = request.form.get('delete_id', '')

        if del_id == '':
            return jsonify({
                'resCode': -1,
                'errMsg': u'delete department id为空.',
            })
        try:
            if ':' in str(del_id):
                dpt_id = str(del_id).split(':')[1]
            else:
                dpt_id = del_id

            dpt = Department.query.get(dpt_id)
            db.session.delete(dpt)
        except exc.IntegrityError as sql_err:
            current_app.logger.error(sql_err)
            db.session.rollback()
            return jsonify({
                'resCode': -1,
                'errMsg': 'Integrity Error.'
            })
        except exc.InvalidRequestError as sql_err:
            current_app.logger.error(sql_err)
            db.session.rollback()
            return jsonify({
                'resCode': -1,
                'errMsg': 'Invalid Request Error.'
            })
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify({
                'resCode': -1,
                'errMsg': str(e)
            })
        else:
            db.session.commit()
            return jsonify({
                'resCode': 1,
                'resData': 'Delete Success.'
            })


@api_assets_bp.route('/department/list', methods=['GET'])
@login_required
def api_assets_department_list():
    """
    :获取所有部门的信息
    """
    try:
        departments = Department.query.all()
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
        department_all = []
        for dpt in departments:
            department_all.append({
                'id': dpt.id,
                'name': dpt.name,
            })
        return jsonify({
            'resCode': 1,
            'resData': department_all
        })
    except Exception as e:
        return jsonify({
            'resCode': -1,
            'errMsg': str(e),
        })


@api_assets_bp.route('/ip/check', methods=['POST'])
@login_required
def api_assets_ip_check():
    """
    :IP地址检查
    """
    if request.method == 'POST':
        inner_ip = request.form.get('innerIP', '')
        if not inner_ip:
            return jsonify({
                'resCode': -1,
                'errMsg': u'innerIP为空!',
            })

        try:
            ippool = IPPool.query.filter(IPPool.IP == inner_ip).first()
            if ippool is not None:
                ip_status = True if ippool.status == u'可用' else False
                return jsonify({
                    'resCode': 1,
                    'status': str(ip_status),
                })
            else:
                return jsonify({
                    'resCode': -1,
                    'errMsg': 'IP池中无此IP',
                })
        except Exception as e:
            return jsonify({
                'resCode': -1,
                'errMsg': str(e),
            })


@api_assets_bp.route('/ip/pool', methods=['POST', 'DELETE'])
@login_required
def api_assets_ip_pool():
    """
    :涉及两张表：IPSegment 和 IPPool; IPSegment存储IP地址段信息，IPPool存储具体IP地址信息，标记可用或不可用.
    """
    if request.method == 'POST':
        new_ip_segment = request.form.get('ip_segment', '')

        if new_ip_segment == '':
            return jsonify({
                'resCode': -1,
                'errMsg': u'提交的添加数据为空!',
            })

        try:
            is_exists = IPSegment.query.filter(IPSegment.ip_segment == new_ip_segment).first()
            if is_exists is not None:
                return jsonify({
                    'resCode': -1,
                    'errMsg': u'该IP段已经存在，请重新输入！',
                })

            ip_segment = IPSegment()
            ip_segment.ip_segment = new_ip_segment
            db.session.add(ip_segment)

            ref_ip_segment = IPSegment.query.filter(IPSegment.ip_segment == new_ip_segment).first()
            ip_scope = new_ip_segment
            gen_ip_list = IP(ip_scope)
            for ip in gen_ip_list:
                ip_pool = IPPool()
                ip_pool.IP = str(ip)
                ip_pool.ip_segment_id = ref_ip_segment.id
                ip_pool.status = u'可用'
                db.session.add(ip_pool)
        except Exception as err:
            db.session.rollback()
            current_app.logger.error(err)
            return jsonify({
                'resCode': -1,
                'errMsg': str(err)
            })
        else:
            db.session.commit()
            return jsonify({
                'resCode': 1,
                'Msg': 'Add IP Segment Success.'
            })

    if request.method == 'DELETE':
        ip_segment_id = request.form.get('ip_segment_id', '')
        if ip_segment_id == '':
            return jsonify({
                'resCode': -1,
                'errMsg': u'删除的ip_segment_id为空!',
            })
        try:
            ip_segment = IPSegment.query.get(ip_segment_id)
            if ip_segment is None:
                return jsonify({
                    'resCode': -1,
                    'errMsg': u'删除的IP段不存在!'
                })

            del_ip_pool = IPPool.query.filter(IPPool.ip_segment_id == ip_segment_id)
            del_ip_pool.delete()
            db.session.delete(ip_segment)
        except exc.IntegrityError as sql_error:
            current_app.logger.error(sql_error)
            db.session.rollback()
            return jsonify({
                'resCode': -1,
                'errMsg': 'SQL Integrity Error.',
            })
        except exc.InvalidRequestError as sql_error:
            current_app.logger.error(sql_error)
            db.session.rollback()
            return jsonify({
                'resCode': -1,
                'errMsg': 'SQL Invalid Request Error.',
            })
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify({
                'resCode': -1,
                'errMsg': str(e),
            })
        else:
            db.session.commit()
            return jsonify({
                'resCode': 1,
                'resData': 'Delete IP Segment Success.'
            })


def gen_ips(ip_segment):
    try:
        ip_list = []
        ips = str(ip_segment)
        key_num = ips.split('/')[0].split('.')[2]
        for ip in range(2, 255):
            ip_list.append("192.168." + str(key_num) + "." + str(ip))
        return ip_list
    except Exception as e:
        return jsonify({
            'resCode': -1,
            'errMsg': str(e),
        })
