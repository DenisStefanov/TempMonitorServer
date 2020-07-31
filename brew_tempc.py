import sys
import os
import time, threading
import datetime
import ConfigParser
from daemon import runner
import random, string

import RPi.GPIO as GPIO
from GCMXMPPClient import GCMXMPPClient
from PowerControl import PowerControl
from ADC import adc

DIMMER_FILE = os.getcwd() + "/TempMonitorServer/dimval.txt"
CONFIG_FILE = os.getcwd() + "/TempMonitorServer/config.cfg"

stillTempList = []
towerTempList = []

def random_id():
    rid = ''
    for x in range(8): rid += random.choice(string.ascii_letters + string.digits)
    return rid

def brew_tempc(gcm):
    global stillTempList, towerTempList
    config = ConfigParser.ConfigParser()
    config.read(CONFIG_FILE)
    tempSource = config.get('Common', 'sensors')
    updInterval = int( config.get('Common', 'updateinterval'))
    fixitStill = config.get('ServerConfig', 'fixtempstill')
    abstempStill = float(config.get('ServerConfig', 'absolutestill'))
    deltaStill = float(config.get('ServerConfig', 'deltastill'))
    fixitTower = config.get('ServerConfig', 'fixtemptower')
    fixitTowerByPower = config.get('ServerConfig', 'fixtemptowerbypower')
    fixitStillByPower = config.get('ServerConfig', 'fixtempstillbypower')
    abstempTower = float(config.get('ServerConfig', 'absolutetower'))
    deltaTower = float(config.get('ServerConfig', 'deltatower'))
    stillSensorIDX = int( config.get('ServerConfig', 'stilltempsensoridx'))
    towerSensorIDX = int( config.get('ServerConfig', 'towertempsensoridx'))
    coolerSensorIDX = int( config.get('ServerConfig', 'coolertempsensoridx'))
    pressureSensorIDX = int( config.get('ServerConfig', 'pressuresensoridx'))
    RegID = config.get('Common', 'regid')

    if len(RegID) == 0:
        print "GCM Reg ID not found"
        sys.exit(1)
        
    if tempSource == 'gpio':
        from GPIOSrc import GPIOSrc
        tempSource = GPIOSrc()
    elif tempSource == 'usb':
        from DGTSrc import DGTSrc
        tempSource = DGTSrc()
    else:
        print "Wrong sensor type configured"
        sys.exit(1)

    if os.environ["GCMDisconnected"] != "True":
      threading.Timer(updInterval, brew_tempc, [gcm]).start()
    else:
      print "DISCONNECTED, NOT Reconnecting. In monit we trust" 
      sys.exit(1)

    if gcm.serverRunning:
      res = tempSource.getData()
      if res:
        cur_temp = [res[0] if len(res) > 0 else -1, res[1] if len(res) > 1 else -1, res[2] if len(res) > 2 else -1]
        stillTempList.append(cur_temp[stillSensorIDX])
        towerTempList.append(cur_temp[towerSensorIDX])
      
        if len(stillTempList) >= 10:
          stillTempList.pop(0)
      
        if len(towerTempList) >= 10:
          towerTempList.pop(0)
      
        stillTempAvg = round(sum(stillTempList) / len(stillTempList), 2)
        towerTempAvg = round(sum(towerTempList) / len(towerTempList), 2)
        msgType = "upd"
        
        stillAlarm = fixitStill.lower() == "true" and \
                     (abstempStill == 0 and cur_temp[stillSensorIDX] > stillTempAvg + deltaStill or \
                      abstempStill != 0 and cur_temp[stillSensorIDX] > abstempStill)
	towerAlarm = fixitTower.lower() == "true" and \
                     (abstempTower == 0 and cur_temp[towerSensorIDX] > towerTempAvg + deltaTower or \
                      abstempTower != 0 and cur_temp[towerSensorIDX] > abstempTower)

	pc17 = PowerControl(17, GPIO.OUT,  GPIO.PUD_OFF) #cooler power
        pc18 = PowerControl(18, GPIO.OUT,  GPIO.PUD_OFF) #heat
        pc25 = PowerControl(25, GPIO.IN,  GPIO.PUD_UP)   #level sensor
        
        if cur_temp[coolerSensorIDX] > 45:
            pc17.PowerCtl(GPIO.LOW)
        if cur_temp[coolerSensorIDX] < 35:
            pc17.PowerCtl(GPIO.HIGH)

        dimval = 4;
        try:
            with open(DIMMER_FILE, "r") as f:
                dimval = int(f.read())
        except:
            pass

        pc18.PowerCtl(GPIO.LOW if dimval > 5 else GPIO.HIGH)
            
        if stillAlarm or towerAlarm:
            if ((towerAlarm and fixitTowerByPower.lower() == "true") or (stillAlarm and fixitStillByPower.lower() == "true")):
                pc18.PowerCtl(GPIO.HIGH)
                print "Turn OFF Still diff = %s Tower diff = %s" % (cur_temp[stillSensorIDX] - stillTempAvg, cur_temp[towerSensorIDX] - towerTempAvg) 
            else:
                msgType = 'alarma'
        elif ((fixitTowerByPower.lower() == "true") or (fixitStillByPower.lower() == "true")):
            pc18.PowerCtl(GPIO.LOW)
            print "Turn ON Still diff = %s Tower diff = %s" % (cur_temp[stillSensorIDX] - stillTempAvg, cur_temp[towerSensorIDX] - towerTempAvg) 
      
        heat = pc18.PowerRead()
        liqLevel = pc25.PowerRead()
        cooler = pc17.PowerRead()
        
        if liqLevel == GPIO.HIGH:
            msgType = 'alarma'

        if cur_temp[coolerSensorIDX] > 50:
            msgType = 'alarma'

	hadc = adc()
	pressureVal = hadc.read(pressureSensorIDX)
	            
        print time.asctime(), "Cur=",cur_temp, "AVG=", stillTempAvg, towerTempAvg, \
                                    "Diffs=", cur_temp[stillSensorIDX] - stillTempAvg, cur_temp[towerSensorIDX] - towerTempAvg, \
                                    "Limits=",abstempStill,abstempTower, \
                                    "LiqLevel=", liqLevel, "pressure=", pressureVal, "MsgType=", msgType
      
        gcm.send({'to': RegID, 'message_id': random_id(), "time_to_live" : 60, \
                  #collapse_key' : msgType, \
                  'data' : {'type': msgType, \
                            'LastUpdated' : time.asctime(), \
                            'tempStill' : cur_temp[stillSensorIDX], \
                            'tempTower' : cur_temp[towerSensorIDX], \
                            'tempCooler' : cur_temp[coolerSensorIDX], \
                            'liqLevelSensor'  :"true" if liqLevel == GPIO.HIGH else "false", \
                            'heatGPIO' : "Off" if heat == GPIO.HIGH else "On", \
                            'coolerGPIO' : "Off" if cooler == GPIO.HIGH else "On", \
			    'pressureVal' : pressureVal }})
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

    os.system("sudo killall pwmcontrol")

    for gpio in (17, 18, 27, 22):
      pc = PowerControl(gpio, GPIO.OUT,  GPIO.PUD_OFF)
      pc.PowerCtl(GPIO.HIGH)
      print "set gpio to high", gpio

    os.system(os.getcwd() + "/TempMonitorServer/pwmcontrol &")

  if sys.argv[1] == 'stop':
    os.environ["GCMDisconnected"] = "True"
    os.system("sudo killall pwmcontrol")
    os.system("ps aux | grep ADCRead | grep -v 'grep' | awk '{print $2}' | xargs kill")
      
  app = MyDaemon()
  daemon_runner = runner.DaemonRunner(app)
  daemon_runner.do_action()
