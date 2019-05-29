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

lastLevelAlarm = None
stillTempList = []
towerTempList = []

def random_id():
    rid = ''
    for x in range(8): rid += random.choice(string.ascii_letters + string.digits)
    return rid

def brew_tempc(gcm):
    global lastLevelAlarm, stillTempList, towerTempList
    config = ConfigParser.ConfigParser()
    config.read(CONFIG_FILE)
    tempSource = config.get('Common', 'sensors')
    updInterval = int( config.get('Common', 'updateinterval'))
    GCMSend = config.get('Common', 'gcmsend')
    fixitStill = config.get('ServerConfig', 'fixtempStill')
    abstempStill = float(config.get('ServerConfig', 'absoluteStill'))
    deltaStill = float(config.get('ServerConfig', 'deltastill'))
    fixitTower = config.get('ServerConfig', 'fixtempTower')
    fixitTowerByPower = config.get('ServerConfig', 'fixtemptowerbypower')
    fixitStillByPower = config.get('ServerConfig', 'fixtempstillbypower')
    abstempTower = float(config.get('ServerConfig', 'absoluteTower'))
    deltaTower = float(config.get('ServerConfig', 'deltatower'))
    RegID = config.get('Common', 'regid')

    if len(RegID) == 0:
        print "GCM Reg ID not found"
        sys.exit(1)
        
    if tempSource == 'gpio':
        tempSource = GPIOSrc()
    elif tempSource == 'usb':
        tempSource = DGTSrc()
    else:
        print "Wrong sensor type configured"
        sys.exit(1)

    if os.environ["GCMDisconnected"] != "True":
      print "Schedule new thread"
      threading.Timer(updInterval, brew_tempc, [gcm]).start()
    else:
      print "DISCONNECTED, NOT Reconnecting. In monit we trust"    
      sys.exit(1)

    if gcm.serverRunning:
      res = tempSource.getData()
      if res:
        cur_temp = [res[0] if len(res) > 0 else -1, res[1] if len(res) > 1 else -1, res[2] if len(res) > 2 else -1]
        stillTempList.append(cur_temp[0])
        towerTempList.append(cur_temp[1])
      
        if len(stillTempList) >= 10:
          stillTempList.pop(0)
      
        if len(towerTempList) >= 10:
          towerTempList.pop(0)
      
        stillTempAvg = round(sum(stillTempList) / len(stillTempList), 2)
        towerTempAvg = round(sum(towerTempList) / len(towerTempList), 2)
        msgType = "upd"
        
        stillAlarm = fixitStill.lower() == "true" and \
                     (abstempStill == 0 and cur_temp[0] > stillTempAvg + deltaStill or \
                      abstempStill != 0 and cur_temp[0] > abstempStill)
	towerAlarm = fixitTower.lower() == "true" and \
                     (abstempTower == 0 and cur_temp[1] > towerTempAvg + deltaTower or \
                      abstempTower != 0 and cur_temp[1] > abstempTower)
        
        if stillAlarm or towerAlarm:
            if ((towerAlarm and fixitTowerByPower.lower() == "true") or (stillAlarm and fixitStillByPower.lower() == "true")):
                pc = PowerControl(18, GPIO.OUT,  GPIO.PUD_OFF)
                pc.PowerCtl(GPIO.HIGH)
                print "Turn OFF Still diff = %s Tower diff = %s" % (cur_temp[0] - stillTempAvg, cur_temp[1] - towerTempAvg) 
            else:
                msgType = 'alarma'
        elif ((fixitTowerByPower.lower() == "true") or (fixitStillByPower.lower() == "true")):
            pc = PowerControl(18, GPIO.OUT,  GPIO.PUD_OFF)
            pc.PowerCtl(GPIO.LOW)
            print "Turn ON Still diff = %s Tower diff = %s" % (cur_temp[0] - stillTempAvg, cur_temp[1] - towerTempAvg) 
      
        pc = PowerControl(25, GPIO.IN,  GPIO.PUD_UP)
        state=pc.PowerRead()
        if state == GPIO.LOW:
            lastLevelAlarm = None
        
        if state == GPIO.HIGH and (not lastLevelAlarm or (lastLevelAlarm + 10 * 60 < time.time())):
            msgType = 'alarma'
            lastLevelAlarm = time.time()
          
        print time.asctime(), "Current=",cur_temp, "Average=", stillTempAvg, towerTempAvg, "Limits=",abstempStill,abstempTower, "LiqLevel=", state
      
        if ((GCMSend.lower() == 'alarm' and msgType == "alarma") or (GCMSend.lower() == 'yes') ):
            gcm.send({'to': RegID, 'message_id': random_id(), "time_to_live" : 60, \
                      #collapse_key' : msgType, \
                      'data' : {'type': msgType, \
                                'LastUpdated' : time.asctime(), \
                                'tempStill' : cur_temp[0], \
                                'tempTower' : cur_temp[1], \
                                'liqLevelSensor'  :"true" if state== GPIO.HIGH else "false"}})

	#pc = PowerControl(XXX, GPIO.OUT,  GPIO.PUD_OFF) #cooler temp sensor
	#pc.PowerCtl(GPIO.LOW if cur_temp[2] > 60 else GPIO.HIGH))

      else:
        print "no data from sensors. Make sure you have 'dtoverlay=w1-gpio' in your /boot/config.txt"
      
    gcm.client.Process(1)
    sys.stdout.flush()

class MyDaemon():
    def __init__(self):
        self.stdin_path = '/dev/null'
        self.stdout_path = '/var/log/tempmon.log'
        self.stderr_path = '/var/log/tempmon.log'
        self.pidfile_path =  '/tmp/tempmon.pid'
        self.pidfile_timeout = 5
    def run(self):
        gcm = GCMXMPPClient()
        brew_tempc(gcm)

if __name__ == "__main__":

  if sys.argv[1] == 'start':
    os.environ["GCMDisconnected"] = "False"
    for gpio in (17, 18, 27, 22):
      pc = PowerControl(gpio, GPIO.OUT,  GPIO.PUD_OFF)
      pc.PowerCtl(GPIO.HIGH)
      print "set gpio to high", gpio
    os.system(os.getcwd() + "/TempMonitorServer/pwmcontrol &")

  if sys.argv[1] == 'stop':
    os.environ["GCMDisconnected"] = "True"
    os.system("sudo killall pwmcontrol")
      
  app = MyDaemon()
  daemon_runner = runner.DaemonRunner(app)
  daemon_runner.do_action()
