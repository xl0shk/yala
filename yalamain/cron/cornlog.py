# -*- coding: utf-8 -*-
import time
from flask import current_app
from sqlalchemy import exc

from yalamain.extensions import db, apscheduler
from yalamain.models import Host, User, CronLog, MonitorTcpConnectProbe, MonitorDomainInfo


@apscheduler.task('cron', id='update_cron_log', hour=16, minute=11)
def update_cron_log():
    with apscheduler.app.app_context():
        this_day = time.strftime("%Y-%m-%d", time.localtime())
        update_date = this_day
        host_count = Host.query.count()
        monitor_domain_count = MonitorDomainInfo.query.count()
        monitor_probe_count = MonitorTcpConnectProbe.query.count()
        users_count = User.query.count()
        assets = ['host', 'domain', 'probe', 'users']
        for asset in assets:
            if asset == 'host':
                count = host_count
            if asset == 'domain':
                count = monitor_domain_count
            if asset == 'probe':
                count = monitor_probe_count
            if asset == 'users':
                count = users_count

            try:
                query_update_date = CronLog.query.filter_by(asset=asset, update_date=this_day).first()
            except exc.SQLAlchemyError as sql_err:
                current_app.logger.error('MySQL ERROR: {}.'.format(sql_err))

            if query_update_date is None:
                try:
                    cronlog = CronLog(asset=asset, update_date=update_date, count=count)
                    db.session.add(cronlog)
                    db.session.commit()
                except exc.SQLAlchemyError as sql_err:
                    current_app.logger.error('MySQL ERROR: {}.'.format(sql_err))