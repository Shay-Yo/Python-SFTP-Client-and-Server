'''
    Shay Yosipov
'''
import socket
import os
import time
import threading
import random
import logging
import paramiko
from optparse import OptionParser


class FileHandlerWithHeader(logging.FileHandler):
    """
        This class handles the log file header.

    """
    # Pass the file name and header string to the constructor.

    def __init__(self, filename, header,  mode='a', encoding=None, delay=0):
        # Store the header information.
        self.header = header

        # Determine if the file pre-exists
        self.file_pre_exists = os.path.exists(filename)

        # Call the parent __init__
        logging.FileHandler.__init__(self, filename, mode, encoding, delay)

        # Write the header if delay is False and a file stream was created.
        if not delay and self.stream is not None:
            self.stream.write('%s\n' % header)

    def emit(self, record):
        # Create the file stream if not already created.
        if self.stream is None:
            self.stream = self._open()

            self.stream.write('%s\n' % self.header)

        # Call the parent class emit function.
        logging.FileHandler.emit(self, record)


class Upload_File(threading.Thread):
    """
        Handles the uploads with different threads.

    """
    connections = 0
    retryCount = 0  # error count with closes
    rejectionsWhileUploading = 0  # without closing connections
    writingRightNow = 0  # without closing connections
    maxWriting = 0  # without closing connections

    def __init__(self, host, port, user, password, localpath, remotepath, uploadDataAmount, sleepTime, isWithClose, logger, id):
        threading.Thread.__init__(self)
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._localpath = localpath
        self._remotepath = remotepath
        self._uploadDataAmount = uploadDataAmount
        self._sleepTime = sleepTime
        self._isWithClose = isWithClose
        self._logger = logger
        self._id = id
        self._errorCounter = 0
        threading.current_thread().setName(id)

    def run(self):

        if(not(self._isWithClose)):
            # Opens a connection with the SFTP server
            try:
                transport = paramiko.Transport(
                    (self._host, self._port))
                transport.connect(None, self._user, self._password)
                sftp = paramiko.SFTPClient.from_transport(
                    transport)
                fileServer = sftp.open(self._remotepath, 'ab')
                fileClient = open(self._localpath, 'rb')
                Upload_File.connections += 1
                print("Connections: "+str(Upload_File.connections))
            except Exception as e:
                print(e)
                exit()

        # file in computer to upload to server
        localSize = os.path.getsize(self._localpath)

        if(self._isWithClose):
            fileClient = open(self._localpath, 'rb')

        # opens data file and file to transfer on my computer and the server
        # it's okay to open with 'a' cause if the file does not exist it opens it
        # server path to transfer data.

        try:
            startTime = time.time()  # Start time of the upload
            uploads = 0  # check total times we uploaded packets
            TotalUploadTime = 0  # Sums up the time took for all of the uploads
            if(self._isWithClose):
                try:
                    data = fileClient.read(self._uploadDataAmount)
                finally:
                    fileClient.close()
            else:
                data = fileClient.read(self._uploadDataAmount)

            while(data != b''):
                if(self._isWithClose):
                    # Opens a connection with the SFTP server
                    while(True):
                        time.sleep(random.uniform(1, 3))
                        try:
                            transport = paramiko.Transport(
                                (self._host, self._port))
                            transport.connect(None, self._user, self._password)
                            sftp = paramiko.SFTPClient.from_transport(
                                transport)
                            fileServer = sftp.open(self._remotepath, 'ab')
                            fileClient = open(self._localpath, 'rb')
                            fileClient.seek(self._uploadDataAmount*uploads)
                            data = fileClient.read(self._uploadDataAmount)

                            Upload_File.connections += 1
                            print("Connections: "+str(Upload_File.connections))

                            # check the size of the file on the server before upload
                            lastSize = fileServer._get_size()

                            timeBeforeUpload = time.time()  # check the time before the upload
                            # sends the packet to the server
                            Upload_File.writingRightNow += 1
                            # print(str(Upload_File.writingRightNow) +
                            #       " Are writing right now")
                            if(Upload_File.writingRightNow > Upload_File.maxWriting):
                                Upload_File.maxWriting = Upload_File.writingRightNow
                            # sends the packet to the server
                            fileServer.write(data)
                            Upload_File.writingRightNow -= 1

                            # adds the time it took for the upload to the sum
                            TotalUploadTime = TotalUploadTime + \
                                (time.time()-timeBeforeUpload)

                            currentSize = fileServer._get_size()  # size of the server after upload

                            # reads the next packet to upload to the server TO CHECK if it is not empty
                            data = fileClient.read(self._uploadDataAmount)

                            fileClient.close()
                            fileServer.close()
                            sftp.close()
                            transport.close()

                            Upload_File.connections -= 1

                            # if the amount of data uploded is different than the packet size write a worning massage to the log
                            uploaded = (currentSize-lastSize)
                            if(uploaded != self._uploadDataAmount and data != b''):
                                self._logger.warning("missing "+str(uploaded) +
                                                     " bytes in current upload")

                            uploads += 1

                            time.sleep(self._sleepTime)
                            break
                        except Exception as e:
                            self._errorCounter += 1
                            Upload_File.retryCount += 1
                            print("Retry Count: "+str(Upload_File.retryCount))
                            print(e)

                else:

                    uploads += 1
                    # check the size of the file on the server before upload
                    lastSize = fileServer._get_size()
                    timeBeforeUpload = time.time()  # check the time before the upload

                    Upload_File.writingRightNow += 1
                    # print(str(Upload_File.writingRightNow) +
                    #      " Are writing right now")
                    if(Upload_File.writingRightNow > Upload_File.maxWriting):
                        Upload_File.maxWriting = Upload_File.writingRightNow
                    fileServer.write(data)  # sends the packet to the server
                    Upload_File.writingRightNow -= 1

                    # adds the time it took for the upload to the sum
                    TotalUploadTime = TotalUploadTime + \
                        (time.time()-timeBeforeUpload)

                    currentSize = fileServer._get_size()  # size of the server after upload

                    # reads the next packet to upload to the server
                    data = fileClient.read(self._uploadDataAmount)

                    # if the amount of data uploded is different than the packet size write a worning massage to the log
                    uploaded = (currentSize-lastSize)
                    if(uploaded != self._uploadDataAmount and data != b''):
                        self._logger.warning("missing "+str(uploaded) +
                                             " bytes in current upload")

                    time.sleep(self._sleepTime)
        except Exception as e:
            Upload_File.rejectionsWhileUploading += 1
            print("Error while uploading: "+str(e))
            print("errors while uploading until now: " +
                  str(Upload_File.rejectionsWhileUploading))

            print("max writing was: "+str(Upload_File.maxWriting))
        finally:
            Upload_File.connections -= 1
            print("Retryes: "+str(Upload_File.retryCount))
            print("Closing connection... Conections left: " +
                  str(Upload_File.connections))
            print("max writing was: "+str(Upload_File.maxWriting))
            print("errors while uploading: " +
                  str(Upload_File.rejectionsWhileUploading))
            endTime = time.time()
            self._logger.info(threading.current_thread(
            ).getName()+", "+str(self._id)+", "+str(startTime)+", "+str(endTime)+", "+str(endTime-startTime)+", "+str(uploads)+", "+str(TotalUploadTime)+", "+str(self._errorCounter))
            # closing the files
            if(not(self._isWithClose)):
                fileClient.close()
                fileServer.close()
                sftp.close()
                transport.close()


