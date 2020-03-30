# -*- coding: utf-8 -*-
from yalamain.extensions import db
from datetime import datetime
from flask_login import UserMixin, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app


class IPPool(db.Model):
    __tablename__ = 'ip_pool'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = db.Column(db.Integer, primary_key=True)
    ip_segment_id = db.Column(db.Integer, db.ForeignKey('ip_segment.id'))
    IP = db.Column(db.String(32))
    status = db.Column(db.String(32))
    comment = db.Column(db.Text)
    host = db.relationship('Host', backref='ip_pool', lazy='dynamic')
    create_time = db.Column(db.DateTime, default=datetime.utcnow)


class IPSegment(db.Model):
    __tablename__ = 'ip_segment'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = db.Column(db.Integer, primary_key=True)
    ip_segment = db.Column(db.String(32))
    region_detail_id = db.Column(db.Integer, db.ForeignKey('region_detail.id'))
    status = db.Column(db.String(32))
    comment = db.Column(db.Text)
    ip_pool = db.relationship('IPPool', backref='ip_segment', lazy='dynamic')
    create_time = db.Column(db.DateTime, default=datetime.utcnow)

    def count_available_ips(self):
        return IPPool.query.filter(IPPool.ip_segment_id == self.id).filter(IPPool.status == u'可用').count()

    def count_unavailable_ips(self):
        return IPPool.query.filter(IPPool.ip_segment_id == self.id).filter(IPPool.status == u'不可用').count()


class Service(db.Model):
    __tablename__ = 'service'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True)
    dpt_id = db.Column(db.Integer, db.ForeignKey('department.id'))
    tree_id = db.Column(db.String(64))
    tree_parent = db.Column(db.String(64))
    host = db.relationship('Host', backref='service', lazy='dynamic')
    create_time = db.Column(db.DateTime, default=datetime.utcnow)


class Host(db.Model):
    __tablename__ = 'host'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = db.Column(db.Integer, primary_key=True)
    instance_id = db.Column(db.String(32))
    innerIP = db.Column(db.Integer, db.ForeignKey('ip_pool.id'))
    outerIP = db.Column(db.String(32))
    elasticIP = db.Column(db.String(32))
    hostname = db.Column(db.String(64))
    cpu = db.Column(db.String(32))
    memory = db.Column(db.String(32))
    disk = db.Column(db.String(32))
    os = db.Column(db.String(32))
    device_id = db.Column(db.Integer, db.ForeignKey('device.id'))
    user_dpt_id = db.Column(db.Integer, db.ForeignKey('department.id'))
    user_dpt = db.relationship("Department", foreign_keys=[user_dpt_id])
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    owner_dpt_id = db.Column(db.Integer, db.ForeignKey('department.id'))
    owner_dpt = db.relationship("Department", foreign_keys=[owner_dpt_id])
    ops_id = db.Column(db.Integer, db.ForeignKey('operator.id'))
    host_model = db.Column(db.String(32))
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'))
    cabinet_id = db.Column(db.Integer, db.ForeignKey('cabinet.id'))
    bill_id = db.Column(db.Integer, db.ForeignKey('bill.id'))
    create_date = db.Column(db.String(16))
    payment = db.Column(db.String(32))
    status = db.Column(db.String(16))
    comment = db.Column(db.Text)


class Operator(db.Model):
    __tablename__ = 'operator'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32))
    host = db.relationship('Host', backref='operator', lazy='dynamic')
    create_time = db.Column(db.DateTime, default=datetime.utcnow)


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True)
    fullname = db.Column(db.String(32))
    password_hash = db.Column(db.String(256))
    email = db.Column(db.String(64))
    status = db.Column(db.Boolean, default=True)
    token = db.Column(db.String(128))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    host = db.relationship('Host', backref='users', lazy='dynamic')
    create_time = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, passwd):
        self.password_hash = generate_password_hash(passwd)

    def verify_password(self, passwd):
        return check_password_hash(self.password_hash, passwd)

    def generate_auth_token(self, expiration):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id, 'username': self.name, 'role': self.role.name})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except Exception as e:
            current_app.logger.error(e)
            return None
        return User.query.get(data['id'])

    @staticmethod
    def get_auth_token_data(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except Exception as e:
            current_app.logger.error(e)
            return None
        return data


role_permission = db.Table('role_permission',
                           db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
                           db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id'), primary_key=True),
                           )

dpt_user = db.Table('dpt_user',
                    db.Column('dpt_id', db.Integer, db.ForeignKey('department.id'), primary_key=True),
                    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
                    )


class Role(db.Model):
    __tablename__ = 'roles'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')
    permissions = db.relationship('Permission', secondary=role_permission, backref=db.backref('roles', lazy='dynamic'), lazy='dynamic')
    create_time = db.Column(db.DateTime, default=datetime.utcnow)


class Permission(db.Model):
    __tablename__ = 'permissions'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True)
    alias_name = db.Column(db.String(32), unique=True)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)


