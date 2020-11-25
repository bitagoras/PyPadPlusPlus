#
# PyPadPlusPlus: Module running in Python subprocess
#

import sys, os
PY3 = sys.version_info[0] >= 3
import code, time
from types import ModuleType
from codeop import compile_command
import traceback
import textwrap
import threading
from . import introspect
if PY3:
    import queue
else:
    import Queue as queue
from copy import copy
try:
   import cPickle as pickle
except:
   import pickle

class bufferOut:
    def __init__(self):
        self.buffer = []
    def clear(self):
        self.buffer = []
    def write(self, text, isErr=False):
        self.buffer.append((isErr,text))
    def read(self):
        buffer = self.buffer
        self.buffer = []
        return buffer
    def flush(self): pass
    def empty(self):
        return len(self.buffer) == 0

class PseudoFileOutBuffer:
    def __init__(self, buffer, isErr=False):
        self.buffer = buffer
        if isErr:
            self.write = self.writeStdErr
        else:
            self.write = self.writeStdOut

    def writeStdOut(self, s):
        self.buffer.write(s)

    def writeStdErr(self, s):
        self.buffer.write(s, True)

pipedFunctions = {}
def fromPipe(commandId):
    def decorator(func):
        global pipedFunctions
        pipedFunctions[commandId] = func
        return func
    return decorator

class interpreter:
    def __init__(self):
        self.buffer = bufferOut()
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        self.stdin = sys.stdin
        self.stdOutBuff = PseudoFileOutBuffer(self.buffer)
        self.stdErrBuff = PseudoFileOutBuffer(self.buffer, True)
        sys.stdout=self.stdOutBuff
        sys.stderr=self.stdErrBuff
        self.userLocals = {}
        self.interp = code.InteractiveInterpreter(self.userLocals)
        self.kernelBusy = threading.Event()
        os.chdir(os.path.expanduser("~"))

    def restartKernel(self):
        self.userLocals = {}
        self.interp = code.InteractiveInterpreter(self.userLocals)
        print("Kernel reset.")

    @fromPipe('A')
    def flush(self):
        err = False
        result = self.buffer.read()
        return err, result

    @fromPipe('B')
    def tryCode(self, iLineStart, filename, block):
        err = None
        code = None
        isValue = False
        requireMore = False
        try:
            block = block.encode('latin1').decode('utf8')
        except:
            pass
        try:
            code = compile_command('\n' * iLineStart + block, filename, 'eval')
            isValue = True
        except (OverflowError, SyntaxError, ValueError):
            try:
                code = compile_command('\n' * iLineStart + block + '\n', filename, 'exec')
                isValue = False
            except (OverflowError, SyntaxError, ValueError):
                self.interp.showsyntaxerror(filename)
                err = self.buffer.read()
                if not err: err = True
        requireMore = code is None and err is None
        if not requireMore:
            self.code = code

        return err, requireMore, isValue

    @fromPipe('C')
    def evaluate(self):
        try:
            object = eval(self.code, self.interp.locals)
            if object is not None:
                result = repr(object)
                if not self.buffer.empty():
                    result = ''.join([i for e,i in self.buffer.read() if not e]) + result
            else:
                result = None
            err = False
        except:
            err = True
            self.interp.showtraceback()
            result = self.buffer.read()
        return err, result

    @fromPipe('D')
    def execute(self, string=None, iLineStart=None, filename=None):
        try:
            if filename is not None:
                exec(compile('\n' * iLineStart + string + '\n',filename,'exec'))
            elif type(string) is str:
                # for non-user commands
                exec(string, globals())
            else:
                # for user commands
                exec(self.code, self.interp.locals)
            err = False
        except:
            err = True
            self.interp.showtraceback()
        return err, self.buffer.read()

    @fromPipe('E')
    def maxCallTip(self, value):
        '''Truncates text to fit in a call tip window.'''
        nMax = 2000  # max length
        cMax = 112  # max colums
        lMax = 14  # max lines
        lines = []
        for l in value[:nMax].split('\n'):
            lines += textwrap.wrap(l, cMax)
        value = '\n'.join(lines[:lMax]) + ('\n...' if len(lines) > lMax else '')
        return value

    @fromPipe('F')
    def getCallTip(self, line, var, truncate=True):
        if not line:
            element = var
        else:
            element = introspect.getRoot(line)
        if len(element) < len(var): return
        try:
            object = eval(element, self.interp.locals)
        except:
            return var, str(0), 'value error'
        if var in element:
            if line:
                try:
                    funcName, funcParam, funcHelp = introspect.getCallTip(element, locals=self.interp.locals)
                except:
                    funcHelp = ''
            else:
                funcHelp = ''
            typ = str(type(object))
            if typ.startswith("<type '") and typ.endswith("'>"):
                typ = typ[7:-2]
            if funcHelp:
                textFull = funcHelp
                if truncate: funcHelp = self.maxCallTip(textFull)
                calltip = 'type: ', typ, '\ndoc: ', funcHelp
            else:
                textFull = str(object)
                if isinstance(object, ModuleType):
                    try:
                        textFull = textFull + '\nhelp:\n'+object.__doc__
                    except: pass
                    value = textFull
                    if truncate: value = self.maxCallTip(textFull)
                    calltip = 'type: ', typ, '\nstr: ', ('\n' if '\n' in value else '') + value
                else:
                    value = textFull
                    if truncate: value = self.maxCallTip(textFull)
                    try:
                        l = len(object)
                        if hasattr(object, 'shape') and type(object.shape) is tuple and len(object.shape) <= 4:
                            calltip = 'type: ', typ + ', len: %i'%l, ', shape: %s'%str(tuple(int(i) for i in object.shape)), '\nstr: ', ('\n' if '\n' in value else '') + value
                        else:
                            calltip = 'type: ', typ + ', len: %i'%l, '\nstr: ', ('\n' if '\n' in value else '') + value
                    except:
                        calltip = 'type: ', typ, '\nstr: ', ('\n' if '\n' in value else '') + value
            self.fullCallTip = var, calltip[:-1] + (textFull,)
        nHighlight = 0
        for ct in calltip[:3]:
            nHighlight += len(ct)

        return element, str(nHighlight), calltip

    @fromPipe('G')
    def getFullCallTip(self):
        return self.fullCallTip

    @fromPipe('H')
    def autoCompleteObject(self, linePart):
        element = introspect.getRoot(linePart)
        try:
            autoCompleteList = dir(eval(element, self.interp.locals))
            if len(autoCompleteList) > 0:
                #autoCompleteList = '\t'.join(sorted(autoCompleteList))
                autoCompleteList = '\t'.join(sorted([i for i in autoCompleteList if not i.startswith('_')],\
                        key=lambda s: s.lower()) + sorted([i for i in autoCompleteList if i.startswith('_')]))
        except:
            autoCompleteList = None
        return autoCompleteList

    @fromPipe('I')
    def autoCompleteFunction(self, linePart):
        element = introspect.getRoot(linePart)
        funcName, funcParam, funcHelp = introspect.getCallTip(element, locals=self.interp.locals)
        self.fullCallTip = funcName, funcHelp
        callTip = self.maxCallTip(funcHelp)
        return len(funcName)-1, funcParam, callTip

    @fromPipe('J')
    def autoCompleteDict(self, linePart):
        element = introspect.getRoot(linePart)
        autoCompleteList = None
        try:
            object = eval(element, self.interp.locals)
            t = type(object)
            if t is dict or 'h5py.' in str(t):
                autoCompleteList = '\t'.join(sorted([repr(i) for i in object.keys()])) if len(object) < 1000 else None
        except:
            pass
        return autoCompleteList

    @fromPipe('K')
    def showtraceback(self):
        """Display the exception that just occurred."""
        try:
            type, value, tb = sys.exc_info()
            sys.last_type = type
            sys.last_value = value
            sys.last_traceback = tb
            tblist = traceback.extract_tb(tb)
            #del tblist[:2]
            list = traceback.format_list(tblist)
            if list:
                list.insert(0, "Traceback (most recent call last):\n")
            list[len(list):] = traceback.format_exception_only(type, value)
        finally:
            tblist = tb = None
        map(sys.stderr, list)

    @fromPipe('L')
    def showtraceback(self):
        """Stops the kernel"""
        exit()

