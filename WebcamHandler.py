import os
import time

class WebcamHandler():
      def __init__(self):
            pass
      
      def CaptureImage(self):
            filepath = '/tmp/'
            filename = 'image' + time.strftime("%Y%m%d-%H%M%S")+ '.jpg'
            os.system('fswebcam -r 640x480 %s%s' % (filepath, filename))
      
            return [filepath, filename]
