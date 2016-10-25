import subprocess

class DGTSrc(object):
    def __init__(self):
        proc = subprocess.Popen(["digitemp_DS9097 -i -s /dev/ttyUSB0"], stdout=subprocess.PIPE, shell=True)
	(out, err) = proc.communicate()
	print "====================================="
	print out
	print "====================================="


    def getData(ax):
        try:
            proc = subprocess.Popen(["digitemp_DS9097 -s /dev/ttyUSB0 -a -q -o 2"], stdout=subprocess.PIPE, shell=True)
            (out, err) = proc.communicate()
            if out:
                print out, "-------------", out.split()[0], out.split()[1]
                cur_temp = [float(out.split()[0]), float(out.split()[1])]
                return cur_temp
        except Exception, e:
            print("Exception is caught [%s]" % (e))
            return ""







