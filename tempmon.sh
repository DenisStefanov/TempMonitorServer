#!/bin/sh
### BEGIN INIT INFO
# Provides:          tempmon
# Required-Start:    $local_fs
# Required-Stop:     $local_fs
# Default-Start:     
# Default-Stop:      
# X-Interactive:     false
# Short-Description: TempMonitorServer init script
# Description:       Start/stop a script
### END INIT INFO

DESC="TempMonitorServer init script"
NAME=tempmon

DAEMON=`which python`
DAEMON_OPTS="/home/pi/TempMonitorServer/brew_tempc.py"

PIDFILE="/var/run/${NAME}.pid"
LOGFILE="/var/log/${NAME}.log"

START_OPTS="--start --background --make-pidfile --pidfile ${PIDFILE} --exec ${DAEMON} ${DAEMON_OPTS}"
STOP_OPTS="--stop --pidfile ${PIDFILE}"

do_start()
{
   echo "starting!";
   start-stop-daemon $START_OPTS >> $LOGFILE
   echo "$NAME."
}

do_stop()
{
   echo "stopping!"
   start-stop-daemon $STOP_OPTS
   echo "$NAME."
   rm -f $PIDFILE
}


case "$1" in
   start)
     do_start
     ;;
   stop)
     do_stop
     ;;
esac

exit 0