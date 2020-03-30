#!/bin/bash
#--------------------------------------------------
# yala项目的启动、重启、停止脚本，不一定适用于其他项目。
#--------------------------------------------------

PROJECT_NAME="yala"
PROJECT_PORT=30010
PID_FILE="/var/run/${PROJECT_NAME}.pid"
CPU_CORE=`grep -c ^processor /proc/cpuinfo`

check_running()
{
    pid=`cat ${PID_FILE}`
    ps aux | grep ${pid} | grep -q ${PROJECT_NAME}
    echo $?
}


start()
{
    cd `dirname $0`
    pipenv run gunicorn -w ${CPU_CORE} -b 0.0.0.0:${PROJECT_PORT} wsgi:app -p ${PID_FILE} -D

    sleep 2

    res=`check_running`

    if [[ ${res} -eq 0 ]];then
        echo "${PROJECT_NAME} Start Success."
    else
        echo "${PROJECT_NAME} Start Failed."
        rm -f ${PROJECT_NAME}
    fi
}


stop()
{
    if [[ -f ${PID_FILE} ]];then
        res=`check_running`
        if [[ ${res} -eq 0 ]];then
            pid=`cat ${PID_FILE}`
            kill ${pid}
            sleep 2
            res=`ps aux | grep ${PROJECT_NAME} | grep -v 'grep'`
            if [[ $? -ne 0 ]];then
                echo "${PROJECT_NAME} Stop Success."
            else
                kill -9 ${pid}
                rm -f ${PID_FILE}
                echo "${PROJECT_NAME} Force Stop Success."
            fi
        else
            echo "${PID_FILE} exists, but ${PROJECT_NAME} not running"
            rm -f ${PID_FILE}
        fi
    else
        echo "${PROJECT_NAME} is not running."
    fi

}


usage()
{
    echo "$0 stop"
    echo "$0 start"
    echo "$0 restart"
}

if [[ $# -ne 1 ]];then
    usage
    exit 1
fi

case $1 in
    start)
        start;;
    stop)
        stop;;
    restart)
        stop && sleep 2 && start;;
    *)
        usage && exit 1
esac
