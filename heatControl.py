import sys
from PowerControl import PowerControl
import RPi.GPIO as GPIO

DIMMER_FILE = "/tmp/dimval.txt"

if __name__ == "__main__":
    pc18 = PowerControl(18, GPIO.OUT,  GPIO.PUD_OFF)
    if sys.argv[1] == 'on':
        pc18.PowerCtl(GPIO.LOW)
    if sys.argv[1] == 'off':
        pc18.PowerCtl(GPIO.HIGH)
        
    if sys.argv[2] >= 5 and sys.argv[2] <= 120:
        f = open(DIMMER_FILE, "w")
        f.write(sys.argv[2])
        f.close()


