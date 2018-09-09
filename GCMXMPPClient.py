import os
import sys, json, xmpp, random, string
import ConfigParser
import time
import urllib2
from PowerControl import PowerControl
import DropboxHandler
from WebcamHandler import WebcamHandler

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
    print "DISCONNECTED, NOT Reconnecting. In monit we trust"
    exit()
    #self.connect()

  def processData(self, msg):
    data = msg.get('data', None)
    print "received type %s data %s" % (msg.get("message_type", None), data)
    if data:
      if data.get('message_type', None) == 'GetPicture':
        wch = WebcamHandler()
        [path, picture] = wch.CaptureImage()
        dbx = DropboxHandler.TransferData(self.access_token)
        dbx.upload_file(path + picture, "/%s" % (picture))
        self.send({'to': msg.get('from', None), 'message_id': random_id(), \
                     'data' : {'type' : 'PictureURL', 'note' : picture}})

      if data.get('message_type', None) == 'StoreRegid':
        regid = msg.get('from', None)
        if regid:
          print "Got new REGID " + regid
          reconfigRegId(regid)
          self.send({'to': msg.get('from', None), 'message_id': random_id(), \
                       'data' : {'type' : 'Notify', 'note' : "Registration ID has been updated"}})

      if data.get('message_type', None) == 'PowerControl':
        pc = PowerControl(data.get("GPIO", None), "out")
        if (pc.PowerCtl("0" if data.get("State", None)=="On" else "1")):
          self.send({'to': msg.get('from', None), 'message_id':  random_id(), \
                       'data' : {'type' : 'Notify', \
                                   'GPIO' : data.get("GPIO", ""), \
                                   'State' : data.get("State", ""), \
                                   'note' : "PowerControl GPIO %s set to %s" % (data.get("GPIO", "Unknown"), data.get("State", "Unknown")) }})
        else:
          self.send({'to': msg.get('from', None), 'message_id':  random_id(), \
                       'data' : {'type' : 'Notify', 'note' : "PowerControl failure"}})

      if data.get('message_type', None) == 'ReadActuals':
        for gpio in ("17", "18", "27", "22"):
          pc = PowerControl(gpio, "out")
          state=pc.PowerRead()
          if (state):
            self.send({'to': msg.get('from', None), 'message_id':  random_id(), \
                         'data' : {'type' : 'Notify', 'GPIO' : gpio, \
                                     'State' : "On" if state.rstrip()=="0" else "Off", \
                                     'note' : "GPIO Actuals received"}})

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
        print "Server config sent to Client - "
        print {'type' : 'ServerConfig', \
                                   'stillTempThreshold'   : config.get('ServerConfig', 'absoluteStill'), \
                                   'stillToggle' : config.getboolean('ServerConfig', 'fixtempStill'), \
                                   'towerTempThreshold'   : config.get('ServerConfig', 'absoluteTower'), \
                                   'towerToggle' : config.getboolean('ServerConfig', 'fixtempTower')}


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

