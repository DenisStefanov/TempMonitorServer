import os
import glob
import time

class GPIOSrc(object):
    def __init__(self):
#        os.system('modprobe w1-gpio')
#        os.system('modprobe w1-therm')

        self.device_file = []
        base_dir = '/sys/bus/w1/devices/'
        device_folders = glob.glob(base_dir + '28*')
    
        for i, folder in enumerate(device_folders):
	    self.device_file.append(folder + '/w1_slave')
        print self.device_file

    
    def read_temp_raw(self, device_f):
        f = open(device_f, 'r')
        lines = f.readlines()
        f.close()
        return lines
     
    def getData(self):
        cur_temp = []
        try:
            for i, f in enumerate(self.device_file):
                lines = self.read_temp_raw(f)
                while lines[0].strip()[-3:] != 'YES':
                    time.sleep(0.2)
                    lines = self.read_temp_raw(f)
                equals_pos = lines[1].find('t=')
                if equals_pos != -1:
                    temp_string = lines[1][equals_pos+2:]
                    temp_c = float(temp_string) / 1000.0
                    temp_f = temp_c * 9.0 / 5.0 + 32.0
                    cur_temp.append(temp_c)
            return cur_temp
        except Exception, e:
            print("Exception is caught [%s]" % (e))
            return ""


