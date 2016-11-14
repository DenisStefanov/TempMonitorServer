import os
import sys, json, xmpp, random, string
import ConfigParser

SERVER = 'gcm.googleapis.com'
PORT = 5235
USERNAME = "620914624750"
PASSWORD = "AIzaSyBZB1eMgM0V1P1wWtts4O2m3Q2d81267A0"
CONFIG_FILE = os.getcwd() + '/TempMonitorServer/config.cfg'

unacked_messages_quota = 100
send_queue = []

class GCMXMPPClient(object):
  def __init__(self):
    self.client = xmpp.Client('gcm.googleapis.com', debug=[])
    self.client.connect(server=(SERVER,PORT), secure=1, use_srv=False)
    self.serverRunning = True
    auth = self.client.auth(USERNAME, PASSWORD)
    if not auth:
      print 'Authentication failed!'
      sys.exit(1)
    self.client.RegisterHandler('message', self.message_callback)

  def reconfigRegId(self, regid):
    config = ConfigParser.RawConfigParser()
    config.read(CONFIG_FILE)
    config.set("Common", "regid", regid)
    with open(CONFIG_FILE, 'wb') as configfile:
      config.write(configfile)

  def processData(self, msg):
    data = msg.get('data', None)
    if data:
      if data.get('message_type', None) == 'StoreRegid':
        regid = msg.get('from', None)
        if regid:
          print "Got new REGID " + regid
          self.reconfigRegId(regid)
      if data.get('message_type', None) == 'StopServer':
        self.serverRunning = False
        print "Stopping server"
      if data.get('message_type', None) == 'StartServer':
        self.serverRunning = True
        print "Starting server"

  def message_callback(self, session, message):
    gcm = message.getTags('gcm')
    if gcm:
      gcm_json = gcm[0].getData()
      msg = json.loads(gcm_json)
      
      self.send({'to': msg.get('from', None), 'message_type': 'ack', 'message_id': msg.get('message_id', None)})
      self.processData(msg)

  def send(self, json_dict):
    template = ("<message><gcm xmlns='google:mobile:data'>{1}</gcm></message>")
    self.client.send(xmpp.protocol.Message(
        node=template.format(self.client.Bind.bound[0], json.dumps(json_dict))))

  def flush_queued_messages(self):
    global unacked_messages_quota
    while len(send_queue) and unacked_messages_quota > 0:
      self.send(send_queue.pop(0))
      unacked_messages_quota -= 1

  def process(self):
    self.client.Process(1)
