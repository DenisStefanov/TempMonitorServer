import signal
import sys
import subprocess
import time
from pylab import *
#import draw_plot
import random
import numpy as np
import pyglet
import ConfigParser

import datetime
import matplotlib.pyplot as plt
from matplotlib import dates
from GCMClient import GCMClient

sensors = []
#g_FixedT = [99,99]
#g_CurT   = [0,0]
#g_N = [0.2, 20]
INTERVAL = 5000


#class eventHandler:
    #def fixTemp(self, event):
    #    print "Button click event = %s" % event
#	global g_FixedT
#	g_FixedT = g_CurT
#	print g_CurT, g_FixedT


class brewChart(object):
    def __init__(self, tempSource):
        self.config = ConfigParser.ConfigParser()

        self.config.read('config.cfg')
        self.updInterval = int( self.config.get('Common', 'UpdateInterval'))
        self.filename = self.config.get('Common', 'LogFileName')
        self.GCMSend = self.config.get('Common', 'GCMSend')
        self.data = self.read_data()
        self.tempSource = tempSource
        self.tempArray1 = []
        self.tempArray2 = []
        self.lastAlarm1 = None
        self.lastAlarm2 = None
        self.gcm = GCMClient()
        self.AlmSuppressInerval = int( self.config.get('Common', 'AlarmFreq'))
        
        self.RegIDs = [self.config.get('Common', 'RegIDs').split(',')]
        if not self.RegIDs:
            f = open("/tmp/regid.txt", "r")
            self.RegIDs = [[line[:-1]] for line in f]
            f.close()
        
        self.AvgSamplesNum = int(self.config.get('Common', 'AvgSamplesNum'))
        self.create_chart()
        grid(b=True, which='major', color='b', linestyle='-')

        # fixT = Button(plt.axes([0.4, 0.01, 0.2, 0.04]), 'Fix this temperature')
        # fixT.on_clicked(eventHandler().fixTemp)

        plt.show()

    def read_data(self):
        arr = []
        try:
            f = open(self.filename, 'r')
        except IOError:
            return [[time.time(), 0.0, 0.0]]

        for line in f.readlines():
            (x, y1, y2) = line.strip().split(',')
            xs = time.mktime(time.strptime(x))
            arr.append([float(xs), float(y1), float(y2)])
        
        return arr

    def raiseAlarm(self):
        print "ALARMA"
        music = pyglet.resource.media('01. MOSCOW CALLING.mp3')
        music.play()
        pyglet.app.run()
 
    def update_chart(self, ax):
        self.config.read('config.cfg')
        fixit1 = self.config.get('Conf1', 'FixTemp')
        delta1 = float(self.config.get('Conf1', 'Delta'))
        abstemp1 = float(self.config.get('Conf1', 'Absolute'))

        fixit2 = self.config.get('Conf2', 'FixTemp')
        delta2 = float(self.config.get('Conf2', 'Delta'))
        abstemp2 = float(self.config.get('Conf2', 'Absolute'))

        cur_temp = self.tempSource.getData()

        if cur_temp:
            self.data.append([time.time(), float(cur_temp[0]), float(cur_temp[1])])
            array = np.array(self.data)

            x = array[:,0]
            y1 = array[:,1]
            y2 = array[:,2]

            self.tempArray1.append(cur_temp[0])
            self.tempArray2.append(cur_temp[1])
            average1 = sum(self.tempArray1[0 - self.AvgSamplesNum:]) / len(self.tempArray1[0 - self.AvgSamplesNum:])
            average2 = sum(self.tempArray2[0 - self.AvgSamplesNum:]) / len(self.tempArray2[0 - self.AvgSamplesNum:])

            now = time.asctime()
            f = open(self.filename,'a')	
            f.write("%s,%s,%s\n" % (time.asctime(time.localtime(x[-1])), y1[-1], y2[-1]))
            f.close()

            msgType = "upd"

            if fixit1.lower() == "yes" and (cur_temp[0] > (average1 + delta1) or (cur_temp[0] > abstemp1)):
                now = datetime.datetime.now()
                if not self.lastAlarm1 or (now - self.lastAlarm1).total_seconds() > self.AlmSuppressInerval:
                    print "Alarma1"
                    msgType = 'alarma'
                    self.lastAlarm1 = now 
                    
            if fixit2.lower() == "yes" and (cur_temp[1] > (average2 + delta2) or (cur_temp[1] > abstemp2)):
                now = datetime.datetime.now()                    
                if  not self.lastAlarm2 or (now - self.lastAlarm2).total_seconds() > self.AlmSuppressInerval:
                    print "Alarma2"
                    msgType = 'alarma'
                    lastAlarm2 = now

            print "%s %.2f %.2f avg = %.2f %.2f  diff = %.2f %.2f " % (time.asctime(time.localtime(x[-1])).split()[3], y1[-1], y2[-1], average1, average2, cur_temp[0]-average1, cur_temp[1]-average2)

            if self.GCMSend.lower() == "alarm" and msgType == 'alarma':
                self.gcm.send(msgType, "%s,%s,%s\n" % (time.asctime(), cur_temp[0], cur_temp[1]), self.RegIDs[0])            
            if self.GCMSend.lower() == "yes":
                self.gcm.send(msgType, "%s,%s,%s\n" % (time.asctime(), cur_temp[0], cur_temp[1]), self.RegIDs[0])

        else:
            print "no data from sensors"

        # convert epoch to matplotlib float format
        dts = map(datetime.datetime.fromtimestamp, x)
        fds = dates.date2num(dts) # converted

        while len(ax.lines) > 0:
            del ax.lines[-1]

        yt = max(y1[-1], y2[-1]) + 1
        yb = min(y1[-1], y2[-1]) - 1

        #yb = yt - 4 

        ax.plot(fds, y1)
        ax.plot(fds, y2)
        ax.lines[0].set_color('b')    
        ax.lines[1].set_color('r')
        ax.set_ylim(top = yt)
        ax.set_ylim(bottom = yb)
        ax.yaxis.set_ticks(np.arange(yb, yt, 0.5))
        try:
            ax.figure.canvas.draw()
        except Exception, e:
            print e
            
    def create_chart(self):
        fig = plt.figure()
        ax = fig.add_subplot(1,1,1)

        ax.xaxis.set_major_locator(dates.HourLocator())
        # matplotlib date format object
        hfmt = dates.DateFormatter('%m/%d %H:%M')
        ax.xaxis.set_major_formatter(hfmt)

        ax.yaxis.tick_right()

        # ax.autoscale_view(True,True,True)


        plt.ylabel('Temperature')
        plt.xlabel('Time')
    
        timer = fig.canvas.new_timer(self.updInterval * 1000)
        timer.add_callback(self.update_chart, ax)
        timer.start()
