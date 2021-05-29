import RPi.GPIO as GPIO

class PowerControl():
    def __init__(self, num, direction, pupdn):
        self.num = num
        self.direction = direction
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(num, direction, pupdn)

    def PowerCtl(self, state):
        if state == None:
            return
        GPIO.output(self.num, state)
        return "Ok"

    def PowerRead(self):
        try:
            state = GPIO.input(self.num)
        except Exception as e:
            print (e)
            return
        return state
