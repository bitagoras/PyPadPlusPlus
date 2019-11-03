#
# PyPadPlusPlus: pyPadHost, module to call Python in subprocess
#

# todo: finish

import subprocess, os, time
import socket
from Npp import console
import threading, Queue
try:
   import cPickle as pickle
except:
   import pickle

def toPipe(symbol):
    def decorator(func):
        def pipeWrapper(self, *param):
            return self.pipeQueue(symbol, param)
        return pipeWrapper
    return decorator

def pipeStream(StartCommand):
    proc = subprocess.Popen(self.StartCommand,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        universal_newlines=True)
    return proc

class socketStream:
    def __ini__(self, host="127.0.0.5", port=8888):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((host,port))
    def read(self, size=1024):
        s.recv(size).decode()
    def write(self, s):
        self.s.send(s.encode())
    def __del__(self):
        s.close()

class interpreter:
    def __init__(self, host="127.0.0.5", port=8888, outBuffer=None):
        self.outBuffer = outBuffer
        clientPath = os.path.join(os.path.dirname(__file__), 'pyPadClient.py')
        #self.StartCommand = pythonPath + ' -u ' + '"' + clientPath + '"'
        self.dataQueueOut = Queue.Queue()
        self.dataQueueIn = Queue.Queue()
        self.kernelBusy = threading.Event()
        self.kernelAlive = threading.Event()
        self.startNewKernel()
        self.thread = threading.Thread(name='communicationLoop', target=self.communicationLoop, args=())
        self.thread.start()

    def startNewKernel(self):
        #self.proc = socketStream(host="127.0.0.5", port=8888)
        self.proc = socketStream()
        # self.proc = subprocess.Popen(self.StartCommand,
                        # stdin=subprocess.PIPE,
                        # stdout=subprocess.PIPE,
                        # stderr=subprocess.STDOUT,
                        # universal_newlines=True)
        time.sleep(0.1)
        self.buffer = []
        self.kernelAlive.set()

    def restartKernel(self):
        self.kernelBusy.set()
        self.kernelAlive.clear()
        self.dataQueueOut.queue.clear()
        self.dataQueueIn.queue.clear()
        self.proc.terminate()
        time.sleep(0.1)
        self.startNewKernel()
        time.sleep(0.1)
        self.kernelAlive.set()
        self.kernelBusy.clear()
        print("Python kernel restarted.")

    def __del__(self):
        self.kernelAlive.clear()
        self.stopProcess()

    def pipeQueue(self, id, data=()):
        if self.kernelAlive.isSet():
            self.dataQueueOut.put((id, data))
            return self.dataQueueIn.get()
        else:
            return None

    def clearQueue(self):
        while not self.dataQueueOut.empty():
            self.dataQueueOut.queue.clear()
            self.dataQueueIn.put(None)

    def communicationLoop(self):
        while True:
            self.kernelAlive.wait()

            # only if the queue is empty the flush thread should request data
            if self.dataQueueOut.empty():
                if self.kernelAlive.isSet():
                    self.kernelBusy.clear()

            # from queue id and data of function
            id, dataToPipe = self.dataQueueOut.get()

            # set communication loop to busy
            self.kernelBusy.set()

            # write the id of the function
            try:
                self.proc.stdin.write(id)
            except:
                self.dataQueueIn.put(None)
                print("Python kernel not responding.")
                self.kernelAlive.clear()
                self.kernelBusy.set()
                continue

            # send data
            pickle.dump(dataToPipe, self.proc.stdin, -1)

            # flush channel for immidiate transfer
            if self.kernelAlive.isSet(): self.proc.stdin.flush()

            returnType = None
            while returnType != 'A':

                # unpickle the received data
                try:
                    assert self.kernelAlive.isSet()
                    returnType, dataFromPipe = pickle.load(self.proc.stdout)
                except:
                    dataFromPipe = None
                    break

                if returnType == 'B':
                    # unpickle the received buffer
                    self.outBuffer(dataFromPipe)

            # answer to queue
            self.dataQueueIn.put(dataFromPipe)

    @toPipe('A')
    def flush(self): pass

    @toPipe('B')
    def tryCode(self, iLineStart, filename, block): pass

    @toPipe('C')
    def evaluate(self): pass

    @toPipe('D')
    def execute(self, string=None): pass

    @toPipe('E')
    def maxCallTip(self, value): pass

    @toPipe('F')
    def getCallTip(self, line, var, truncate=True): pass

    @toPipe('G')
    def getFullCallTip(self): pass

    @toPipe('H')
    def autoCompleteObject(self, linePart): pass

    @toPipe('I')
    def autoCompleteFunction(self, linePart): pass

    @toPipe('J')
    def autoCompleteDict(self, linePart): pass

    @toPipe('K')
    def showtraceback(self): pass

    @toPipe('X')
    def stopProcess(self): pass
