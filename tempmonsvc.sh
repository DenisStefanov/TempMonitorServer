#! /bin/sh
# /etc/init.d/tempmonsvc

### BEGIN INIT INFO
# Provides:          tempmonsvc
# Required-Start:    $remote_fs $syslog
# Required-Stop:     $remote_fs $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: TempMonServer
# Description:       Temp Monitoring Server
### END INIT INFO


# Carry out specific functions when asked to by the system
case "$1" in
  start)
    echo "Starting TempMonitorServer"
    cd /home/pi/
    python /home/pi/TempMonitorServer/brew_tempc.py start
    ;;
  stop)
    echo "Stopping TempMonitorServer"
    python /home/pi/TempMonitorServer/brew_tempc.py stop
    ;;
  *)
    echo "Usage: /etc/init.d/tempmonsvc {start|stop}"
    exit 1
    ;;
esac

exit 0 
