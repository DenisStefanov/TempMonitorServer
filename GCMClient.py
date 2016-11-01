import urllib2
import json

url = 'https://android.googleapis.com/gcm/send'
PjNum = '620914624750'
APIKey = 'AIzaSyBZB1eMgM0V1P1wWtts4O2m3Q2d81267A0'

class GCMClient():
    def __init__(self):
        pass

    def send(self, datatype, rawdata, regids):
        json_data = {"data" : {
                              "data": rawdata,
                              "type": datatype
                              }, 
                     "registration_ids": regids,
                     }
        data = json.dumps(json_data)

        headers = {'Content-Type': 'application/json', 'Authorization': 'key=%s' % APIKey}
        req = urllib2.Request(url, data, headers)

        print url, data, headers

        try:
            f = urllib2.urlopen(req)
            response = json.loads(f.read())
            print
            print response
        except Exception, e:
            print e
