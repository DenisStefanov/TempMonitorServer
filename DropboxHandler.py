import dropbox
import ConfigParser

CONFIG_FILE = os.getcwd() + '/TempMonitorServer/config.cfg'

class TransferData:
    def __init__(self, access_token):
        self.access_token = access_token

    def upload_file(self, file_from, file_to):
        """upload a file to Dropbox using API v2
        """
        dbx = dropbox.Dropbox(self.access_token)

        with open(file_from, 'rb') as f:
            dbx.files_upload(f.read(), file_to)

def main():
    config = ConfigParser.RawConfigParser()
    config.read(CONFIG_FILE)
    self.access_token = config.get('DropboxClient', 'DBXAccessToken')

    transferData = TransferData(self.access_token)

    file_from = 'test.txt'
    file_to = '/test.txt'  # The full path to upload the file to, including the file name

    # API v2
    transferData.upload_file(file_from, file_to)

if __name__ == '__main__':
    main()

