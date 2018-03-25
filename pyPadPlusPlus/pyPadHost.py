#
# PyPadPlusPlus: pyPadHost, module to call Python in subprocess
#

import subprocess, os, time
from Npp import console

try:
   import cPickle as pickle
except:
   import pickle

class interpreter:
    def __init__(self, pythonPath='pythonw'):
        clientPath = os.path.join(os.path.dirname(__file__), 'pyPadClient.py')
        cmd = pythonPath + ' -u ' + '"' + clientPath + '"'
        self.proc = subprocess.Popen(cmd,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        universal_newlines=True)
        time.sleep(1)
        self.proc.stdin.flush()
        # self.out(self.proc.stderr.readline())

    def callPipe(self, command, args=()):
        self.proc.stdin.write(command)
        toPipe = pickle.dumps(args,-1)
        self.proc.stdin.write(hex(len(toPipe))+'\n')
        self.proc.stdin.write(toPipe)
        self.proc.stdin.flush()
        fromPipe = self.proc.stdout.readline()
        assert len(fromPipe) > 1
        nBytes = int(fromPipe, 16)
        fromPipe = self.proc.stdout.read(nBytes)
        ret = pickle.loads(fromPipe)
        return ret

    # func:
        # A: interp.tryCode,
        # B: interp.evaluate,
        # C: interp.execute
        # D: interp.getCallTip,
        # E: interp.autoCompleteObject,
        # F: interp.autoCompleteFunction,
        # G: interp.autoCompleteDict,

    def tryCode(self, iLineStart, filename, block):
        return self.callPipe('A', (iLineStart, filename, block))

    def evaluate(self):
        return self.callPipe('B')

    def execute(self):
        return self.callPipe('C')

    def getCallTip(self, line, var, truncate=True):
        return self.callPipe('D', (line, var, truncate))

    def autoCompleteObject(self, linePart):
        return self.callPipe('E', (linePart,))

    def autoCompleteFunction(self, linePart):
        return self.callPipe('F', (linePart,))

    def autoCompleteDict(self, linePart):
        return self.callPipe('G', (linePart,))

    def out(self, text):
        if type(text) is not str: text = repr(text)
        console.write('\n'+text+'\n')
        console.editor.setReadOnly(0)