def start_clients(threads, filepath, packetSize, delayTime, host, port, user, password, isClosing, remotePath):
    localpath = filepath
    remotep = remotePath
    host = host
    port = port
    user = user
    password = password
    packet = packetSize
    delay = delayTime
    threads = threads
    isWithClose = isClosing
    fileSize = os.path.getsize(localpath)

    # creating the log file and his header --------------------------------------------
    # log name:
    LOG_FILE = "SFTP PERFORMANCE T " + \
        str(threads)+", FS "+str(fileSize)+", PS " + \
        str(packet/1000000)+", D "+str(delay)
    if(isWithClose):
        LOG_FILE += ", C C"
    else:
        LOG_FILE += ", C O"

    # log level
    logger = logging.getLogger("SFTP PERFORMANCE")
    logger.setLevel(logging.INFO)

    # log header
    header = "Threads, "+str(threads)+",,,\nFile, "+localpath+",,,\nFile Size (bytes), " + \
        str(fileSize)+",,,\nPacketSize (bytes), "+str(packet) + \
        ",,,\nDelay (sec), "+str(delay)+",,,\n"
    if(isWithClose):
        header += "Connection,CLOSED,,,\n"
    else:
        header += "Connection,OPENED,,,\n"

    header += "\n\nThread, Start, End, Time, Uploads, Pure upload time"

    # creating file
    LOG_FILE += ".csv"
    fh = FileHandlerWithHeader(
        LOG_FILE, header, delay=True)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    # --------------------------------------------

    fileExtension = localpath.split(".")[-1]
    # creating the clients and starting them
    threadsUpload = []
    for i in range(threads):
        serverfName = ""+str(i)+"."+fileExtension
        serverpath = remotep + serverfName
        f = Upload_File(host, port, user, password, localpath,
                        serverpath, packet, delay, isWithClose, logger, str(i))
        threadsUpload.append(f)
        f.start()
        time.sleep(0.5)


def main():
    usage = 'usage: %prog [options] arg1 arg2'
    parser = OptionParser(usage=usage)

    parser.add_option('-u', action="store", type="string", dest="user",
                      default="user", help='user name of the sftp server [default: %default]')
    parser.add_option('--password', action="store", type="string", dest="password",
                      default="pass", help='password of the user of the sftp server [default: %default]')
    parser.add_option('-t', action="store", type="int", dest="threads",
                      default=3, help='number of threads [default: %default]')
    parser.add_option('-f', action="store", type="string", dest="file_path",
                      default="Files\\text.txt", help="local file path [default: %default]")
    parser.add_option("-s", action="store", type="int", dest="packetSize",
                      default=0.1, help="packet size (MB) [default: %default]")
    parser.add_option("-d", action="store", type="int", dest="delay",
                      default=5, help="delay time (sec) between uploads [default: %default]")
    parser.add_option("--host", action="store", type="string", dest="host",
                      default="localhost", help="Server Name or IP [default: %default]")
    parser.add_option("-P", action="store", type="int", dest="port",
                      default=22, help="port number [default: %default]")
    parser.add_option("--closing", action="store", type="int", dest="isClosing",
                      default=False, help="If the uploads will be with or without closing the connection after each upload [default: %default]")
    parser.add_option("--remPath", action="store", type="string", dest="remotePath",
                      default="sftp/", help="remote path of the server to upload the file to [default: %default]")

    options, args = parser.parse_args()

    start_clients(options.threads, options.file_path,
                  int(options.packetSize*1000000), options.delay, options.host, options.port, options.user, options.password, options.isClosing, options.remotePath)


if __name__ == "__main__":
    main()
