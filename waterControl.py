import sys
import time
from PowerControl import PowerControl
import RPi.GPIO as GPIO

CloseGPIO = 27
OpenGPIO  = 22
cycleTimeClose = 28.5
cycleTimeOpen = 26.5
WATER_FILE = "/tmp/waterval.txt"


class WaterControl():
    def __init__(self):
        self.pcOpen  = PowerControl(OpenGPIO, GPIO.OUT,  GPIO.PUD_OFF)
        self.pcClose = PowerControl(CloseGPIO, GPIO.OUT,  GPIO.PUD_OFF)
	[self.openPercent, self.closePercent] = self.readWaterPosition()

    def writeWaterPosition(self, openPercent, closePercent):
        try:
            f = open(WATER_FILE, 'w')
            f.write(str(openPercent) + "," + str(closePercent))
            f.close()
        except:
            raise

    def readWaterPosition(self):
        try:
            f = open(WATER_FILE, 'r')
            waterVal = f.read().split(',')
            if len(waterVal) < 2:
                waterVal = [0,0]
            f.close()
        except:
            print "water control file empty. ignoring"
	return waterVal

    def Open(self, percent):
        if percent > 0 and percent <= 100:
            self.pcClose.PowerCtl(GPIO.HIGH)
            time.sleep(0.5)
            self.pcOpen.PowerCtl(GPIO.LOW)
            time.sleep(cycleTimeOpen / 100 * percent)
            self.pcOpen.PowerCtl(GPIO.HIGH)

	    self.openPercent += percent
	    if self.openPercent > 100:
		self.openPercent = 100
	    self.writeWaterPosition(self.openPercent, self.closePercent)
        else:
            print "Open: wrong paramenter percent ", percent


    def Close(self, percent):
        if percent > 0 and percent <= 100:
            self.pcOpen.PowerCtl(GPIO.HIGH)
            time.sleep(0.5)
            self.pcClose.PowerCtl(GPIO.LOW)
            time.sleep(cycleTimeClose / 100 * percent)
            self.pcClose.PowerCtl(GPIO.HIGH)

	    self.closePercent += percent
	    if self.closePercent > 100:
		self.closePercent = 100
            self.writeWaterPosition(self.openPercent, self.closePercent)
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



