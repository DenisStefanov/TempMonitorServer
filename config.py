import os
import sys
import ConfigParser

CONFIG_FILE = os.getcwd() + '/TempMonitorServer/config.cfg'

if __name__ == "__main__":
	
	if len(sys.argv) <> 3:
		print "usage get sectionName,paramName;<RPT> |set sectionName,paramName,paramValue;<RPT> - no spaces"
		exit()
	command = sys.argv[1]
	configList = sys.argv[2].split(";")

	config = ConfigParser.RawConfigParser()

	config.read(CONFIG_FILE)

	if command == "set":
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
	
	if command == "get":
		reslist = ""
		for configEl in configList:
			(section, name) = configEl.split(",")
			reslist = reslist + section + "," + name + "," + config.get(section, name) + ";"
		print reslist[:-1]
