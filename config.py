import sys
import ConfigParser

CONFIG_FILE = 'config.cfg'

if __name__ == "__main__":
	
	if len(sys.argv) <> 2:
		print "usage sectionName,paramName,paramValue;<RPT> - no spaces"
		exit()
	configList = sys.argv[1].split(";")
	print configList

	config = ConfigParser.RawConfigParser()
	config.read(CONFIG_FILE)
	try:
		config.add_section('Common')
		config.add_section('Conf1')
		config.add_section('Conf2')
	except:
		pass

	for configEl in configList:
		(section, name, val) = configEl.split(",")
		config.set(section, name, val)

	with open(CONFIG_FILE, 'wb') as configfile:
    		config.write(configfile)