import sys
import time
from PowerControl import PowerControl
import RPi.GPIO as GPIO

CloseGPIO = 22
OpenGPIO  = 27
cycleTime = 15

if __name__ == "__main__":
    pcOpen  = PowerControl(27, GPIO.OUT,  GPIO.PUD_OFF)
    pcClose = PowerControl(22, GPIO.OUT,  GPIO.PUD_OFF)

    op = sys.argv[1].lower() if len(sys.argv) > 1 else None
    partMove = sys.argv[2] if len(sys.argv) > 2 else 100

    if op == 'open':
    	if partMove > 0 and partMove <= 100:
	    pcClose.PowerCtl(GPIO.HIGH)
	    time.sleep(0.5)
            pcOpen.PowerCtl(GPIO.LOW)
	    partMove = cycleTime / 100 * partMove
	    time.sleep(partMove)
	    pcOpen.PowerCtl(GPIO.HIGH)

    if op == 'close':
    	if partMove > 0 and partMove <= 100:
	    pcOpen.PowerCtl(GPIO.HIGH)
	    time.sleep(0.5)
            pcClose.PowerCtl(GPIO.LOW)
	    partMove = cycleTime / 100 * partMove
	    time.sleep(partMove)
	    pcClose.PowerCtl(GPIO.HIGH)



