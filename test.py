import ConfigParser
import os

CONFIG_FILE = os.getcwd() + "/config.cfg"
config = ConfigParser.ConfigParser()
config.read(CONFIG_FILE)
     
ScenarioTempConfig=[]
i = 0
while (True):
  try:
    ScenarioTempConfig.append(config.get('ScenarioDist', 'Temperature%s' % (i)).split(';'))
  except:
    break
  i = i + 1
  print i, ScenarioTempConfig
                    
print ScenarioTempConfig
