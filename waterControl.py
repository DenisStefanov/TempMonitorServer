import os
import sys
import time, random, string
from PowerControl import PowerControl
import RPi.GPIO as GPIO

CloseGPIO = 27
OpenGPIO  = 22
cycleTimeClose = 28.5
cycleTimeOpen = 26.5
WATER_FILE = os.getcwd() + "/TempMonitorServer/waterval.txt"

def random_id():
    rid = ''
    for x in range(8): rid += random.choice(string.ascii_letters + string.digits)
    return rid

def waterOpen(gcm, to, percent):
  wc = WaterControl()
  if wc.pcOpen.PowerRead() == GPIO.HIGH: #not currently running
    wc.Open(percent)
  gcm.send({'to': to, 'message_id':  random_id(), "time_to_live" : 60,\
            'data' : {'type' : 'NotifyWater', 'note' : str(wc.angle)}})

def waterClose(gcm, to, percent):
  wc = WaterControl()
  if wc.pcClose.PowerRead() == GPIO.HIGH: #not currently running
    wc.Close(percent)
  gcm.send({'to': to, 'message_id':  random_id(), "time_to_live" : 60,\
            'data' : {'type' : 'NotifyWater', 'note' : str(wc.angle)}})

class WaterControl():
    def __init__(self):
        self.pcOpen  = PowerControl(OpenGPIO, GPIO.OUT,  GPIO.PUD_OFF)
        self.pcClose = PowerControl(CloseGPIO, GPIO.OUT,  GPIO.PUD_OFF)
	self.angle = self.readWaterPosition()

    def writeWaterPosition(self):
        try:
            f = open(WATER_FILE, 'w')
            f.write(str(self.angle))
            f.close()
            print "Write water ", str(self.angle)
        except:
            raise

    def readWaterPosition(self):
        waterVal = 0
        try:
            f = open(WATER_FILE, 'r')
            waterVal = int(f.read())
            f.close()
        except:
            print "water control file empty. ignoring"
        print "readWaterPosition ", waterVal
	return waterVal

    def Open(self, percent):
        if percent > 0 and percent <= 100:
            self.pcClose.PowerCtl(GPIO.HIGH)
            time.sleep(0.5)
            self.pcOpen.PowerCtl(GPIO.LOW)
            time.sleep(cycleTimeOpen / 100 * percent)
            self.pcOpen.PowerCtl(GPIO.HIGH)
	    self.angle  += int(1.80 * percent)
            print "percent = ", percent
            print "Open angle = ", self.angle
            if self.angle > 180:
                self.angle = 180
            
            self.writeWaterPosition()
        else:
            print "Open: wrong paramenter percent ", percent


    def Close(self, percent):
        if percent > 0 and percent <= 100:
            self.pcOpen.PowerCtl(GPIO.HIGH)
            time.sleep(0.5)
            self.pcClose.PowerCtl(GPIO.LOW)
            time.sleep(cycleTimeClose / 100 * percent)
            self.pcClose.PowerCtl(GPIO.HIGH)
            
            self.angle  += int(1.80 * percent)

            print "percent = ", percent
            print "Close angle = ", self.angle

            if self.angle >= 360:
                self.angle = 0

            self.writeWaterPosition()
	else:
            print "Close: wrong paramenter percent ", percent

if __name__ == "__main__":
    op = sys.argv[1].lower() if len(sys.argv) > 1 else None
    partMove = int(sys.argv[2]) if len(sys.argv) > 2 else 100

    if op == 'open':
        wc = WaterControl()
        wc.Open(partMove)
  
    if op == 'close':
        wc = WaterControl()
        wc.Close(partMove)
