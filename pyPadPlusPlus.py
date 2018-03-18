# PyPadPlusPlus: A Notepad++ plugin for interactive Python development,
# based on the Python Script plugin

__author__ = "Christian Schirm"
__copyright__ = "Copyright 2018"
__license__ = "GPLv3"
__version__ = "0.1"

from Npp import *
import code, sys, time
from codeop import compile_command
import introspect  # Module for code introspection from the wxPython project
import traceback
import threading
import textwrap

class PseudoFileOut:
    def __init__(self, write):
        self.write = write
    def write(self, s): pass
    # def readline(self): pass
    # def writelines(self, l): map(self.write, l)
    # def flush(self): pass
    # def isatty(self): return 1

class pyPad:
    def __init__(self):
        '''Initializes PyPadPlusPlus to prepare Notepad++ 
        for interactive Python development'''
        sys.stdout=PseudoFileOut(console.write)
        sys.stderr=PseudoFileOut(console.writeError)
        sys.stdout.outp=PseudoFileOut(console.write)
        self.markers = None
        self.thread = None
        self.lock = False
        self.holdMarker = False
        console.show()
        editor.grabFocus()
        console.clear()
        editor.setTargetStart(0)
        editor.clearCallbacks([SCINTILLANOTIFICATION.CHARADDED])
        editor.callback(self.onAutocomplete, [SCINTILLANOTIFICATION.CHARADDED])
        editor.clearCallbacks([SCINTILLANOTIFICATION.MODIFIED])
        editor.callback(self.textModified, [SCINTILLANOTIFICATION.MODIFIED])
        self.interp = code.InteractiveInterpreter(globals())
        editor.callTipSetBack((255,255,225))
        console.editor.setReadOnly(0)
		#editor.autoCSetIgnoreCase(True)
		
		# Marker margin
        editor.setMarginWidthN(3, 4)
        editor.setMarginMaskN(3, 256+128)
        editor.markerDefine(8, MARKERSYMBOL.LEFTRECT)
        editor.markerDefine(7, MARKERSYMBOL.LEFTRECT)
        editor.markerDeleteAll(8)
        editor.markerDeleteAll(7)
        self.setMarkers(color='a')
        editor.autoCSetSeparator(ord('\t'))

        editor.setMouseDwellTime(750)
        editor.callback(self.onMouseDwell, [SCINTILLANOTIFICATION.DWELLSTART])        
        
    def __del__(self):
        '''Clear call backs on exit.'''
        editor.clearCallbacks([SCINTILLANOTIFICATION.CHARADDED])
        editor.clearCallbacks([SCINTILLANOTIFICATION.MODIFIED])
        editor.clearCallbacks([SCINTILLANOTIFICATION.DWELLSTART])
        
    def textModified(self, args):
        '''When the text is modified the execution markers
        will be hidden, except when the code is running or
        when the color as changed in the last few seconds.'''
        if args['text']:
            id = notepad.getCurrentBufferID()
            if self.markers is not None and self.markers != id and not (self.lock or self.holdMarker):
                editor.markerDeleteAll(7)
                editor.markerDeleteAll(8)
                self.markers = id

    def onMouseDwell(self, args):
        '''Show a call tip window about the current content
        of a selected variable'''
        if editor.callTipActive(): return
        p = editor.positionFromPoint(args['x'], args['y'])
        iStart = editor.getSelectionStart()
        iEnd = editor.getSelectionEnd()
        if iStart != iEnd and iStart <= p <= iEnd:
            iLineStart = editor.positionFromLine(editor.lineFromPosition(iStart))
            var = editor.getTextRange(iStart, iEnd)
            line = editor.getTextRange(iLineStart, iEnd)
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
                if funcHelp:
                    calltip = 'type: ', str(type(object)), '\ndoc:\n', self.maxCallTip(funcHelp)
                else:
                    value = self.maxCallTip(str(object))
                    calltip = 'type: ', str(type(object)), '\nstr: ', \
                            ('\n' if '\n' in value else '') + value
                editor.callTipShow(iStart, ''.join(calltip))
                accumulate = 0
                for i,ct in enumerate(calltip[:3]):
                    accumulate += len(ct)
                editor.callTipSetHlt(0, accumulate)
                
    def maxCallTip(self, value):
        '''Truncates text to fit in a call tip window.'''
        nMax = 2000  # max length
        cMax = 100  # max colums
        lMax = 30  # max lines
        endLine = ''
        n = len(value)
        if n > nMax:
            value = value[:nMax]
            endLine = '\n...'
        value = '\n'.join(['\n'.join(textwrap.wrap(i, cMax)) for i in value[:nMax].split('\n')[:lMax]])
        return value + endLine
                
    def onAutocomplete(self, args):
        '''Check if auto complete data can added and displayed:
        "." after objects: show auto completion list with properties and methods
        "[" after dict: show auto completion list with keys
        "(" after functions: insert template and display a call tip with the doc string.'''
        if args['ch'] == 46 and args['code'] == 2001: # character "."
            iPos = editor.getCurrentPos()
            element = self.getCodeElement(iPos)
            try:
                autoCompleteList = dir(eval(element,self.interp.locals,globals()))
                if len(autoCompleteList) > 0:
                    autoCompleteList = sorted([i for i in autoCompleteList if not i.startswith('_')]) + \
                            sorted([i for i in autoCompleteList if i.startswith('_')])
                    editor.autoCSetSeparator(ord('\t'))
                    editor.autoCShow(0, '\t'.join(autoCompleteList))
            except:
                pass
        elif args['ch'] == 40 and args['code'] == 2001: # character "("
            iPos = editor.getCurrentPos()
            element = self.getCodeElement(iPos)
            funcName, funcParam, funcHelp = introspect.getCallTip(element, locals=self.interp.locals)
            callTip = self.maxCallTip(funcHelp)
            if funcHelp:
                editor.callTipShow(max(0,iPos-len(funcName)-1), callTip)
                editor.callTipSetHlt(0, max(0, callTip.find('\n')))
            if funcParam:
                editor.insertText(iPos,funcParam+')')
                editor.setSelectionStart(iPos)
                editor.setSelectionStart(iPos + len(funcParam) + 1)
                editor.setCurrentPos(iPos)
        elif args['ch'] == 91 and args['code'] == 2001: # character "["
            try:
                iPos = editor.getCurrentPos()
                element = self.getCodeElement(iPos)
                object = eval(element,self.interp.locals,globals())
                if type(object) is dict:
                    editor.autoCSetSeparator(ord('\t'))
                    editor.autoCShow(0, '\t'.join([repr(i).replace('\t','\\t') for i in object.keys()]))
            except:
                pass
        
    def getCodeElement(self, iPos):
        '''get the whole expression with the context of a
        variable that is required to evaluate the variable'''
        iLine = editor.lineFromPosition(iPos)
        iStart = editor.positionFromLine(iLine)
        linePart = editor.getTextRange(iStart, iPos - 1)
        return introspect.getRoot(linePart)
        
        
    def completeBlockStart(self, iLine):
        '''Add preceding lines that are required to execute
        the selected code, e.g. the beginning of an indented
        code block.'''
        lineRequiresMoreLinesBefore = False
        n = editor.getLength()
        while iLine >= 0:
            iStart = editor.positionFromLine(iLine)
            line = editor.getTextRange(iStart, min(iStart + 10, n-1)).rstrip()
            lineRequiresMoreLinesBefore = (lineRequiresMoreLinesBefore and len(line)==0) \
                    or line.startswith(' ') or line.startswith('\t') \
                    or line.startswith('else:') or line.startswith('elif') \
                    or line.startswith('except:') or line.startswith('finally:')
            if not lineRequiresMoreLinesBefore:
                break
            iLine -= 1
        return iStart

    def completeBlockEnd(self, iLine):
        '''Add following lines that are required to execute
        the selected code, without leaving code that cannot
        be executed seperately in the next step.'''
        n = editor.getLength()
        iStartTest = editor.positionFromLine(iLine)
        iEnd = iEndTest = editor.getLineEndPosition(iLine)
        while iEndTest < n:
            lineTest = editor.getTextRange(iStartTest, iEndTest).rstrip()
            lineBelongsToBlock = (len(lineTest)==0) or lineTest.startswith(' ') \
                    or lineTest.startswith('\t') or lineTest.startswith('else:') \
                    or lineTest.startswith('elif') or lineTest.startswith('except:') \
                    or lineTest.startswith('finally:')
            if not lineBelongsToBlock:
                yield iEnd
            iEnd = iEndTest
            iLine += 1
            iEndTest = editor.getLineEndPosition(iLine)
            iStartTest = editor.positionFromLine(iLine)
        yield n

    def execute(self):
        '''Executes the smallest possible code element
        for the current selection.'''
        if self.lock: return
        iPos = editor.getCurrentPos()
        iLineStart = editor.lineFromPosition(editor.getSelectionStart())
        iLineEnd = max(iLineStart, editor.lineFromPosition(editor.getSelectionEnd()-1))
        iStart = self.completeBlockStart(iLineStart)
        iLineStart = editor.lineFromPosition(iStart)
        getEnd = self.completeBlockEnd(iLineEnd)
        iEnd = next(getEnd)
        filename = notepad.getCurrentFilename()
        lang = notepad.getLangType()
        if lang == LANGTYPE.TXT and '.' not in filename:
            notepad.setLangType(LANGTYPE.PYTHON)
            
        # add more lines until the parser is happy or finds
        # a syntax error
        code = None
        err = False
        while code is None:
            block = editor.getTextRange(iStart, iEnd).rstrip()
            try:
                code = compile_command('\n' * iLineStart + block, filename, 'eval')
                value = True
            except (OverflowError, SyntaxError, ValueError):
                try:
                    code = compile_command('\n' * iLineStart + block + '\n', filename, 'exec')
                    value = False
                except (OverflowError, SyntaxError, ValueError):
                    err = True
                    console.write('\n')
                    self.interp.showsyntaxerror(filename)
                    break
            if code is None:
                iEnd = next(getEnd, -1)
                if iEnd == -1:
                    err= True
                    iStart = iEnd = iPos
                    break

        iLineStart, iLineEnd = editor.lineFromPosition(iStart), editor.lineFromPosition(iEnd)
        self.setMarkers((iLineStart, iLineEnd), block, color='a' if not err else 'r')

        if err:
            editor.setSelectionStart(iPos)
            editor.scrollCaret()
            
        # Start a thread to execute the code
        
        if not err:
            
            iNewPos = max(iPos, editor.positionFromLine(iLineEnd + 1))
            editor.setSelectionStart(iNewPos)
            editor.setCurrentPos(iNewPos)
            editor.scrollCaret()

            self.lock = True
            if value:
                try:
                    self.thread = threading.Thread(name='threadValue', target=self.threadValue, args=(code,))
                except:
                    err = True
                    console.write('\n')
                    self.interp.showtraceback()
            else:
                self.thread = threading.Thread(name='threadCode', target=self.threadCode, args=(code,))
                
            if not err:
                self.holdMarker = True
                self.thread.start()
        if err:
            self.setMarkers(color='r')
            self.holdMarker = False
            console.editor.setReadOnly(0)
            self.lock = False

    def threadValue(self,code):
        '''Thread of the running code in case the code is
        a value. When finished, the execution markers are
        set to the coresponding color.'''
        try:
            print repr(eval(code,self.interp.locals,globals()))
            err = False
        except:
            err = True
            self.interp.showtraceback()
        if not err:
            self.setMarkers(color='f')
        else:
            self.setMarkers(color='r')
        self.lock = False
        console.editor.setReadOnly(0)
        
        # wait some seconds until the markers can hide
        time.sleep(2) 
        self.holdMarker = False
        
    def threadCode(self,code):
        '''Thread of the running code in case the code is
        not a value. When finished, the execution markers are
        set to the coresponding color.'''
        try:
            exec(code,self.interp.locals,globals())
            err = False
        except:
            err = True
            self.interp.showtraceback()
        if not err:
            self.setMarkers(color='f')
        else:
            self.setMarkers(color='r')
        self.lock = False
        console.editor.setReadOnly(0)
        
        # wait some seconds until the markers can hide
        time.sleep(2)
        self.holdMarker = False

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
            
    def setMarkers(self, iRange=(0, 0), block='', color=None):
        '''Set markers at the beginning and end of the executed
        code block, to show the user which part is actually executed
        and if the code is still running or finished or if errors
        occurred.'''
        if block or color is None:
            editor.markerDeleteAll(8)
            editor.markerDeleteAll(7)
        if block:
            iLineStart, iLineEnd = iRange
            lineHasCode = [len(line) > 0 and not (line.isspace() or line.startswith('#')) for line in block.splitlines()]
            linesWithCode = [i for i, c in enumerate(lineHasCode) if c]
            firstMarker = iLineStart + linesWithCode[0]
            lastMarker = iLineStart + linesWithCode[-1]
            editor.markerAdd(firstMarker, 8)
            if (lastMarker-firstMarker) >= 1:
                editor.markerAdd(lastMarker, 8)
            if (lastMarker-firstMarker) >= 2:
                editor.markerAdd(firstMarker+1, 7)
            if (lastMarker-firstMarker) >= 3:
                editor.markerAdd(lastMarker-1, 7)
            self.markers = True
        if color == 'r':
            colorFull = (255,100,100) # color error
        elif color == 'f':
            colorFull = (255,220,0) # color finished
        elif color == 'a':
            colorFull = (100,100,100) # color active
            #colorFull = (200,200,200) # color active
            #colorFull = (50,50,255) # color active
            #colorFull = (127, 54, 237) # color active
        colorBack = (228, 228, 228)
        colorHalf = tuple([(1*colorFull[i] + 2*colorBack[i]) // 3 for i in 0,1,2])
        editor.markerSetBack(8, colorFull) # color gray
        editor.markerSetBack(7, colorHalf) # color bright gray
