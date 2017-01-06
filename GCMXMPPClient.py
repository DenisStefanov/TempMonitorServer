import os
import sys, json, xmpp, random, string
import ConfigParser
import time
from PowerControl import PowerControl

SERVER = 'gcm-xmpp.googleapis.com'
PORT = 5235
USERNAME = "620914624750"
PASSWORD = "AIzaSyBZB1eMgM0V1P1wWtts4O2m3Q2d81267A0"
CONFIG_FILE = os.getcwd() + '/TempMonitorServer/config.cfg'

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

class GCMXMPPClient(object):
  def __init__(self):
    self.connect()
    self.client.RegisterHandler('message', self.message_callback)
    self.client.RegisterDisconnectHandler(self.disconnectHandler)

  def connect(self):
    self.serverRunning = False
    self.client = xmpp.Client('gcm.googleapis.com', debug=[])
    self.client.connect(server=(SERVER,PORT), secure=1, use_srv=False)
    auth = self.client.auth(USERNAME, PASSWORD)
    
    if not auth:
      print 'Authentication failed!'
      sys.exit(1)
    
  def disconnectHandler(self):
    print "DISCONNECTED, Reconnecting"
    self.connect()

  def processData(self, msg):
    data = msg.get('data', None)
    if data:
      if data.get('message_type', None) == 'StoreRegid':
        regid = msg.get('from', None)
        if regid:
          print "Got new REGID " + regid
          reconfigRegId(regid)
          self.send({'to': msg.get('from', None), 'message_id': random_id(), \
                       'data' : {'type' : 'Notify', 'note' : "Registration ID has been updated"}})

      if data.get('message_type', None) == 'PowerControl':
        pc = PowerControl("17", "out")
        if data.get('Power', None) == 'On':
          pc.PowerCtl("0")
        if data.get('Power', None) == 'Off':
          pc.PowerCtl("1")
        self.send({'to': msg.get('from', None), 'message_id':  random_id(), \
                                  'data' : \
                     {'type' : 'Notify', 'note' : "PowerControl set to %s" % (data.get("Power", "Unknown")) }})

      if data.get('message_type', None) == 'StopServer':
        self.serverRunning = False
        self.send({'to': msg.get('from', None), 'message_id':  random_id(), \
                                  'data' : {'type' : 'Notify', 'note' : "Server stopped"}})
        print "Stopping server"

      if data.get('message_type', None) == 'StartServer':
        self.serverRunning = True
        self.send({'to': msg.get('from', None), 'message_id':  random_id(), \
                                  'data' : {'type' : 'Notify', 'note' : "Server started"}})
        print "Starting server"

      if data.get('message_type', None) == 'ConfigServerGet':
        config = ConfigParser.RawConfigParser()
        config.read(CONFIG_FILE)
        self.send({'to': msg.get('from', None), 'message_id':  random_id(), \
                                  'data' : {'type' : 'ServerConfig', \
                                   'stillTempThreshold'   : config.get('ServerConfig', 'absoluteStill'), \
                                   'stillToggle' : config.getboolean('ServerConfig', 'fixtempStill'), \
                                   'towerTempThreshold'   : config.get('ServerConfig', 'absoluteTower'), \
                                   'towerToggle' : config.getboolean('ServerConfig', 'fixtempTower')}}) 

        self.send({'to': msg.get('from', None), 'message_id':  random_id(), \
                                  'data' : {'type' : 'Notify', 'note' : "Got Server Config"}})
        print "Server config sent to Client"

      if data.get('message_type', None) == 'ServerConfig':
        config = ConfigParser.RawConfigParser()
        config.read(CONFIG_FILE)
        for key, value in data.items():
          if (key != "message_type"):
            config.set(data.get('message_type', None), key, value)
            print "set " + data.get('message_type', None) , key, value
        with open(CONFIG_FILE, 'wb') as configfile:
          config.write(configfile)
        self.send({'to': msg.get('from', None), 'message_id':  random_id(), \
                                  'data' : {'type' : 'Notify', 'note' : "Server config has been updated"}})
        print "Server reconfigured"

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

