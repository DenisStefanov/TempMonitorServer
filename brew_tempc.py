import sys
import os
import json
import time
import datetime
import ConfigParser
from daemon import runner
import random, string
import urllib2
import sqlite3

from GPIOSrc import GPIOSrc
from DGTSrc import DGTSrc
from GCMClient import GCMClient

LOCAL_PATH = os.getcwd() + "/TempMonitorServer"
CONFIG_FILE = LOCAL_PATH + '/config.cfg'

def random_id():
    rid = ''
    for x in range(8): rid += random.choice(string.ascii_letters + string.digits)
    return rid

def brew_tempc():
    config = ConfigParser.ConfigParser()
    config.read(CONFIG_FILE)
    tempSource = config.get('Common', 'sensors')
    updInterval = int( config.get('Common', 'updateinterval'))
    db = config.get('Common', 'DBPath')

    dbconn = sqlite3.connect(db)
    dbcursor = dbconn.cursor()
    RegID = None

    if tempSource == 'gpio':
        tempSource = GPIOSrc()
    elif tempSource == 'usb':
        tempSource = DGTSrc()
    else:
        print "Wrong sensor type configured"
        exit()

    gcm = GCMClient()

    serverRunning = False

    while True:
        if serverRunning:
            cur_temp = tempSource.getData()
            #cur_temp = [44.44, 77.77]
            if cur_temp:
                now = datetime.datetime.now()                    

                dbcursor.execute("SELECT stillTemp, towerTemp, stillTempFix, towerTempFix FROM TempMonitorServer_limits")
                (abstempStill, abstempTower, fixitStill, fixitTower) =  dbcursor.fetchone()
                 
                dbcursor.execute("INSERT INTO TempMonitorServer_readings(datetime, stillTemp, towerTemp) VALUES (?, ?, ?)", [now, cur_temp[0], cur_temp[1]])
                dbconn.commit()

                print now, "Current=",cur_temp, "Limits=",abstempStill,abstempTower

                if RegID:
                    if (fixitStill and cur_temp[0] > abstempStill) or (fixitTower and cur_temp[1] > abstempTower):
                        gcm.send("alarma", "someshit", [RegID])
                else:
                    print "No Reg ID configured. No GCM."

            else:
                print "no data from sensors. Make sure you have 'dtoverlay=w1-gpio' in your /boot/config.txt"

        dbcursor.execute("SELECT serverRunning, regID FROM TempMonitorServer_config")
        (serverRunning, RegID) = dbcursor.fetchone()
        sys.stdout.flush()
        time.sleep(updInterval)

class MyDaemon():
    def __init__(self):
        self.stdin_path = '/dev/null'
        self.stdout_path = '/var/log/tempmon.log'
        self.stderr_path = '/var/log/tempmon.log'
        self.pidfile_path =  '/tmp/tempmon.pid'
        self.pidfile_timeout = 5
    def run(self):
        brew_tempc()

if __name__ == "__main__":
  
  if len(sys.argv) > 2 and sys.argv[2]=="cleandb":
    print "cleaning readings from DB, Are you sure?"
    if (raw_input().lower() =="y"):
      config = ConfigParser.ConfigParser()
      config.read(CONFIG_FILE)
      db = config.get('Common', 'DBPath')
      dbconn = sqlite3.connect(db)
      dbcursor = dbconn.cursor()
      dbcursor.execute("DELETE FROM TempMonitorServer_readings")
      dbcursor.execute("VACUUM")
      dbconn.commit()
      dbconn.close()
      

  connected = False
  while (not connected):
    try:
      urllib2.urlopen('http://google.com', timeout=5)
      connected = True
    except:
      time.sleep(1)

  app = MyDaemon()
  daemon_runner = runner.DaemonRunner(app)
  daemon_runner.do_action()



