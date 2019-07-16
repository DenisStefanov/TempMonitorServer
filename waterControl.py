import sys
import time
from PowerControl import PowerControl
import RPi.GPIO as GPIO

CloseGPIO = 27
OpenGPIO  = 22
cycleTimeClose = 28.5
cycleTimeOpen = 26.5


class WaterControl():
    def __init__(self):
        self.pcOpen  = PowerControl(OpenGPIO, GPIO.OUT,  GPIO.PUD_OFF)
        self.pcClose = PowerControl(CloseGPIO, GPIO.OUT,  GPIO.PUD_OFF)

    def Open(self, percent):
        if percent > 0 and percent <= 100:
            self.pcClose.PowerCtl(GPIO.HIGH)
            time.sleep(0.5)
            self.pcOpen.PowerCtl(GPIO.LOW)
            time.sleep(cycleTimeOpen / 100 * percent)
            self.pcOpen.PowerCtl(GPIO.HIGH)
        else:
            print "Open: wrong paramenter percent ", percent


    def Close(self, percent):
        if percent > 0 and percent <= 100:
            self.pcOpen.PowerCtl(GPIO.HIGH)
            time.sleep(0.5)
            self.pcClose.PowerCtl(GPIO.LOW)
            time.sleep(cycleTimeClose / 100 * percent)
            self.pcClose.PowerCtl(GPIO.HIGH)
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



