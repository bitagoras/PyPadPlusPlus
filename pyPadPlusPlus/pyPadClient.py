#
# PyPadPlusPlus: Module running in Python subprocess
#

activateMatplotlibEventHandler = True

import sys, code, time
from types import ModuleType
import introspect  # Module for code introspection from the wxPython project
from codeop import compile_command
import traceback
import textwrap
import threading, Queue
from copy import copy
try:
   import cPickle as pickle
except:
   import pickle
if activateMatplotlibEventHandler:
    import matplotlib
    from matplotlib import _pylab_helpers
    from matplotlib.rcsetup import interactive_bk as _interactive_bk
    import matplotlib.pyplot
    pyplotShow = matplotlib.pyplot.show
    def show(*args, **kw):
        pyplotShow(block=False, *args, **kw)
    matplotlib.pyplot.show = show  # monkeypatch plt.show to default to non-blocking mode

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

    def write(self, s): pass

pipedFunctions = {}
def fromPipe(symbol):
    def decorator(func):
        global pipedFunctions
        pipedFunctions[symbol] = func
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
        self.interp = code.InteractiveInterpreter(globals())

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
            object = eval(self.code, self.interp.locals, globals())
            if object is not None:
                result = repr(object)
            else:
                result = ''
            if not self.buffer.empty():
                result = ''.join([i for e,i in self.buffer.read() if not e]) + result
            err = False
        except:
            err = True
            self.interp.showtraceback()
            result = self.buffer.read()
        return err, result

    @fromPipe('D')
    def execute(self):
        try:
            exec(self.code, self.interp.locals, globals())
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
        endLine = ''
        lines = []
        for l in value[:nMax].split('\n'):
            lines += textwrap.wrap(l, cMax)
        value = '\n'.join(lines[:lMax]) + ('\n...' if len(lines) > lMax else '')
        return value

    @fromPipe('F')
    def getCallTip(self, line, var, truncate=True):
        element = introspect.getRoot(line)
        if len(element) < len(var): return
        try:
            object = eval(element, self.interp.locals, globals())
        except:
            return
        if var in element:
            try:
                funcName, funcParam, funcHelp = introspect.getCallTip(element, locals= self.interp.locals)
            except:
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
            autoCompleteList = dir(eval(element, self.interp.locals, globals()))
            if len(autoCompleteList) > 0:
                #autoCompleteList = '\t'.join(sorted([i for i in autoCompleteList if not i.startswith('_')]) + \
                #        sorted([i for i in autoCompleteList if i.startswith('_')]))
                # The scintilla option for unordered lists seems not to work:
                #     editor.autoCSetOrder(2)
                autoCompleteList = '\t'.join(sorted(autoCompleteList))
        except:
            autoCompleteList = None
        return autoCompleteList

    @fromPipe('I')
    def autoCompleteFunction(self, linePart):
        element = introspect.getRoot(linePart)
        funcName, funcParam, funcHelp = introspect.getCallTip(element, locals= self.interp.locals)
        self.fullCallTip = funcName, funcHelp
        callTip = self.maxCallTip(funcHelp)
        return len(funcName)-1, funcParam, callTip

    @fromPipe('J')
    def autoCompleteDict(self, linePart):
        element = introspect.getRoot(linePart)
        autoCompleteList = None
        try:
            object = eval(element, self.interp.locals, globals())
            t = type(object)
            if t is dict or 'h5py.' in str(t):
                autoCompleteList = '\t'.join(sorted([repr(i) for i in object.keys()])) if len(object) < 1000 else None
        except:
            pass
        return autoCompleteList

    @fromPipe('K')
    def showtraceback(self):
        """Display the exception that just occurred.
        The first two stack items are removed because it is
        not the user code."""
        try:
            type, value, tb = sys.exc_info()
            sys.last_type = type
            sys.last_value = value
            sys.last_traceback = tb
            tblist = traceback.extract_tb(tb)
            del tblist[:2]
            list = traceback.format_list(tblist)
            if list:
                list.insert(0, "Traceback (most recent call last):\n")
            list[len(list):] = traceback.format_exception_only(type, value)
        finally:
            tblist = tb = None
        map(sys.stderr, list)


def startRemoteClient():

    interp = interpreter()

    dataQueueOut = Queue.Queue()
    dataQueueIn = Queue.Queue()

    def communicationLoop():
        while True:
            # receive the id of the function
            command = interp.stdin.read(1)

            # unpickle the received data
            dataFromPipe = pickle.load(interp.stdin)

            # to queue for execution in main thread
            dataQueueIn.put((command, dataFromPipe))

            # get answer of function from queue
            dataToPipe = dataQueueOut.get()

            # pickle the result of the function
            ret = pickle.dumps(dataToPipe,-1)

            # send the result to the pipe
            interp.stdout.write(ret)

    thread = threading.Thread(name='communicationLoop', target=communicationLoop, args=())
    thread.start()

    def matplotlib_EventHandler(interval):
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
        if activateMatplotlibEventHandler:
            matplotlib_EventHandler(0.05)
        else:
            time.sleep(0.05)

    # busyLoop = threading.Event()
    # busyLoop.clear()
    
    # def busyLoop():
        # while True:
            # busyLoop.wait()
            # busyLoop.clear()
            
    isExecuting = False
            
    # endless loop in the client mode
    while thread.is_alive():
        while dataQueueIn.empty():
            wait()
        command, dataFromPipe = dataQueueIn.get()
        if command == "X": break
        # busyLoop.set() #  let the busyLoop do the communication
        dataToPipe = pipedFunctions[command](interp, *dataFromPipe)
        # busyLoop.clear() #  stop the busyLoop and let the main loop do the communication
        dataQueueOut.put(dataToPipe)


#
# Main function for the pyPadClient to run inside the python subprocess.
#
if __name__ == '__main__':
    startRemoteClient()
    exit()
