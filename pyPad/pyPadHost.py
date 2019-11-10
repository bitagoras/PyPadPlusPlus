#
# PyPadPlusPlus: pyPadHost, module to call Python in subprocess
#
import os, time
from Npp import console
import subprocess, threading, Queue
import multiprocessing.queues
try:
   import cPickle as pickle
except:
   import pickle

queueOut = multiprocessing.queues.Queue(maxsize=5)

class quantizedChannel:
    def __init__(self, commandId, timeout=1):
        self.receiveQueue = multiprocessing.queues.Queue(maxsize=1)
        self.timeout = timeout
        self.sendLock = threading.Lock()
        self.commandId = commandId

    def __call__(self, arg=None):
        if kernelAlive.isSet():
            with self.sendLock:
                if self.receiveQueue.empty():
                    try:
                        queueOut.put_nowait((self.commandId, arg))
                    except:
                        print "Python kernel not responding."
                        kernelAlive.clear()
                        return None
                try:
                    ret = self.receiveQueue.get(block=True, timeout=self.timeout)
                except:
                    return None
            return ret
        else:
            return None

    def clear(self):
        while not queueOut.empty():
            queueOut.get_nowait()

receiveChannels = {}
receiveQueues = {}
def toPipe(symbol, timeout=1):
    channel = quantizedChannel(symbol, timeout=timeout)
    receiveChannels[symbol] = channel
    receiveQueues[symbol] = channel.receiveQueue
    def decorator(func):
        def pipeWrapper(self, *param):
            return channel(param)
        return pipeWrapper
    return decorator

class interpreter:
    def __init__(self, pythonPath='pythonw', outBuffer=None):
        global kernelAlive
        self.queueIn = Queue.Queue()
        if not pythonPath.endswith('.exe'):
            if pythonPath.strip().endswith('pythonw'):
                pythonPath = pythonPath.strip() + '.exe'
            else:
                pythonPath = os.path.join(pythonPath.strip(),'pythonw.exe')
        assert os.path.exists(pythonPath), 'file pythonw.exe not found.'
        self.outBuffer = outBuffer
        clientPath = os.path.join(os.path.dirname(__file__), 'pyPadClient.py')
        self.StartCommand = pythonPath + ' -u ' + '"' + clientPath + '"'
        print "start kernel:", self.StartCommand
        self.kernelActive = threading.Event()
        self.kernelAlive = kernelAlive = threading.Event()
        self.startNewKernel()
        self.thread = threading.Thread(name='communicationLoop', target=self.communicationLoop, args=())
        self.thread.start()

    def active(self):
        return self.kernelActive.isSet()

    def startNewKernel(self):
        self.proc = subprocess.Popen(self.StartCommand,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        universal_newlines=True)
        time.sleep(0.1)
        self.buffer = []
        self.kernelAlive.set()

    def restartKernel(self):
        self.kernelAlive.clear()
        self.kernelActive.set()
        #self.clearQueue()
        self.proc.terminate()
        time.sleep(0.1)
        self.startNewKernel()
        self.kernelActive.clear()
        print "Python kernel restarted."

    def __del__(self):
        self.kernelAlive.clear()
        self.stopProcess()

    def pipeQueue(self, commandId, data=()):
        if self.kernelAlive.isSet():
            queueOut.put((commandId, data))
            return self.queueIn.get()
        else:
            return None

    def clearQueue(self):
        global queueOut
        queueOut.close()
        queueOut = multiprocessing.queues.Queue(maxsize=5)
        self.queueIn.queue.clear()
        for k,i in receiveChannels.items():
            i.clear()

    def communicationLoop(self):
        while True:
            self.kernelAlive.wait()

            # # only if the output queue is empty the flush thread should request data
            if queueOut.empty():
                if self.kernelAlive.isSet():
                    self.kernelActive.clear()

            # from queue commandId and data of function
            commandId, dataToPipe = queueOut.get()

            if not self.kernelAlive.isSet(): continue

            # set communication loop to busy
            if commandId in "BCD":
                self.kernelActive.set()

            # write the commandId of the function
            try:
                # send data
                self.proc.stdin.write(repr((commandId, dataToPipe))+'\n')
            except:
                if self.kernelAlive:
                    print "Python kernel not responding."
                    self.kernelAlive.clear()
                continue

            # flush channel for immidiate transfer
            if self.kernelAlive.isSet(): self.proc.stdin.flush()

            try:
                answers = eval(unicode(self.proc.stdout.readline(),'latin1').encode('utf-8'))
            except:
                continue

            # answer to queue
            for commandId, dataFromPipe in answers:
                receiveQueues[commandId].put(dataFromPipe)
                if commandId in 'BCD':
                    self.kernelActive.clear()

    @toPipe('A')
    def flush(self): pass

    @toPipe('B', timeout=None)
    def tryCode(self, iLineStart, filename, block): pass

    @toPipe('C', timeout=None)
    def evaluate(self): pass

    @toPipe('D', timeout=None)
    def execute(self, string=None, iLineStart=None, filename=None): pass

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

    @toPipe('L')
    def stopProcess(self): pass