class AnonymousUser(AnonymousUserMixin):
    pass


class Department(db.Model):
    __tablename__ = 'department'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True)
    token = db.Column(db.String(128))
    tree_id = db.Column(db.String(64))
    tree_parent = db.Column(db.String(64))
    service = db.relationship('Service', backref='department', lazy='dynamic')
    users = db.relationship('User', secondary=dpt_user, backref=db.backref('department', lazy='dynamic'), lazy='dynamic')
    create_time = db.Column(db.DateTime, default=datetime.utcnow)


class MonitorDomainInfo(db.Model):
    __tablename__ = 'monitor_domain_info'
    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(255))
    rd_maintainer = db.Column(db.String(255))
    cre_maintainer = db.Column(db.String(255))
    remark = db.Column(db.String(255))
    update_time = db.Column(db.DateTime)

    def __init__(self, domain, rd_maintainer, cre_maintainer, remark, update_time):
        self.domain = domain
        self.rd_maintainer = rd_maintainer
        self.cre_maintainer = cre_maintainer
        self.remark = remark
        self.update_time = update_time


class MonitorTcpConnectProbe(db.Model):
    __tablename__ = 'monitor_tcp_connect_probe'
    id = db.Column(db.Integer, primary_key=True)
    service_name = db.Column(db.String(255))
    target = db.Column(db.String(255))
    server_ip = db.Column(db.String(255))
    tcp_port = db.Column(db.Integer)
    service_owner = db.Column(db.String(255))
    update_date = db.Column(db.Date)

    def __init__(self, service_name, target, server_ip, tcp_port, service_owner, update_date):
        self.service_name = service_name
        self.target = target
        self.server_ip = server_ip
        self.tcp_port = tcp_port
        self.service_owner = service_owner
        self.update_date = update_date


"""
:----------------------------------------------------------------------------------------------------------------------------
:以下不常用的数据库表
"""


class Region(db.Model):
    __tablename__ = 'region_detail'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'))
    supplier_name = db.Column(db.String(32))
    region = db.Column(db.String(32))
    detail = db.Column(db.String(64))
    code = db.Column(db.String(32))
    comment = db.Column(db.Text)
    ip_segment = db.relationship('IPSegment', backref='region_detail', lazy='dynamic')
    cabinet = db.relationship('Cabinet', backref='region_detail', lazy='dynamic')
    device = db.relationship('Device', backref='region_detail', lazy='dynamic')
    create_time = db.Column(db.DateTime, default=datetime.utcnow)


class Supplier(db.Model):
    __tablename__ = 'supplier'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32))
    code = db.Column(db.String(32))
    contacts = db.Column(db.String(32))
    phone = db.Column(db.String(32))
    wechat = db.Column(db.String(32))
    dingtalk = db.Column(db.String(32))
    email = db.Column(db.String(64))
    regions = db.relationship('Region', backref='supplier', lazy='dynamic')
    device = db.relationship('Device', backref='supplier', lazy='dynamic')
    create_time = db.Column(db.DateTime, default=datetime.utcnow)


class CPU(db.Model):
    __tablename__ = 'cpu'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(16))
    model = db.Column(db.String(16))
    core_number = db.Column(db.String(16))
    processor_speed = db.Column(db.String(16))
    l2_cache = db.Column(db.String(16))
    l3_cache = db.Column(db.String(16))
    device = db.relationship('Device', backref='cpu', lazy='dynamic')
    create_time = db.Column(db.DateTime, default=datetime.utcnow)


class Memory(db.Model):
    __tablename__ = 'memory'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(16))
    type = db.Column(db.String(16))
    speed = db.Column(db.String(16))
    size = db.Column(db.String(16))
    device = db.relationship('Device', backref='memory', lazy='dynamic')
    create_time = db.Column(db.DateTime, default=datetime.utcnow)


