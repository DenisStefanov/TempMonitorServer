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
from waterControl import WaterControl, waterOpen, waterClose
import waterControl

from ADC import adc

DIMMER_FILE = os.getcwd() + "/TempMonitorServer/dimval.txt"
CONFIG_FILE = os.getcwd() + "/TempMonitorServer/config.cfg"

stillTempList = []
towerTempList = []
scenTimeStart = [None]*20

def random_id():
    rid = ''
    for x in range(8): rid += random.choice(string.ascii_letters + string.digits)
    return rid

def reconfigScenario(scenario, scenid, val):
  config = ConfigParser.RawConfigParser()
  config.read(CONFIG_FILE)
  config.set(scenario, scenid, val)
  with open(CONFIG_FILE, 'wb') as configfile:
    config.write(configfile)

def brew_tempc(gcm):
    global stillTempList, towerTempList
    config = ConfigParser.ConfigParser()
    config.read(CONFIG_FILE)
    tempSource = config.get('Common', 'sensors')
    updInterval = int( config.get('Common', 'updateinterval'))
    ScenarioToday = config.get('Common', 'ScenarioToday')
    fakeTempData = map(float, config.get('Common', 'fakeTempData').split(',')[:3])
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
      os.system("%s %s %s", ("cp ", "/var/log/tempmon.log", "/var/log/tempmon.log_" + datetime.datetime.now().strftime("%d%m%Y%H%M%S")))
      sys.exit(1)

    if gcm.serverRunning:
      res = tempSource.getData() if config.get('Common', 'fakeTempData').split(',')[3]!="Active" else fakeTempData 
      if res:
        cur_temp = [res[0] if len(res) > 0 else -1, res[1] if len(res) > 1 else -1, res[2] if len(res) > 2 else -1]
        stillTempList.append(cur_temp[stillSensorIDX])
        towerTempList.append(cur_temp[towerSensorIDX])
      
        #if len(stillTempList) >= 10:
        #  stillTempList.pop(0)
        #if len(towerTempList) >= 10:
        #  towerTempList.pop(0)
      
        stillTempAvg = round(sum(stillTempList[-10:]) / 10, 2)
        towerTempAvg = round(sum(towerTempList[-10:]) / 10, 2)
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

        cooler = pc17.PowerRead()
        heat   = pc18.PowerRead()
        liqLevel = pc25.PowerRead()

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

        # Scenarios
        ScenarioTempConfig=[]
        scenNum = 0
        while (True):
            try:
                ScenarioTempConfig.append(config.get(ScenarioToday, 'Temperature%s' % (scenNum)).split(';'))
                scenActive = True if ScenarioTempConfig[scenNum][0] == 'Active' else False
                scenTempStillMin = int(ScenarioTempConfig[scenNum][1].split(',')[0])
                scenTempStillMax = int(ScenarioTempConfig[scenNum][1].split(',')[1])
                scenTempTowerMin = int(ScenarioTempConfig[scenNum][2].split(',')[0])
                scenTempTowerMax = int(ScenarioTempConfig[scenNum][2].split(',')[1])
                exitCriterias = ScenarioTempConfig[scenNum][3].split('=')[1].split(',')
                scenWaterFun = ScenarioTempConfig[scenNum][4]
                scenDimmer = ScenarioTempConfig[scenNum][5].split('=')[1]
                scenDirect = ScenarioTempConfig[scenNum][6]
                print ScenarioTempConfig[scenNum]
            except Exception, e:
                break

            #print cur_temp[stillSensorIDX], cur_temp[towerSensorIDX], scenTempStillMin, scenTempStillMax, scenTempTowerMin, scenTempTowerMax
            if (scenActive and
                ((cur_temp[stillSensorIDX] > scenTempStillMin and cur_temp[stillSensorIDX] < scenTempStillMax) or
                 (cur_temp[towerSensorIDX] > scenTempTowerMin and cur_temp[towerSensorIDX] < scenTempTowerMax))):

                if scenTimeStart[scenNum] is None:
                    scenTimeStart[scenNum] = datetime.datetime.now() 

                print "Run scenario #%s. %s <> %s; %s <> %s direct = %s TimeStart = %s" % \
                    (scenNum, scenTempStillMin, scenTempStillMax, scenTempTowerMin, scenTempTowerMax, scenDirect, scenTimeStart[scenNum])

                f = open(DIMMER_FILE, "w")
                f.write(str(int(int(scenDimmer)*1.2)))
                f.close()
                wc = WaterControl()
                if ((wc.angle == 0 and scenWaterFun == "waterOpen") or (wc.angle == 180 and scenWaterFun == "waterClose")):
                    print "Updating WaterControl %s. Current angle=%d" % (scenWaterFun, wc.angle) 
                    threading.Thread(target=getattr(waterControl, scenWaterFun), args=(gcm, RegID, 100)).start()
                else:
                    #print "Skip WaterControl, as it is already set to %s. Angle=%d" % (scenWaterFun, wc.angle)
                    pass
                
                #here we need to close all the valves except 'scenDirect' one
                pcHead = PowerControl(12, GPIO.OUT,  GPIO.PUD_OFF)
                pcBody = PowerControl(16, GPIO.OUT,  GPIO.PUD_OFF)
                pcTail = PowerControl(20, GPIO.OUT,  GPIO.PUD_OFF)
                pcHead.PowerCtl(GPIO.LOW if scenDirect=='Head' else GPIO.HIGH)
                pcBody.PowerCtl(GPIO.LOW if scenDirect=='Body' else GPIO.HIGH)
                pcTail.PowerCtl(GPIO.LOW if scenDirect=='Tail' else GPIO.HIGH)
                for j in range(1, scenNum+1): #mark all previous scenarios inactive
                    if ScenarioTempConfig[j-1][0] == 'Active':
                        print "Scenario %d to be inactivated" % (j-1)
                        reconfigScenario(ScenarioToday, "temperature%s" % (j-1),
                                         "%s;%s;%s;%s;%s;%s;%s" % ("NotActive",
                                                                ScenarioTempConfig[j-1][1], ScenarioTempConfig[j-1][2],
                                                                ScenarioTempConfig[j-1][3], ScenarioTempConfig[j-1][4],
                                                                ScenarioTempConfig[j-1][5], ScenarioTempConfig[j-1][6]))
                if (liqLevel == GPIO.HIGH) or \
                    ('TempGrowing' in exitCriterias and len(towerTempList) > 10 \
                     and round(cur_temp[towerSensorIDX], 2) >= round(sum(towerTempList[-10:]) / 10, 2) + deltaTower) or \
                    ('Time' in exitCriterias and scenTimeStart[scenNum] + datetime.timedelta(minutes=int(exitCriterias[1])) < datetime.datetime.now()): 
                    print "Changing scenario %d %s Average=%d CurTemp10=%d Average+dt=%d" % \
                        (j, exitCriterias, round(cur_temp[towerSensorIDX], 1),
                         round(cur_temp[towerSensorIDX], 2), round(sum(towerTempList[-10:]) / 10, 2) + deltaTower)
                    reconfigScenario(ScenarioToday, "temperature%s"%(j),
                                     "%s;%s;%s;%s;%s;%s;%s" % ("NotActive",
                                                            ScenarioTempConfig[j][1], ScenarioTempConfig[j][2],
                                                            ScenarioTempConfig[j][3], ScenarioTempConfig[j][4],
                                                            ScenarioTempConfig[j][5], ScenarioTempConfig[j][6]))

                break;
            scenNum+=1

        if stillAlarm or towerAlarm:
            if ((towerAlarm and fixitTowerByPower.lower() == "true") or (stillAlarm and fixitStillByPower.lower() == "true")):
                pc18.PowerCtl(GPIO.HIGH)
                print "Turn OFF Still diff = %s Tower diff = %s" % (cur_temp[stillSensorIDX] - stillTempAvg, cur_temp[towerSensorIDX] - towerTempAvg) 
            else:
                msgType = 'alarma'
        elif ((fixitTowerByPower.lower() == "true") or (fixitStillByPower.lower() == "true")):
            pc18.PowerCtl(GPIO.LOW)
            print "Turn ON Still diff = %s Tower diff = %s" % (cur_temp[stillSensorIDX] - stillTempAvg, cur_temp[towerSensorIDX] - towerTempAvg) 
              
        if liqLevel == GPIO.HIGH:
            msgType = 'alarma'

        if cur_temp[coolerSensorIDX] > 50:
            msgType = 'alarma'

	#hadc = adc()
	pressureVal = 0 #hadc.read(pressureSensorIDX)
	            
        print time.asctime(), "Cur=",cur_temp, "AVG=", stillTempAvg, towerTempAvg, \
                                    "Diffs=", cur_temp[stillSensorIDX] - stillTempAvg, cur_temp[towerSensorIDX] - towerTempAvg, \
                                    "Limits=",abstempStill,abstempTower, \
                                    "LiqLevel=", liqLevel, "pressure=", pressureVal, "MsgType=", msgType, "\n"
      
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
        os.system("%s %s %s" % ("cp ", "/var/log/tempmon.log", "/var/log/tempmon.log_" + datetime.datetime.now().strftime("%d%m%Y%H%M%S")))
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
