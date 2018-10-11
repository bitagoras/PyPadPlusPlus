# PyPadPlusPlus: A Notepad++ plugin for interactive Python development,
# based on the Python Script plugin

__author__ = "Christian Schirm"
__copyright__ = "Copyright 2018"
__license__ = "GPLv3"
__version__ = "0.2"

from Npp import *
import code, sys, time
from codeop import compile_command
import introspect  # Module for code introspection from the wxPython project
import traceback
import threading
import textwrap
import pyPadHost
import pyPadClient


class pyPad:
    def __init__(self, externalPython=False):
        '''Initializes PyPadPlusPlus to prepare Notepad++
        for interactive Python development'''
        self.stdout=console.write
        self.stderr=console.writeError
        self.thread = None
        self.lock = False
        self.holdMarker = False
        self.activeCalltip = None
        console.show()
        editor.grabFocus()
        console.clear()
        editor.setTargetStart(0)
        if externalPython:
            self.interp = pyPadHost.interpreter()
        else:
            self.interp = pyPadClient.interpreter()
        editor.callTipSetBack((255,255,225))
        console.editor.setReadOnly(0)
		# editor.autoCSetIgnoreCase(True)
        editor.autoCSetSeparator(ord('\t'))

		# Marker margin
        self.markerWidth = 3
        self.markers = None
        editor.markerDeleteAll(8)
        editor.markerDeleteAll(7)
        editor.markerDeleteAll(6)
        editor.markerDefine(8, MARKERSYMBOL.LEFTRECT)
        editor.markerDefine(7, MARKERSYMBOL.RGBAIMAGE)
        editor.markerDefine(6, MARKERSYMBOL.RGBAIMAGE)
        editor.setMarginWidthN(3, self.markerWidth)
        editor.setMarginMaskN(3, 256+128+64)

        self.fade = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
            255, 255, 255, 255, 255, 255, 255, 252, 246, 240, 234, 228, 223,
            217, 211, 205, 199, 193, 188, 182, 176, 170, 164, 159, 153, 147,
            141, 135, 130, 124, 118, 112, 106, 101, 95, 89, 83, 77, 71, 66,
            60, 54, 48, 42, 37, 31, 25]

        editor.setMouseDwellTime(750)
        editor.callback(self.onMouseDwell, [SCINTILLANOTIFICATION.DWELLSTART])
        editor.clearCallbacks([SCINTILLANOTIFICATION.CHARADDED])
        editor.callback(self.onAutocomplete, [SCINTILLANOTIFICATION.CHARADDED])
        editor.clearCallbacks([SCINTILLANOTIFICATION.MODIFIED])
        editor.callback(self.textModified, [SCINTILLANOTIFICATION.MODIFIED])

        editor.clearCallbacks([SCINTILLANOTIFICATION.CALLTIPCLICK])
        editor.callback(self.onCalltipClick, [SCINTILLANOTIFICATION.CALLTIPCLICK])

    def execute(self, moveCursor=True):
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
        elif lang != LANGTYPE.PYTHON: return

        # add more lines until the parser is happy or finds
        # a syntax error
        requireMore = True
        err = None
        
        while requireMore:
            block = editor.getTextRange(iStart, iEnd).rstrip()
            err, requireMore, isValue = self.interp.tryCode(iLineStart, filename, block)
            
            if requireMore:
                iEnd = next(getEnd, -1)
                if iEnd == -1:
                    iStart = iEnd = iPos
                    break
            
        iLineStart, iLineEnd = editor.lineFromPosition(iStart), editor.lineFromPosition(iEnd)
        self.setMarkers((iLineStart, iLineEnd), block, color='a' if not err else 'r')

        if err is not None:
            if moveCursor:
                editor.setSelectionStart(iPos)
                editor.scrollCaret()
            self.out(err)

        else:

            # Start a thread to execute the code
            
            iNewPos = max(iPos, editor.positionFromLine(iLineEnd + 1))
            if moveCursor:
                editor.setSelectionStart(iNewPos)
                editor.setCurrentPos(iNewPos)
                editor.scrollCaret()

            self.lock = True
            if isValue:
                self.thread = threading.Thread(name='threadValue', target=self.threadValue, args=())
            else:
                self.thread = threading.Thread(name='threadCode', target=self.threadCode, args=())

            if not err:
                self.holdMarker = True
                self.thread.start()
        if err:
            self.setMarkers(color='r')
            self.holdMarker = False
            console.editor.setReadOnly(0)
            self.lock = False

    def threadValue(self):
        '''Thread of the running code in case the code is
        a value. When finished, the execution markers are
        set to the corresponding color.'''
        err, result = self.interp.evaluate()
        console.editor.beginUndoAction()
        if not err:
            self.setMarkers(color='f')
            if result: self.stdout(result+'\n')
        else:
            self.setMarkers(color='r')
            self.out(result)
        console.editor.endUndoAction()
        self.lock = False
        console.editor.setReadOnly(0)

        # wait some seconds until the markers can hide
        time.sleep(3)
        self.holdMarker = False

    def threadCode(self):
        '''Thread of the running code in case the code is
        not a value. When finished, the execution markers are
        set to the corresponding color.'''
        err, result = self.interp.execute()
        if not err:
            self.setMarkers(color='f')
        else:
            self.setMarkers(color='r')
        console.editor.beginUndoAction()
        self.out(result)
        console.editor.endUndoAction()
        self.lock = False
        console.editor.setReadOnly(0)

        # wait some seconds until the markers can hide
        time.sleep(3)
        self.holdMarker = False
        
    def out(self, buffer):
        #console.write('buff:'+buffer)
        for err, line in buffer:
            if err: self.stderr(line)
            else: self.stdout(line)
        console.editor.setReadOnly(0)

    def outx(self, *text):
        #console.write('buff:'+buffer)
        if type(text) is not str: text = repr(text)
        console.write('\n'+text+'\n')
        console.editor.setReadOnly(0)  
        
    def setMarkers(self, iRange=(0, 0), block=None, color=None):
        '''Set markers at the beginning and end of the executed
        code block, to show the user which part is actually executed
        and if the code is still running or finished or if errors
        occurred.'''
        if color == 'r':
            c = (255,100,100) # color error
        elif color == 'f':
            c = (255,220,0) # color finished
        elif color == 'a':
            c = (150,150,150) # color active
            #c = (53, 107, 196) # color active
        if block or color is None:
            editor.markerDeleteAll(8)
            editor.markerDeleteAll(7)
            editor.markerDeleteAll(6)
            self.markers = False
        if block or color is not None:
            hLine = len(self.fade)
            rgb = chr(c[0])+chr(c[1])+chr(c[2])
            rgba = ''.join([(rgb+chr(f))*self.markerWidth for f in self.fade])
            rgba_r = ''.join([(rgb+chr(f))*self.markerWidth for f in reversed(self.fade)])
            editor.rGBAImageSetWidth(self.markerWidth)
            editor.rGBAImageSetHeight(hLine)
            editor.markerDefineRGBAImage(6, rgba)
            editor.markerDefineRGBAImage(7, rgba_r)
            editor.markerSetBack(8, c)
        if block:
            iLineStart, iLineEnd = iRange
            lineHasCode = [len(line) > 0 and not (line.isspace() or line.startswith('#')) for line in block.splitlines()]
            linesWithCode = [i for i, c in enumerate(lineHasCode) if c]
            firstMarker = iLineStart + linesWithCode[0]
            lastMarker = iLineStart + linesWithCode[-1]
            nExtraLines = lastMarker - firstMarker + 1
            if nExtraLines <= 4:
                for iLine in range(nExtraLines):
                    editor.markerAdd(firstMarker+iLine, 8)
            else:
                editor.markerAdd(firstMarker, 8)
                editor.markerAdd(firstMarker+1, 6)
                editor.markerAdd(lastMarker-1, 7)
                editor.markerAdd(lastMarker, 8)
            self.markers = True

    def textModified(self, args):
        '''When the text is modified the execution markers
        will be hidden, except when the code is running or
        when the color just has changed in the last few seconds.'''
        if args['text']:
            id = notepad.getCurrentBufferID()
            if self.markers is not None and self.markers != id and not (self.lock or self.holdMarker):
                editor.markerDeleteAll(6)
                editor.markerDeleteAll(7)
                editor.markerDeleteAll(8)
                self.markers = id

    def onCalltipClick(self, args):
        if self.activeCalltip:# and args['position']==0:
            element, nHighlight, calltip = self.interp.getCallTip(*self.activeCalltip, truncate=False)
            var = element # self.activeCalltip[1]
            if len(var) > 50: var = var[:50] + '...'
            head = '-'*(40 - len(var)//2 - 3) + ' Calltip: ' + var + ' ' + '-'*(40 - len(var)//2 - 3)
            foot = '-'*len(head)
            console.editor.beginUndoAction()
            self.stdout('\n' + head + '\n' + ''.join(calltip) + '\n' + foot + '\n')
            console.editor.endUndoAction()
            console.editor.setReadOnly(0)
                
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
            try:
                element, nHighlight, calltip = self.interp.getCallTip(line, var)
                self.activeCalltip = line, var
                editor.callTipShow(iStart, ''.join(calltip))
                editor.callTipSetHlt(0, int(nHighlight))
            except:
                pass

    def onAutocomplete(self, args):
        '''Check if auto complete data can added and displayed:
        "." after objects: show auto completion list with properties and methods
        "[" after dict: show auto completion list with keys
        "(" after functions: insert template and display a call tip with the doc string.'''
        if args['ch'] == 46 and args['code'] == 2001: # character "."
            iPos = editor.getCurrentPos()
            autoCompleteList = self.interp.autoCompleteObject(self.getUncompleteLine(iPos))
            if autoCompleteList:
                editor.autoCSetSeparator(ord('\t'))
                editor.autoCShow(0, autoCompleteList)
        elif args['ch'] == 40 and args['code'] == 2001: # character "("
            iPos = editor.getCurrentPos()
            n, funcParam, callTip = self.interp.autoCompleteFunction(self.getUncompleteLine(iPos))
            if callTip:
                editor.callTipShow(max(0,iPos-n), callTip)
                editor.callTipSetHlt(0, max(0, callTip.find('\n')))
            if funcParam:
                editor.insertText(iPos,funcParam+')')
                editor.setSelectionStart(iPos)
                editor.setSelectionStart(iPos + len(funcParam) + 1)
                editor.setCurrentPos(iPos)
        elif args['ch'] == 91 and args['code'] == 2001: # character "["
            iPos = editor.getCurrentPos()
            autoCompleteList = self.interp.autoCompleteDict(self.getUncompleteLine(iPos))
            if autoCompleteList:
                editor.autoCSetSeparator(ord('\t'))
                editor.autoCShow(0, autoCompleteList)

    def getUncompleteLine(self, iPos):
        '''get the whole expression with the context of a
        variable that is required to evaluate the variable'''
        iLine = editor.lineFromPosition(iPos)
        iStart = editor.positionFromLine(iLine)
        linePart = editor.getTextRange(iStart, iPos - 1)
        return linePart

    def completeBlockStart(self, iLine):
        '''Add preceding lines that are required to execute
        the selected code, e.g. the beginning of an indented
        code block.'''
        lineRequiresMoreLinesBefore = False
        n = editor.getLength()
        while iLine >= 0:
            iStart = editor.positionFromLine(iLine)
            iEnd = editor.getLineEndPosition(iLine)
            line = editor.getTextRange(iStart, iEnd).rstrip()
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
        iLastWithCode = iEnd = iEndTest = editor.getLineEndPosition(iLine)
        while iEndTest < n:
            lineTest = editor.getTextRange(iStartTest, iEndTest).rstrip()
            noCodeLine = len(lineTest) == 0 or lineTest.startswith('#')
            lineBelongsToBlock = len(lineTest)==0 or lineTest.startswith(' ') \
                    or lineTest.startswith('\t') or lineTest.startswith('else:') \
                    or lineTest.startswith('elif') or lineTest.startswith('except:') \
                    or lineTest.startswith('finally:')
            if not lineBelongsToBlock:
                yield iLastWithCode
            if not noCodeLine: iLastWithCode = iEndTest
            iEnd = iEndTest
            iLine += 1
            iEndTest = editor.getLineEndPosition(iLine)
            iStartTest = editor.positionFromLine(iLine)
        yield n

    def __del__(self):
        '''Clear call backs on exit.'''
        editor.clearCallbacks([SCINTILLANOTIFICATION.CALLTIPCLICK])
        editor.clearCallbacks([SCINTILLANOTIFICATION.CHARADDED])
        editor.clearCallbacks([SCINTILLANOTIFICATION.MODIFIED])
        editor.clearCallbacks([SCINTILLANOTIFICATION.DWELLSTART])
