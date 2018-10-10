import sys
import os
import time, threading
import datetime
import ConfigParser
from daemon import runner
import random, string

import RPi.GPIO as GPIO
from GPIOSrc import GPIOSrc
from DGTSrc import DGTSrc
from GCMClient import GCMClient
from GCMXMPPClient import GCMXMPPClient
from PowerControl import PowerControl

CONFIG_FILE = os.getcwd() + "/TempMonitorServer/config.cfg"

def random_id():
  rid = ''
  for x in range(8): rid += random.choice(string.ascii_letters + string.digits)
  return rid

def brew_tempc():
    config = ConfigParser.ConfigParser()
    config.read(CONFIG_FILE)
    tempSource = config.get('Common', 'sensors')
    RegID = config.get('Common', 'regid')
    updInterval = int( config.get('Common', 'updateinterval'))

    if len(RegID) == 0:
        print "GCM Reg ID not found"
        exit()

    lastAlarm = None
    
    if tempSource == 'gpio':
        tempSource = GPIOSrc()
    elif tempSource == 'usb':
        tempSource = DGTSrc()
    else:
        print "Wrong sensor type configured"
        exit()

    gcm = GCMXMPPClient()

    stillTempList = []
    towerTempList = []
    lastLevelAlarm = None

    threading.Timer(updInterval, sendToClient(True)).start()

    while True:
        if gcm.serverRunning:
            config.read(CONFIG_FILE)
            GCMSend = config.get('Common', 'gcmsend')
            fixitStill = config.get('ServerConfig', 'fixtempStill')
            abstempStill = float(config.get('ServerConfig', 'absoluteStill'))
            deltaStill = float(config.get('ServerConfig', 'deltastill'))
            fixitTower = config.get('ServerConfig', 'fixtempTower')
	    fixitTowerByPower = config.get('ServerConfig', 'fixtemptowerbypower')
	    fixitStillByPower = config.get('ServerConfig', 'fixtempstillbypower')
            abstempTower = float(config.get('ServerConfig', 'absoluteTower'))
            deltaTower = float(config.get('ServerConfig', 'deltatower'))

            res = tempSource.getData()
            cur_temp = [res[0] if len(res) > 0 else -1, res[1] if len(res) > 1 else -1]
            if cur_temp:

                stillTempList.append(cur_temp[0])
                towerTempList.append(cur_temp[1])

                if len(stillTempList) >= 10:
                  stillTempList.pop(0)

                if len(towerTempList) >= 10:
                  towerTempList.pop(0)

                stillTempAvg = round(sum(stillTempList) / len(stillTempList), 2)
                towerTempAvg = round(sum(towerTempList) / len(towerTempList), 2)
                msgType = "upd"

                stillAlarm = fixitStill.lower() == "true" and (abstempStill == 0 and cur_temp[0] > stillTempAvg + deltaStill or abstempStill != 0 and cur_temp[0] > abstempStill)
		towerAlarm = fixitTower.lower() == "true" and (abstempTower == 0 and cur_temp[1] > towerTempAvg + deltaTower or abstempTower != 0 and cur_temp[1] > abstempTower)

                if stillAlarm or towerAlarm:
		  if ((towerAlarm and fixitTowerByPower.lower() == "true") or (stillAlarm and fixitStillByPower.lower() == "true")):
	            pc = PowerControl(18, GPIO.OUT,  GPIO.PUD_OFF)
                    pc.PowerCtl(GPIO.HIGH)
		  else:
		    msgType = 'alarma' 
                  print "Still diff = %s Tower diff = %s" % (cur_temp[0] - stillTempAvg, cur_temp[1] - towerTempAvg) 
                else if ((fixitTowerByPower.lower() == "true") or (fixitStillByPower.lower() == "true")):
                  pc = PowerControl(18, GPIO.OUT,  GPIO.PUD_OFF)
                  pc.PowerCtl(GPIO.LOW)

		pc = PowerControl(25, GPIO.IN,  GPIO.PUD_UP)
     	     	state=pc.PowerRead()
                now = time.time()

                if state == GPIO.LOW:
                  lastLevelAlarm = None

                if state == GPIO.HIGH and (not lastLevelAlarm or now - lastLevelAlarm > 10 * 60):
                  msgType = 'alarma'
                  lastLevelAlarm = now

                print time.asctime(), "Current=",cur_temp, "Average=", stillTempAvg, towerTempAvg, "Limits=",abstempStill,abstempTower, "LiqLevel=", state

		def sendToClient(reschedule):
  		  if GCMSend.lower() == 'yes':
		    gcm.send({'to': RegID, 'message_id': random_id(), \
	   #        'collapse_key' : msgType, \
        	    'data' : {'type': msgType, \
		    'LastUpdated' : time.asctime(), \
		    'tempStill' : cur_temp[0], \
	            'tempTower' : cur_temp[1], \
                    'liqLevelSensor'  :"true" if state== GPIO.HIGH else "false"}})
		  if reschedule:
		    threading.Timer(updInterval, sendToClient(True)).start()
	
		if ((GCMSend.lower() == 'alarm') and (msgType == "alarma")):
		  sendToClient(False)

            else:
                print "no data from sensors. Make sure you have 'dtoverlay=w1-gpio' in your /boot/config.txt"

        
        gcm.client.Process(1)                
        sys.stdout.flush()
#        time.sleep(updInterval)

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

  app = MyDaemon()
  daemon_runner = runner.DaemonRunner(app)
  daemon_runner.do_action()
