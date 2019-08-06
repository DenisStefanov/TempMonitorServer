import Adafruit_ADS1x15

class adc():
    def __init__(self):
	self.adcVal = [0]*4
    	for i in range(len(self.adcVal)):
            self.adcVal[i] = Adafruit_ADS1x15.ADS1115().read_adc(i, gain=1)

    def read(self, sensor):
	return self.adcVal[sensor]