class Disk(db.Model):
    __tablename__ = 'disk'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(16))
    size = db.Column(db.String(16))
    cache = db.Column(db.String(16))
    speed = db.Column(db.String(16))
    socket_type = db.Column(db.String(16))
    device = db.relationship('Device', backref='disk', lazy='dynamic')
    create_time = db.Column(db.DateTime, default=datetime.utcnow)


class Nic(db.Model):
    __tablename__ = 'nic'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(16))
    model = db.Column(db.String(32))
    speed = db.Column(db.String(16))
    device = db.relationship('Device', backref='nic', lazy='dynamic')
    create_time = db.Column(db.DateTime, default=datetime.utcnow)


class Cabinet(db.Model):
    __tablename__ = 'cabinet'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = db.Column(db.Integer, primary_key=True)
    region_detail_id = db.Column(db.Integer, db.ForeignKey('region_detail.id'))
    code = db.Column(db.String(32))
    device = db.relationship('Device', backref='cabinet', lazy='dynamic')
    host = db.relationship('Host', backref='cabinet', lazy='dynamic')
    create_time = db.Column(db.DateTime, default=datetime.utcnow)


class Brand(db.Model):
    __tablename__ = 'brand'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32))
    device_model = db.relationship('Model', backref='brand', lazy='dynamic')
    device = db.relationship('Device', backref='brand', lazy='dynamic')
    create_time = db.Column(db.DateTime, default=datetime.utcnow)


class Model(db.Model):
    __tablename__ = 'model'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32))
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'))
    device = db.relationship('Device', backref='model', lazy='dynamic')
    create_time = db.Column(db.DateTime, default=datetime.utcnow)


class Device(db.Model):
    __tablename__ = 'device'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(16))
    sn = db.Column(db.String(32))
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'))
    model_id = db.Column(db.Integer, db.ForeignKey('model.id'))
    cpu_num = db.Column(db.String(16))
    memory_num = db.Column(db.String(16))
    disk_num = db.Column(db.String(16))
    cpu_core = db.Column(db.String(16))
    memory_size = db.Column(db.String(16))
    cpu_id = db.Column(db.Integer, db.ForeignKey('cpu.id'))
    memory_id = db.Column(db.Integer, db.ForeignKey('memory.id'))
    disk_id = db.Column(db.Integer, db.ForeignKey('disk.id'))
    nic_id = db.Column(db.Integer, db.ForeignKey('nic.id'))
    socket = db.Column(db.String(32))
    region_detail_id = db.Column(db.Integer, db.ForeignKey('region_detail.id'))
    cabinet_id = db.Column(db.Integer, db.ForeignKey('cabinet.id'))
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'))
    purchase_date = db.Column(db.String(16))
    status = db.Column(db.String(16))
    host = db.relationship('Host', backref='device', lazy='dynamic')
    create_time = db.Column(db.DateTime, default=datetime.utcnow)


class Bill(db.Model):
    __tablename__ = 'bill'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = db.Column(db.Integer, primary_key=True)
    subscription_type = db.Column(db.String(32))
    instance_id = db.Column(db.String(32))
    product_code = db.Column(db.String(32))
    product_detail = db.Column(db.String(32))
    deducted_by_prepaid_card = db.Column(db.Float)
    cost_unit = db.Column(db.String(32))
    pretax_amount = db.Column(db.Float)
    deducted_by_coupons = db.Column(db.Float)
    region = db.Column(db.String(32))
    payment_amount = db.Column(db.Float)
    outstanding_amount = db.Column(db.Float)
    deducted_by_cash_coupons = db.Column(db.Float)
    product_name = db.Column(db.String(32))
    billing_type = db.Column(db.String(32))
    currency = db.Column(db.String(32))
    pretax_gross_amount = db.Column(db.Float)
    invoice_discount = db.Column(db.Float)
    host = db.relationship('Host', backref='bill', lazy='dynamic')
    create_time = db.Column(db.DateTime, default=datetime.utcnow)


class CronLog(db.Model):
    __tablename__ = 'cron_log'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = db.Column(db.Integer, primary_key=True)
    asset = db.Column(db.String(32))
    update_date = db.Column(db.String(32))
    count = db.Column(db.Integer)
