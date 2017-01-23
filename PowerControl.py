class PowerControl():
    def __init__(self, num, direction):        
        self.cfg = {"num" : num, "direction" : direction}
        self.export_file = "/sys/class/gpio/export"
        self.dir_file = "/sys/class/gpio/gpio%s/direction" % (self.cfg.get("num"))
        self.value_file = "/sys/class/gpio/gpio%s/value" % (self.cfg.get("num"))

        try:
            fd = open(self.export_file,'w')
            fd.write(self.cfg.get("num"))
            fd.close()
        except IOError, e:
            pass

    def PowerCtl(self, state):

        if state == None:
            return

        try:
            fd = open(self.dir_file,'w')
            fd.write(self.cfg.get("direction"))
            fd.close()
        except Exception, e:
            print e

        try:
            fd = open(self.value_file,'w')
            fd.write(state)
            fd.close()
        except Exception, e:
            print e

        return "Ok"

    def PowerRead(self):
        try:
            fd = open(self.value_file,'r')
            state = fd.read()
            fd.close()
        except Exception, e:
            print e
            return

        return state
