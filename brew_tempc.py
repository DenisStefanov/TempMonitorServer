import signal
import sys
import time
import os
import glob
import time
import datetime
import ConfigParser
import numpy as np
from daemon import runner

from GPIOSrc import GPIOSrc
from DGTSrc import DGTSrc
from chart import brewChart
from GCMClient import GCMClient

CONFIG_FILE = '/home/pi/TempMonitorServer/config.cfg'

def brew_tempc():
    config = ConfigParser.ConfigParser()

    config.read(CONFIG_FILE)
    updInterval = int( config.get('Common', 'UpdateInterval'))
    AlmSuppressInerval = int( config.get('Common', 'AlarmFreq'))
    AvgSamplesNum = int( config.get('Common', 'AvgSamplesNum'))
    LogFileName = config.get('Common', 'LogFileName')

    RegIDs=''
    f = open("/tmp/regid.txt", "r")
    RegIDs = [[line[:-1] for line in f]]
    f.close()
    print RegIDs

    if len(RegIDs) == 0:
        print "GCM Reg ID not found"
        exit()

    tempSource = config.get('Common', 'Sensors')
    BBChart = config.get('Common', 'BBChart')
    GCMSend = config.get('Common', 'GCMSend')

    lastAlarm1 = lastAlarm2 = None
    
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
    
    #for rec in sensors.split('\n'):
        #print rec
    #    if rec:
    #        tempArray1.append(float(rec.split(',')[1]))            
    #        tempArray2.append(float(rec.split(',')[2]))

    if BBChart.lower() == 'yes':
        chart = brewChart(tempSource)
    else:
        while True:
            config.read('config.cfg')
            GCMSend = config.get('Common', 'GCMSend')

            fixit1 = config.get('Conf1', 'FixTemp')
            delta1 = float(config.get('Conf1', 'Delta'))
            abstemp1 = float(config.get('Conf1', 'Absolute'))

            fixit2 = config.get('Conf2', 'FixTemp')
            delta2 = float(config.get('Conf2', 'Delta'))
            abstemp2 = float(config.get('Conf2', 'Absolute'))

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
                    if not lastAlarm1 or (now - lastAlarm1).total_seconds() > AlmSuppressInerval:
                        msgType = 'alarma'
                        lastAlarm1 = now 

                if fixit2.lower() == "yes" and (cur_temp[1] > (average2 + delta2) or (cur_temp[1] > abstemp2)):
                    now = datetime.datetime.now()                    
                    if  not lastAlarm2 or (now - lastAlarm2).total_seconds() > AlmSuppressInerval:
                        msgType = 'alarma'
                        lastAlarm2 = now
                    

                if GCMSend.lower() == 'yes' or (GCMSend.lower() == 'alarm' and msgType == "alarma"):
                    gcm.send(msgType, "%s,%s,%s\n" % (time.asctime(), cur_temp[0], cur_temp[1]), RegIDs[0])
                
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
