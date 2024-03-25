import glob
import time

class GPIOSrc(object):
    def __init__(self):

        self.device_file = []
        base_dir = '/sys/bus/w1/devices/'
        device_folders = glob.glob(base_dir + '28*')
    
        for i, folder in reversed(list(enumerate(device_folders))): 
            self.device_file.append(folder + '/w1_slave')
        #print ("Found temperature sensors %s" % self.device_file)
    
    def read_temp_raw(self, device_f):
        f = open(device_f, 'r')
        lines = f.readlines()
        f.close()
        return lines
     
    def getData(self):
        cur_temp = dict()
        try:
            for i, f in enumerate(self.device_file):
                lines = self.read_temp_raw(f)
                count  = 0
                while lines[0].strip()[-3:] != 'YES' and count < 5:
                    time.sleep(0.2)
                    lines = self.read_temp_raw(f)
                    count += 1
                    print ('Retry %s for %s' % (count, f))
                if count >= 5:
                    print('Failed to read data for sensor %s' % (f))
                equals_pos = lines[1].find('t=')
                if equals_pos != -1:
                    temp_string = lines[1][equals_pos+2:]
                    temp_c = float(temp_string) / 1000.0
                    temp_f = temp_c * 9.0 / 5.0 + 32.0
                    cur_temp[f[f.find('/28')+4:f.find('/w1_slave')]] = temp_c
            return cur_temp
        except Exception as e:
            print("Exception is caught [%s]" % (e))
            return ""

