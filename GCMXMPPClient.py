import os
import sys, json, xmpp, random, string
import ConfigParser
import time
import urllib2
import threading
import RPi.GPIO as GPIO
from PowerControl import PowerControl
import DropboxHandler
from WebcamHandler import WebcamHandler
from waterControl import waterOpen, waterClose

CONFIG_FILE = os.getcwd() + '/TempMonitorServer/config.cfg'
DIMMER_FILE = os.getcwd() + "/TempMonitorServer/dimval.txt"

def random_id():
  rid = ''
  for x in range(8): rid += random.choice(string.ascii_letters + string.digits)
  return rid

def reconfigRegId(regid):
  config = ConfigParser.RawConfigParser()
  config.read(CONFIG_FILE)
  config.set("Common", "regid", regid)
  with open(CONFIG_FILE, 'wb') as configfile:
    config.write(configfile)

def sendServerConfig(gcm, msg):
  config = ConfigParser.RawConfigParser()
  config.read(CONFIG_FILE)
  gcm.send({'to': msg.get('from', None), 'message_id':  random_id(), "time_to_live" : 60,\
             'data' : {'type' : 'ServerConfig', \
                       'stillTempThreshold'   : config.get('ServerConfig', 'absolutestill'), \
                       'stillToggle' : config.getboolean('ServerConfig', 'fixtempstill'), \
                       'towerTempThreshold'   : config.get('ServerConfig', 'absolutetower'), \
                       'stillAutoToggle' : config.getboolean('ServerConfig', 'fixtempstillbypower'), \
                       'towerAutoToggle' : config.getboolean('ServerConfig', 'fixtemptowerbypower'), \
                       'towerToggle' : config.getboolean('ServerConfig', 'fixtemptower')}}) 

#        self.send({'to': msg.get('from', None), 'message_id':  random_id(), "time_to_live" : 60, \
#                                  'data' : {'type' : 'Notify', 'note' : "Got Server Config"}})
  print "Server config sent to Client - "
  print {'type' : 'ServerConfig', \
         'stillTempThreshold'   : config.get('ServerConfig', 'absolutestill'), \
         'stillToggle' : config.getboolean('ServerConfig', 'fixtempstill'), \
         'towerTempThreshold'   : config.get('ServerConfig', 'absolutetower'), \
         'towerToggle' : config.getboolean('ServerConfig', 'fixtemptower'), \
         'stillAutoToggle' : config.getboolean('ServerConfig', 'fixtempstillbypower'), \
         'towerAutoToggle' : config.getboolean('ServerConfig', 'fixtemptowerbypower')}    

class GCMXMPPClient(object):
  def __init__(self):
    config = ConfigParser.RawConfigParser()
    config.read(CONFIG_FILE)
    self.access_token = config.get('DropboxClient', 'DBXAccessToken')
    self.server = config.get('GCMXMPPServer', 'server')
    self.port = config.get('GCMXMPPServer', 'port')
    self.username = config.get('GCMXMPPServer', 'username')
    self.password = config.get('GCMXMPPServer', 'password')
    self.client_url = config.get('GCMXMPPClient', 'client')
    self.serverRunning = True

    self.connect()
    self.client.RegisterHandler('message', self.message_callback)
    self.client.RegisterDisconnectHandler(self.disconnectHandler)

  def connect(self):
    url = 'http://ya.ru'
    connected = False
    while (not connected):
      try:
        print "trying %s" % (url)
        urllib2.urlopen(url, timeout=5)
        connected = True
        print "Connected."
      except Exception, e:
        print e
        time.sleep(1)
      finally:
        sys.stdout.flush()
        
    self.client = xmpp.Client(self.client_url, debug=[])
    #self.client = xmpp.Client(self.client_url)
    self.client.connect(server=(self.server,self.port), secure=1, use_srv=False)
    auth = self.client.auth(self.username, self.password)
        
    if not auth:
      print 'Authentication failed!'
      sys.exit(1)
    
  def disconnectHandler(self):
    os.environ["GCMDisconnected"] = "True"
    print "Disconnect handler. Set GCMDisconnected to True"
    sys.exit(1)

  def processData(self, msg):
    data = msg.get('data', None)
    if data:
      print "Received data %s" % (data)
#      if data.get('message_type', None) == 'GetPicture':
#        wch = WebcamHandler()
#        [path, picture] = wch.CaptureImage()
#        dbx = DropboxHandler.TransferData(self.access_token)
#        dbx.upload_file(path + picture, "/%s" % (picture))
#        self.send({'to': msg.get('from', None), 'message_id': random_id(), "time_to_live" : 60,\
#                     'data' : {'type' : 'PictureURL', 'note' : picture}})

      if data.get('message_type', None) == 'StoreRegid':
        regid = msg.get('from', None)
        if regid:
          print "Got new REGID " + regid
          reconfigRegId(regid)
          self.send({'to': msg.get('from', None), 'message_id': random_id(), "time_to_live" : 60,\
                       'data' : {'type' : 'Notify', 'note' : "Registration ID has been updated"}})

