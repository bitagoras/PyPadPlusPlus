#
# PyPadPlusPlus: pyPadHost, module to call Python in subprocess
#

import subprocess, os, time
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
   
class interpreter:
    def __init__(self, pythonPath='pythonw'):
        clientPath = os.path.join(os.path.dirname(__file__), 'pyPadClient.py')
        cmd = pythonPath + ' -u ' + '"' + clientPath + '"'
        self.proc = subprocess.Popen(cmd,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        universal_newlines=True)

        self.dataQueueOut = Queue.Queue()
        self.dataQueueIn = Queue.Queue()
        
        thread = threading.Thread(name='communicationLoop', target=self.communicationLoop, args=())
        thread.start()
                
    def pipeQueue(self, id, data=()):
        self.dataQueueOut.put((id, data))
        return self.dataQueueIn.get()

    def communicationLoop(self):
        while True:
            # from queue id and data of function
            id, dataToPipe = self.dataQueueOut.get()
            
            # write the id of the function
            self.proc.stdin.write(id)
            
            # pickle the data for transmitting
            toPipe = pickle.dumps(dataToPipe,-1)
            
            # send data
            self.proc.stdin.write(toPipe)
            
            # flush channel for immidiate transfer
            self.proc.stdin.flush()

            if id == 'X': return

            # unpickle the received data
            dataFromPipe = pickle.load(self.proc.stdout)

            # answer to queue
            self.dataQueueIn.put(dataFromPipe)

    @toPipe('A')
    def flush(self): pass
    
    @toPipe('B')
    def tryCode(self, iLineStart, filename, block): pass
    
    @toPipe('C')
    def evaluate(self): pass
    
    @toPipe('D')
    def execute(self): pass
    
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
    