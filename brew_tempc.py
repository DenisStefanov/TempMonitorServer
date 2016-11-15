import sys
import os
import time
import datetime
import ConfigParser
from daemon import runner
import random

from GPIOSrc import GPIOSrc
from DGTSrc import DGTSrc
from GCMClient import GCMClient
from GCMXMPPClient import GCMXMPPClient

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
    BBChart = config.get('Common', 'bbchart')
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

    #gcm = GCMClient()
    gcm = GCMXMPPClient()

    tempArray1 = []
    tempArray2 = []
    
    while True:
        if gcm.serverRunning:
            config.read(CONFIG_FILE)
            AlmSuppressInerval = int( config.get('Common', 'alarmfreq'))
            AvgSamplesNum = int( config.get('Common', 'avgsamplesnum'))
            LogFileName = config.get('Common', 'logfilename')
            GCMSend = config.get('Common', 'gcmsend')
            fixit1 = config.get('Conf1', 'fixtemp')
            delta1 = float(config.get('Conf1', 'delta'))
            abstemp1 = float(config.get('Conf1', 'absolute'))
            fixit2 = config.get('Conf2', 'fixtemp')
            delta2 = float(config.get('Conf2', 'delta'))
            abstemp2 = float(config.get('Conf2', 'absolute'))

            cur_temp = tempSource.getData()
            cur_temp = [44.44, 77.77]
            if cur_temp:
                tempArray1.append(cur_temp[0])
                tempArray2.append(cur_temp[1])
                average1 = sum(tempArray1[0 - AvgSamplesNum:]) / len(tempArray1[0 - AvgSamplesNum:])
                average2 = sum(tempArray2[0 - AvgSamplesNum:]) / len(tempArray2[0 - AvgSamplesNum:])

                print "Average = ", average1, average2

                now = time.asctime()
                print now, cur_temp

                fd = open(LogFileName,'a')
                fd.write("%s,%s,%s\n" % (time.asctime(), cur_temp[0], cur_temp[1]))
                fd.close()

                msgType = "upd"

                if fixit1.lower() == "yes" and (cur_temp[0] > (average1 + delta1) or (cur_temp[0] > abstemp1)):
                    now = datetime.datetime.now()
                    if not lastAlarm or (now - lastAlarm).total_seconds() > AlmSuppressInerval:
                        msgType = 'alarma'
                        lastAlarm = now 

                if fixit2.lower() == "yes" and (cur_temp[1] > (average2 + delta2) or (cur_temp[1] > abstemp2)):
                    now = datetime.datetime.now()                    
                    if  not lastAlarm or (now - lastAlarm).total_seconds() > AlmSuppressInerval:
                        msgType = 'alarma'
                        lastAlarm = now

                if GCMSend.lower() == 'yes' or (GCMSend.lower() == 'alarm' and msgType == "alarma"):
                    gcm.send({'to': RegID, 'message_id': random_id(), \
                                  'data' : 
                              {'type': 'upd', \
                                   'time' : time.asctime(), \
                                   'tempStill' : cur_temp[0], \
                                   'tempTower' : cur_temp[1]}})
            else:
                print "no data from sensors. Make sure you have 'dtoverlay=w1-gpio' in your /boot/config.txt"

            print "================================================="
        
        gcm.process()                
        gcm.flush_queued_messages()
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
    app = MyDaemon()
    daemon_runner = runner.DaemonRunner(app)
    daemon_runner.do_action()