def startLocalClient():
    clientInterp = interpreter()
    dataQueueOut = queue.Queue()
    dataQueueIn = queue.Queue()
    stdin = clientInterp.stdin.buffer if PY3 else clientInterp.stdin

    def communicationLoop():
        while True:
            # receive the id and input of the function
            data = stdin.readline()
            commandId, dataIn = eval(data)
            # to queue for execution in main thread
            if commandId in 'CD':
                dataQueueIn.put((commandId, dataIn))
            else:
                try:
                    dataToPipe = pipedFunctions[commandId](clientInterp, *dataIn)
                except:
                    dataToPipe = None
                dataQueueOut.put((commandId, dataToPipe))

            # Send back answer from output queue
            answers = []
            while not dataQueueOut.empty():
                answers.append(dataQueueOut.get())
            clientInterp.stdout.write(repr(answers)+'\n')

    thread = threading.Thread(name='communicationLoop', target=communicationLoop, args=())
    thread.start()

    def matplotlib_eventHandler(interval):
        backend = matplotlib.rcParams['backend']
        if backend in _interactive_bk:
            figManager = _pylab_helpers.Gcf.get_active()
            if figManager:
                canvas = figManager.canvas
                if canvas.figure.stale:
                    canvas.draw()
                canvas.start_event_loop(interval)
        time.sleep(interval) # In case no on-screen figure is active

    def wait():
        if active_matplotlib_eventHandler:
            matplotlib_eventHandler(0.05)
        else:
            time.sleep(0.05)

    # endless loop in the client mode
    while thread.is_alive():
        while dataQueueIn.empty():
            wait()
        commandId, dataFromPipe = dataQueueIn.get()
        dataToPipe = pipedFunctions[commandId](clientInterp, *dataFromPipe)
        dataQueueOut.put((commandId, dataToPipe))
#
# Main function for the pyPadClient to run inside the python subprocess.
#
if __name__ == '__main__':
    active_matplotlib_eventHandler = False
    startLocalClient()
    exit()