#      if data.get('message_type', None) == 'PowerControl':
#        pc = PowerControl(int(data.get("GPIO", None)), GPIO.OUT,  GPIO.PUD_OFF)
#        if (pc.PowerCtl(GPIO.LOW if data.get("State", None)=="On" else GPIO.HIGH)):
#          self.send({'to': msg.get('from', None), 'message_id':  random_id(), "time_to_live" : 60,\
#                       'data' : {'type' : 'NotifyGPIO', \
#                                   'GPIO' : data.get("GPIO", ""), \
#                                   'State' : data.get("State", ""), \
#                                   'note' : "PowerControl GPIO %s set to %s" % (data.get("GPIO", "Unknown"), data.get("State", "Unknown")) }})
#        else:
#          self.send({'to': msg.get('from', None), 'message_id':  random_id(), "time_to_live" : 60,\
#                       'data' : {'type' : 'Notify', 'note' : "PowerControl failure"}})

      if data.get('message_type', None) == 'DimmerControl':
        try:
          f = open(DIMMER_FILE, "r")
          dimval = f.read()
          f.close()
        except:
          dimval = None
          
        if dimval == "" or dimval == None:
          dimval = 0;
        if data.get("DIMMER", None) == "UP":
          dimval = int(dimval) + 1 if int(dimval) < 120 else dimval
        elif data.get("DIMMER", None) == "DN":
          dimval = int(dimval) - 1 if int(dimval) > 5 else dimval
        else:
          dimval = int(data.get("DIMMER", 0))
          
        self.send({'to': msg.get('from', None), 'message_id':  random_id(), "time_to_live" : 60,\
                   'data' : {'type' : 'NotifyDIMMER', 'DIMMER' : dimval, \
                             'note' : "DIMMER Actuals received"}})	

        pc = PowerControl(18, GPIO.OUT,  GPIO.PUD_OFF)
        pc.PowerCtl(GPIO.LOW if dimval > 5 else GPIO.HIGH)

        f = open(DIMMER_FILE, "w")
        f.write(str(dimval))
        f.close()

      if data.get('message_type', None) == 'WaterControl':
        try:
          valOpen  = int(data.get("OPEN", 0))
          valClose = int(data.get("CLOSE", 0))
          if valOpen > 0:
            threading.Thread(target=waterOpen, args=(self, msg.get('from', None), valOpen,)).start()
          elif valClose > 0:
            threading.Thread(target=waterClose, args=(self, msg.get('from', None), valClose,)).start()
        except Exception, e:
          print e

      if data.get('message_type', None) == 'ReadDimmer':
        try:
          f= open(DIMMER_FILE, "r")
          dimval = f.read()
          f.close()
        except:
          dimval = 0
        
        self.send({'to': msg.get('from', None), 'message_id':  random_id(), "time_to_live" : 60,\
                     'data' : {'type' : 'NotifyDIMMER', 'DIMMER' : dimval, \
                               'note' : "DIMMER Actuals received"}})	

#      if data.get('message_type', None) == 'ReadActuals':
#        for gpio in (17, 18, 27, 22):
#          pc = PowerControl(gpio, GPIO.OUT, GPIO.PUD_OFF)
#          state=pc.PowerRead()
#          self.send({'to': msg.get('from', None), 'message_id':  random_id(), "time_to_live" : 60,\
#                     'data' : {'type' : 'NotifyGPIO', 'GPIO' : gpio, \
#                               'State' : "Off" if state == GPIO.HIGH else "On", \
#                               'note' : "GPIO Actuals received"}})

      if data.get('message_type', None) == 'StopServer':
        self.serverRunning = False
        self.send({'to': msg.get('from', None), 'message_id':  random_id(), "time_to_live" : 60,\
                                  'data' : {'type' : 'Notify', 'note' : "Server stopped"}})
        print "Stopping server"

      if data.get('message_type', None) == 'StartServer':
        self.serverRunning = True
        self.send({'to': msg.get('from', None), 'message_id':  random_id(), "time_to_live" : 60,\
                                  'data' : {'type' : 'Notify', 'note' : "Server started"}})
        print "Starting server"

      if data.get('message_type', None) == 'ConfigServerGet':
        sendServerConfig(self, msg)

      if data.get('message_type', None) == 'ServerConfig':
        config = ConfigParser.RawConfigParser()
        config.read(CONFIG_FILE)
        for key, value in data.items():
          if (key != "message_type"):
            config.set(data.get('message_type', None), key, value)
            print "set " + data.get('message_type', None) , key, value
        with open(CONFIG_FILE, 'wb') as configfile:
          config.write(configfile)
        self.send({'to': msg.get('from', None), 'message_id':  random_id(), "time_to_live" : 60, \
                                  'data' : {'type' : 'Notify', 'note' : "Server config has been updated"}})
        print "Server reconfigured"
        sendServerConfig(self, msg)

  def message_callback(self, session, message):
    gcm = message.getTags('gcm')
    if gcm:
      gcm_json = gcm[0].getData()
      msg = json.loads(gcm_json)
      if (msg.get("message_type", None) != 'ack'): #no ack for ack
        self.send({'to': msg.get('from', None), 'message_type':'ack','message_id': msg.get('message_id', None)})
      self.processData(msg)

  def send(self, json_dict):
    template = ("<message><gcm xmlns='google:mobile:data'>{1}</gcm></message>")
    self.client.send(xmpp.protocol.Message(
        node=template.format(self.client.Bind.bound[0], json.dumps(json_dict))))

