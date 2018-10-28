#
# PyPadPlusPlus: Module running in Python subprocess
#

import sys, code
import introspect  # Module for code introspection from the wxPython project
from codeop import compile_command
import threading
import traceback
import textwrap
#import Queue
try:
   import cPickle as pickle
except:
   import pickle
   
from functools import wraps

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
        #console.write('buff:'+s+'\n')
        self.buffer.write(s)
        
    def writeStdErr(self, s):
        #console.writeError('buff:'+s+'\n')
        self.buffer.write(s, True)
        
    def write(self, s): pass

def withPipe(func):
    """ Decorate a function to pickle the input and output
    """
    @wraps(func)
    def pickledFunc(self, *args):
        if self.usePipe:
            res = func(self, *cPickle.loads(args[0], encoding='latin1'))
            return cPickle.dumps(res,-1)
        else:
            return func(self, *args)
    return pickledFunc
    
class interpreter:
    def __init__(self):
        self.buffer = bufferOut()
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        self.stdin = sys.stdin
        self.stdOutBuff = PseudoFileOutBuffer(self.buffer)
        self.stdErrBuff = PseudoFileOutBuffer(self.buffer, True)
        self.interp = code.InteractiveInterpreter(globals())
        sys.stdout=self.stdOutBuff
        sys.stderr=self.stdErrBuff

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
                #console.writeError('\n')
                self.interp.showsyntaxerror(filename)
                err = self.buffer.read()
        
        requireMore = code is None and err is None
        if not requireMore:
            self.code = code

        return err, requireMore, isValue
        
    def evaluate(self):
        try:
            object = eval(self.code,self.interp.locals,globals())
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

    def flush(self):
        # try:
            # self.interp.showtraceback()
        # except:
            # pass
        err = False
        result = self.buffer.read()
        return err, result            
            
    def execute(self):
        try:
            exec(self.code, self.interp.locals, globals())
            err = False
        except:
            err = True
            self.interp.showtraceback()
        return err, self.buffer.read()
        
    def maxCallTip(self, value):
        '''Truncates text to fit in a call tip window.'''
        nMax = 2000  # max length
        cMax = 100  # max colums
        lMax = 14  # max lines
        endLine = ''
        n = len(value)
        if n > nMax:
            value = value[:nMax]
            endLine = '\n...'
        value = '\n'.join(['\n'.join(textwrap.wrap(i, cMax)) for i in value[:nMax].split('\n')[:lMax]])
        return value + endLine
    
    def getCallTip(self, line, var, truncate=True):
        element = introspect.getRoot(line)
        if len(element) < len(var): return
        try:
            object = eval(element,self.interp.locals,globals())
        except:
            return
        if var in element:
            try:
                funcName, funcParam, funcHelp = introspect.getCallTip(element, locals=self.interp.locals)
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
                textFull = value = str(object)
                if truncate: value = self.maxCallTip(textFull)
                calltip = 'type: ', typ, '\nstr: ', ('\n' if '\n' in value else '') + value
            self.fullCallTip = var, calltip[:-1] + (textFull,)
        nHighlight = 0
        for i,ct in enumerate(calltip[:3]):
            nHighlight += len(ct)
        
        return element, str(nHighlight), calltip
            
    def getFullCallTip(self):
        return self.fullCallTip
            
    def autoCompleteObject(self, linePart):
        element = introspect.getRoot(linePart)
        try:
            autoCompleteList = dir(eval(element,self.interp.locals,globals()))
            if len(autoCompleteList) > 0:
                #autoCompleteList = '\t'.join(sorted([i for i in autoCompleteList if not i.startswith('_')]) + \
                #        sorted([i for i in autoCompleteList if i.startswith('_')]))
                # The scintilla option for unordered lists seems not to work:
                #     editor.autoCSetOrder(2)
                autoCompleteList = '\t'.join(sorted(autoCompleteList))
        except:
            autoCompleteList = None
        return autoCompleteList

    def autoCompleteFunction(self, linePart):
        element = introspect.getRoot(linePart)
        funcName, funcParam, funcHelp = introspect.getCallTip(element, locals=self.interp.locals)
        self.fullCallTip = funcName, funcHelp
        callTip = self.maxCallTip(funcHelp)
        return len(funcName)-1, funcParam, callTip

    def autoCompleteDict(self, linePart):
        element = introspect.getRoot(linePart)
        autoCompleteList = None
        try:
            object = eval(element,self.interp.locals,globals())
            t = type(object)
            if t is dict or 'h5py.' in str(t):
                autoCompleteList = '\t'.join(sorted([repr(i) for i in object.keys()])) if len(object) < 1000 else None
        except:
            pass
        return autoCompleteList

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
    
#
# Main function for the pyPadClient to run inside the python subprocess.
# This function is under construction.
#
if __name__ == '__main__':

    execute = False
    interp = interpreter()
    
    def executeFlag():
        execute = True
        
    def wait():
        time.sleep(0.1)

    func = {
        'A': interp.tryCode,
        'B': interp.evaluate,
        'C': executeFlag,
        'D': interp.getCallTip,
        'E': interp.autoCompleteObject,
        'F': interp.autoCompleteFunction,
        'G': interp.autoCompleteDict,
        'H': interp.getFullCallTip,
        'I': interp.flush
        }

    commandQueue = Queue.LifoQueue()
    output = []
    
    def communicationLoop(queue):
        while True:
            # receive the id of the function
            command = interp.stdin.read(1)
            
            # receive number of bytes of the data
            n = int(interp.stdin.readline(), 16)
            if n < 0: exit()
            
            # unpickle the received data
            args = pickle.loads(interp.stdin.read(n))
            
            # call the function and pickle the result
            ret = pickle.dumps(func[command](*args),-1)
            
            # send size of the result to the pipe
            interp.stdout.write(hex(len(ret))+'\n')
            
            # send the result to the pipe
            interp.stdout.write(ret)    
            
            
    thread = threading.Thread(name='communicationLoop', target=communicationLoop, args=(queue,))
    thread.start()
   
    # def doCommand():
        # # receive the id of the function
        # command = interp.stdin.read(1)
        
        # # receive number of bytes of the data
        # n = int(interp.stdin.readline(), 16)
        # if n < 0: exit()
        
        # # unpickle the received data
        # args = pickle.loads(interp.stdin.read(n))
        
        # # call the function and pickle the result
        # ret = pickle.dumps(func[command](*args),-1)
        
        # # send size of the result to the pipe
        # interp.stdout.write(hex(len(ret))+'\n')
        
        # # send the result to the pipe
        # interp.stdout.write(ret)    
    
    
    # enless loop in the client mode
    while thread.is_alive():
    
        if execute:
            interp.execute()
            
        wait()

        #doCommand(commandQueue.get())
        
        #if commandQueue.empty():
        #    wait()
    
    exit()

