import socket
import ConfigParser
from GPIOSrc import GPIOSrc
from ADC import adc

tempSource = GPIOSrc()
DEVICE_MAC = 'b8:27:eb:26:6f:8b'

SENSOR_ID_TEMP = DEVICE_MAC + '01'
SENSOR_ID_PRESS = DEVICE_MAC + '02'

CONFIG_FILE = "/home/pi/TempMonitorServer/config.cfg"

config = ConfigParser.ConfigParser()
config.read(CONFIG_FILE)
pressureSensorIDX = int( config.get('ServerConfig', 'pressuresensoridx'))

res = tempSource.getData()
if res:
    cur_temp = [res[0] if len(res) > 0 else -1, res[1] if len(res) > 1 else -1, res[2] if len(res) > 2 else -1]

hadc = adc()
pressureVal = hadc.read(pressureSensorIDX)

print cur_temp, pressureVal

sock = socket.socket()
pressureVal = pressureVal * .736
try:
    sock.connect(('narodmon.ru', 8283))
    #sock.send("#{}\n#{}#{}\n##".format(DEVICE_MAC, SENSOR_ID_1, cur_temp[0]))
    sock.send("#{}\n#{}#{}\n#{}#{}\n##".format(DEVICE_MAC, SENSOR_ID_TEMP, cur_temp[0], SENSOR_ID_PRESS, pressureVal))
    data = sock.recv(1024)
    sock.close()
    print "Resp = ", data
except socket.error, e:
    print('ERROR! Exception {}'.format(e))
