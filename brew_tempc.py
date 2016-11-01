import sys
import os
import time
import datetime
import ConfigParser
from daemon import runner

from GPIOSrc import GPIOSrc
from DGTSrc import DGTSrc
from GCMClient import GCMClient

LOCAL_PATH = os.getcwd()
CONFIG_FILE = LOCAL_PATH + '/config.cfg'
REGID_FILE = LOCAL_PATH + '/regid.txt'

def brew_tempc():

    RegIDs=''
    f = open(REGID_FILE, "r")
    RegIDs = [[line[:-1] for line in f]]
    f.close()
    print RegIDs

    if len(RegIDs) == 0:
        print "GCM Reg ID not found"
        exit()

    config = ConfigParser.ConfigParser()
    config.read(CONFIG_FILE)
    tempSource = config.get('Common', 'sensors')
    BBChart = config.get('Common', 'bbchart')


    lastAlarm = None
    
    if tempSource == 'gpio':
        tempSource = GPIOSrc()
    elif tempSource == 'usb':
        tempSource = DGTSrc()
    else:
        print "Wrong sensor type configured"
        exit()

    gcm = GCMClient()

    tempArray1 = []
    tempArray2 = []
    
    while True:
        config.read(CONFIG_FILE)
	updInterval = int( config.get('Common', 'updateinterval'))
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
                gcm.send(msgType, "%s,%s,%s,%s,%s\n" % (time.asctime(), cur_temp[0], cur_temp[1]), RegIDs[0])
            
        else:
            print "no data from sensors. Make sure you have 'dtoverlay=w1-gpio' in your /boot/config.txt"

        print "================================================="
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
