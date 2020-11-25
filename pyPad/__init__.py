# PyPadPlusPlus: A Notepad++ plugin for interactive Python development,
# requires the Python Script plugin.

__author__ = "Christian Schirm"
__copyright__ = "Copyright 2019"
__license__ = "GPLv3"
__version__ = "1.2.1"

import Npp
from Npp import editor, console, notepad
import code, sys, time, os
from codeop import compile_command
#import introspect  # Module for code introspection from the wxPython project
import traceback
import threading
import textwrap
from math import sin, pi

from ctypes import windll, Structure, c_ulong, byref
def GetCursorPos():
    point = (c_ulong*2)()
    windll.user32.GetCursorPos(byref(point))
    return [int(i) for i in point]
def GetWindowRect(hwnd):
    rect = (c_ulong*4)()
    windll.user32.GetWindowRect(hwnd, byref(rect))
    return [int(i) for i in rect]
VK_MBUTTON = 4

init_matplotlib_eventHandler = """try:
    import matplotlib
    from matplotlib import _pylab_helpers
    from matplotlib.rcsetup import interactive_bk as _interactive_bk
    import matplotlib.pyplot
    pyplotShow = matplotlib.pyplot.show
    def show(*args, **kw):
        if not args and not 'block' in kw:
            kw['block'] = False
        pyplotShow(*args, **kw)
    matplotlib.pyplot.show = show  # monkeypatch plt.show to default to non-blocking mode
    active_matplotlib_eventHandler = True
except: pass
"""

class PseudoFileOut:
    def __init__(self, write):
        self.write = write
    def write(self, s): pass

class pyPadPlusPlus:
    def __init__(self, externalPython=None, matplotlib_eventHandler=True, cellHighlight=True,
            popupForUnselectedVariable=True, popupForSelectedExpression=False,
            mouseDwellTime=200):
        '''Initializes PyPadPlusPlus to prepare Notepad++
        for interactive Python development'''
        console.show()
        editor.grabFocus()
        self.windowHandle = windll.user32.GetForegroundWindow()

        sys.stdout=PseudoFileOut(Npp.console.write)
        sys.stderr=PseudoFileOut(Npp.console.writeError)
        sys.stdout.outp=PseudoFileOut(Npp.console.write)
        
        self.matplotlib_eventHandler = matplotlib_eventHandler
        self.matplotlib_enabled = False
        self.popupForUnselectedVariable = popupForUnselectedVariable
        self.popupForSelectedExpression = popupForSelectedExpression
        self.mouseDwellTime = mouseDwellTime

        self.externalPython = bool(externalPython)
        if self.externalPython:
            from . import pyPadHost
            self.interp = pyPadHost.interpreter(externalPython, outBuffer=self.outBuffer)
            #from . import pyPadRemoteHost
            #self.interp = pyPadRemoteHost.interpreter(host="127.0.0.5", port=8888, outBuffer=self.outBuffer)
        else:
            from . import pyPadClient
            self.interp = pyPadClient.interpreter()

        if cellHighlight:
            self.lexer = EnhancedPythonLexer()
            self.lexer.main()
        else:
            self.lexer = None

        self.thread = None
        self.threadMarker = None
        self.bufferActive = 1
        self.delayedMarker = False
        self.activeCalltip = None
        editor.setTargetStart(0)
        self.specialMarkers = None
        self.bufferMarkerAction = {}
        self.lastActiveBufferID = -1

        # Marker
        self.markerWidth = 3
        editor.setMarginWidthN(3, self.markerWidth)
        editor.setMarginMaskN(3, (256+128+64) * (1 + 2**3 + 2**6))
        self.markers = {}
        self.m_active, self.m_error, self.m_finish = [6 + 3*i for i in [0,1,2]]
        self.preCalculateMarkers()
        for iMarker in self.m_active, self.m_error, self.m_finish:
            self.drawMarker(iMarker)

        self.setCallbacks()

        editor.callTipSetBack((255,255,225))
        editor.autoCSetSeparator(ord('\t'))
        editor.autoCSetIgnoreCase(False)
        editor.autoCSetCaseInsensitiveBehaviour(False)
        editor.autoCSetCancelAtStart(False)
        editor.autoCSetDropRestOfWord(False)

        console.clear()
        console.editor.setReadOnly(0)

        self.tTimerFlush = 0.15
        self.tTimerMiddleButton = 0.1
        self.middleButton = 0

        self.bufferActive = 0
        self.onTimerFlush()  # start periodic timer to check output of subprocess
        self.onTimerMiddleButton()  # start periodic timer to check state of middleButton

    def clearCallbacks(self):
        editor.clearCallbacks([Npp.SCINTILLANOTIFICATION.CALLTIPCLICK])
        editor.clearCallbacks([Npp.SCINTILLANOTIFICATION.CHARADDED])
        editor.clearCallbacks([Npp.SCINTILLANOTIFICATION.DWELLSTART])
        editor.clearCallbacks([Npp.SCINTILLANOTIFICATION.MODIFIED])
        notepad.clearCallbacks([Npp.NOTIFICATION.BUFFERACTIVATED])
        notepad.clearCallbacks([Npp.NOTIFICATION.SHUTDOWN])
        if self.lexer:
            notepad.clearCallbacks([Npp.SCINTILLANOTIFICATION.UPDATEUI])
            notepad.clearCallbacks([Npp.NOTIFICATION.LANGCHANGED])

    def setCallbacks(self):
        self.clearCallbacks()
        editor.setMouseDwellTime(self.mouseDwellTime)
        editor.callback(self.onCalltipClick, [Npp.SCINTILLANOTIFICATION.CALLTIPCLICK])
        editor.callback(self.onAutocomplete, [Npp.SCINTILLANOTIFICATION.CHARADDED])
        editor.callback(self.onMouseDwell, [Npp.SCINTILLANOTIFICATION.DWELLSTART])
        editor.callback(self.textModified, [Npp.SCINTILLANOTIFICATION.MODIFIED])
        notepad.callback(self.onBufferActivated, [Npp.NOTIFICATION.BUFFERACTIVATED])
        notepad.callback(self.onShutdown, [Npp.NOTIFICATION.SHUTDOWN])
        if self.lexer:
            editor.callbackSync(self.lexer.on_updateui, [Npp.SCINTILLANOTIFICATION.UPDATEUI])
            notepad.callback(self.lexer.on_langchanged, [Npp.NOTIFICATION.LANGCHANGED])

    def __del__(self):
        '''Clear call backs on exit.'''
        try: self.interp.proc.terminate()
        except: pass
        self.clearCallbacks()

    def onShutdown(self, args):
        try: self.interp.proc.terminate()
        except: pass

    def restartKernel(self):
        if self.externalPython:
            bufferID = self.bufferActive
            self.interp.restartKernel()
            if bufferID:
                self.changeMarkers(iMarker=self.m_error, bufferID=bufferID)
                self.bufferActive = 0
        else:
            self.interp.restartKernel()
        self.hideMarkers()
        self.lastActiveBufferID = -1
        self.setCallbacks()
        self.matplotlib_enabled = False

    def onBufferActivated(self, args):
        bufferID = args["bufferID"]
        if bufferID in self.bufferMarkerAction:
            iMarker = self.bufferMarkerAction.pop(bufferID)
            self.changeMarkers(iMarker, bufferID)
        if self.lexer:
            self.lexer.on_bufferactivated(args)

    def onTimerMiddleButton(self):
        middleButton = windll.user32.GetKeyState(VK_MBUTTON)
        if self.middleButton != middleButton and (middleButton - (middleButton & 1)) != 0:
            x,y = GetCursorPos()
            hFore = windll.user32.GetForegroundWindow()
            hPoint = windll.user32.WindowFromPoint(x,y)
            if hPoint == hFore:
                hPoint = windll.user32.ChildWindowFromPoint(hFore, x,y)
            hSelf = self.windowHandle
            x0,y0,x1,y1 = GetWindowRect(hPoint)
            if x0 <= x <= x1 and y0 <= y <= y1 and hSelf == hFore:
                editor.grabFocus()
                pos = editor.positionFromPoint(x-x0, y-y0)
                iLineClick = editor.lineFromPosition(pos)
                iStart = editor.getSelectionStart()
                iEnd = editor.getSelectionEnd()
                iLineStart = editor.lineFromPosition(iStart)
                iLineEnd = editor.lineFromPosition(iEnd)
                if iStart != iEnd and iLineStart <= iLineClick <= iLineEnd:
                    self.runCodeAtCursor(moveCursor=False, onlyInsideCodeLines=True)
                elif 0 <= pos < editor.getLength():
                    self.runCodeAtCursor(moveCursor=False, nonSelectedLine=iLineClick, onlyInsideCodeLines=True)
        self.middleButton = middleButton
        threading.Timer(self.tTimerMiddleButton, self.onTimerMiddleButton).start()

    def onTimerFlush(self):
        #if not self.interp.active():
        try:
            r = self.interp.flush()
            if r is not None: 
                err, result = r
                if result:
                    self.outBuffer(result)
        except:
            pass
        threading.Timer(self.tTimerFlush, self.onTimerFlush).start()

    def textModified(self, args):
        '''When the marked text is modified the execution markers
        will be hidden, except when the code is still running.'''
        if args['text'] != '':
            bufferID = notepad.getCurrentBufferID()
            if self.markers.get(bufferID, None) is not None and not self.bufferActive and len(self.markers[bufferID]) > 0:
                iCurrentLine = editor.lineFromPosition(editor.getCurrentPos())
                iLines = []
                for i in self.markers[bufferID]:
                    iLine = editor.markerLineFromHandle(i)
                    iLines.append(iLine)
                if min(iLines) <= iCurrentLine <= max(iLines):
                    self.hideMarkers(bufferID)
            if self.markers.get(bufferID, None) is not None and self.bufferActive and len(self.markers[bufferID]) > 0:
                iCurrentLine = editor.lineFromPosition(editor.getCurrentPos())
                iLines = []
                for i in self.markers[bufferID]:
                    iLine = editor.markerLineFromHandle(i)
                    iLines.append(iLine)
                if len(iLines) > 0 and min(iLines) <= iCurrentLine <= max(iLines):
                    self.setMarkers(min(iLines), max(iLines), iMarker=self.m_active, bufferID=bufferID, startAnimation=False)

    def runCodeAtCursor(self, moveCursor=True, nonSelectedLine=None, onlyInsideCodeLines=False):
        '''Executes the smallest possible code element for
        the current selection. Or execute one marked cell.'''
        if not self.bufferActive:
            self.thread = threading.Thread(target=self.runThread, args=(moveCursor, nonSelectedLine, onlyInsideCodeLines))
            self.thread.start()

    def runThread(self, moveCursor=True, nonSelectedLine=None, onlyInsideCodeLines=False):
        '''Executes the smallest possible code element for
        the current selection. Or execute one marked cell.'''

        bufferID = notepad.getCurrentBufferID()
        self.bufferActive = bufferID
        lang = notepad.getLangType()
        filename = notepad.getCurrentFilename()
        if lang == Npp.LANGTYPE.TXT and '.' not in os.path.basename(filename):
            notepad.setLangType(Npp.LANGTYPE.PYTHON)
        elif lang != Npp.LANGTYPE.PYTHON:
            self.bufferActive = 0
            return

        if nonSelectedLine is None:
            iSelStart = editor.getSelectionStart()
            iSelEnd = editor.getSelectionEnd()
            iPos = editor.getCurrentPos()
            iLineCursor = iLineStart = editor.lineFromPosition(iSelStart)
            iLineEnd = max(iLineStart, editor.lineFromPosition(iSelEnd-1))
        else:
            iLineCursor = iLineStart = iLineEnd = nonSelectedLine
            iSelStart = iSelEnd = 0
        selection = iSelStart != iSelEnd
        startLine = editor.getLine(iLineStart).rstrip()
        cellMode = not selection and (startLine.startswith('#%%') or startLine.startswith('# %%'))
        err = None
        if not cellMode:
            getLineEnd = self.completeBlockEnd(iLineStart, iLineMin=iLineEnd, iLineMax=editor.getLineCount()-1)
            iFirstCodeLine, iLineEnd, isEmpty, inspectLineBefore = next(getLineEnd)
            if not inspectLineBefore and iFirstCodeLine:
                iLineStart = iFirstCodeLine
            if isEmpty:
                self.hideMarkers(bufferID)
                self.bufferActive = 0
                return
            iLineStart = self.completeBlockStart(iLineStart, inspectLineBefore)

            requireMore = True

        iStart = editor.positionFromLine(iLineStart)
        iDocEnd = editor.getLength()

        if cellMode:
            iMatch = []
            editor.research('^# ?%%(.*)$', lambda m: iMatch.append(m.span(0)[0]-1), 0, iStart+4, iDocEnd-1, 1)
            iEnd = iMatch[0] if len(iMatch) else iDocEnd
            iLineEnd = editor.lineFromPosition(iEnd)
            block = editor.getTextRange(iStart, iEnd).rstrip()
            r = self.interp.tryCode(iLineStart, filename, block)
            if r is None:
                self.hideMarkers(bufferID)
                self.bufferActive = 0
                return
            err, requireMore, isValue = r
            if requireMore:
                err = True

        else:
            # add more lines until the parser is happy or finds
            # a syntax error

            while requireMore:
                iEnd = editor.getLineEndPosition(iLineEnd)
                block = editor.getTextRange(iStart, iEnd).rstrip()
                if block:
                    res = self.interp.tryCode(iLineStart, filename, block)
                    if res is None:
                        self.bufferActive = 0
                        return
                    else:
                        err, requireMore, isValue = res
                else: err, requireMore, isValue = None, True, False
                if requireMore:
                    nextLine = next(getLineEnd, None)
                    if nextLine is None:
                        self.bufferActive = 0
                        iEnd = editor.getLength()
                        block = editor.getTextRange(iStart, iEnd).rstrip()
                        err, buff = self.interp.execute(block,iLineStart,filename)
                        self.outBuffer(buff)
                        self.setMarkers(iLineStart, iLineEnd, block, iMarker=self.m_error, bufferID=bufferID)
                        return
                    iCodeLineStart, iLineEnd, isEmpty, inspectLineBefore = nextLine
                        
        if onlyInsideCodeLines and not selection and not iLineStart <= iLineCursor <= iLineEnd:
            self.hideMarkers()
            self.bufferActive = 0
            return

        if self.activeCalltip:
            editor.callTipCancel()
            self.activeCalltip = None

        self.setMarkers(iLineStart, iLineEnd, block, iMarker=(self.m_active if not err else self.m_error), bufferID=bufferID)

        if err is not None:
            if moveCursor:
                editor.setSelectionStart(iStart)
                editor.scrollRange(iEnd, iStart)
            if err is not True: self.outBuffer(err)

        else:

            # Check if correct path is set
            if self.lastActiveBufferID != bufferID and '.' in os.path.basename(filename):
                filePath = os.path.normpath(os.path.split(filename)[0])
                self.interp.execute('os.chdir('+repr(filePath)+')')
                self.lastActiveBufferID = bufferID

            # Start a thread to execute the code
            if moveCursor:
                iNewPos = max(iPos, editor.positionFromLine(iLineEnd + 1))
                editor.setSelectionStart(iNewPos)
                editor.setCurrentPos(iNewPos)
                if iNewPos >= iDocEnd and iLineEnd == editor.getLineCount()-1:
                    editor.newLine()
                editor.scrollCaret()

            if self.matplotlib_eventHandler and not self.matplotlib_enabled:
                if 'matplotlib' in block:
                    self.interp.execute(init_matplotlib_eventHandler)
                    self.matplotlib_enabled = True

            if isValue:
                res = self.interp.evaluate()
                if res is not None:
                    err, result = res
                    if not err:
                        if self.bufferActive:
                            self.changeMarkers(iMarker=self.m_finish, bufferID=bufferID)
                        if result: self.stdout(result+'\n')
                    else:
                        self.changeMarkers(iMarker=self.m_error, bufferID=bufferID)
                        self.outBuffer(result)

            else:
                res = self.interp.execute()
                if res is not None:
                    err, result = res
                    if not err and self.bufferActive:
                        self.changeMarkers(iMarker=self.m_finish, bufferID=bufferID)
                    else:
                        self.changeMarkers(iMarker=self.m_error, bufferID=bufferID)
                    self.outBuffer(result)

        if err:
            self.changeMarkers(iMarker=self.m_error, bufferID=bufferID)

        self.bufferActive = 0

    def getUncompleteLine(self, iPos):
        '''get the whole expression with the context of a
        variable that is required to evaluate the variable'''
        iLine = editor.lineFromPosition(iPos)
        iStart = editor.positionFromLine(iLine)
        linePart = editor.getTextRange(iStart, iPos - 1)
        return linePart

    def completeBlockStart(self, iLine, inspectLineBefore):
        '''Add preceding lines that are required to execute
        the selected code, e.g. the beginning of an indented
        code block.'''
        iFirstCodeLine = iLine
        satisfied = False
        while iLine >= 0:
            line = editor.getLine(iLine).rstrip()
            isCodeLine = len(line) > 0 and not line.lstrip().startswith('#')
            isDecorator = line.startswith('@')
            if satisfied and not isDecorator:
                break
            isIndent = isCodeLine and (line.startswith(' ') or line.startswith('\t'))
            requireLineBefore = isIndent or line.startswith('else:') or line.startswith('elif') \
                    or line.startswith('except:') or line.startswith('finally:')
            inspectLineBefore = line.startswith('def ') or inspectLineBefore or requireLineBefore 
            satisfied = isCodeLine and not (requireLineBefore or inspectLineBefore)
            satisfied = satisfied or not (requireLineBefore or isCodeLine or inspectLineBefore)
            if isDecorator:
                satisfied = False
            if satisfied:
                break
            if isCodeLine:
                iFirstCodeLine = iLine
                if not (requireLineBefore or isIndent):
                    inspectLineBefore = False
                    satisfied = True
            iLine -= 1
        return max(0, iFirstCodeLine)

    def completeBlockEnd(self, iLine, iLineMin, iLineMax, isEmpty=True, inspectLineBefore=False):
        '''Add following lines that are required to execute
        the selected code, without leaving code that cannot
        be executed seperately in the next step.'''
        iLastCodeLine = iLine
        iFirstCodeLine = None
        inspectLineAfter = False
        isFirstCodeLine = True
        while iLine <= iLineMax:
            line = editor.getLine(iLine).rstrip()
            isCodeLine = len(line) > 0 and not line.lstrip().startswith('#')
            isIndent = isCodeLine and (line.startswith(' ') or line.startswith('\t'))
            thisLineIsRequiredAndMaybeMore = line.startswith('elif') or line.startswith('except:')
            thisLineIsRequired = line.startswith('else:') or line.startswith('finally:') \
                    or thisLineIsRequiredAndMaybeMore
            mightRequireLineAfter = (thisLineIsRequiredAndMaybeMore or isFirstCodeLine and \
                (line.startswith('if ') or line.startswith('for ') or line.startswith('while ')
                    )) and not inspectLineAfter
            if thisLineIsRequired or isIndent or mightRequireLineAfter:
                inspectLineAfter = True
            if thisLineIsRequired: isCodeLine = True
            if isEmpty and isIndent: inspectLineBefore = True
            if isCodeLine:
                isEmpty = False
                if not thisLineIsRequired and not mightRequireLineAfter:
                    inspectLineAfter = False
                if iFirstCodeLine is None:
                    iFirstCodeLine = iLine
                if thisLineIsRequired or iLine <= iLineMin:
                    iLastCodeLine = iLine
            if isCodeLine and line.endswith('\\'):
                inspectLineAfter = True
            satisfied = not isIndent and isCodeLine and not inspectLineAfter
            if iLine >= iLineMin and satisfied:
                yield iFirstCodeLine, iLastCodeLine, isEmpty, inspectLineBefore
            if isCodeLine:
                iLastCodeLine = iLine
                isFirstCodeLine = False
            iLine += 1
        yield iFirstCodeLine, iLastCodeLine, isEmpty, inspectLineBefore

    def preCalculateMarkers(self):
        if self.specialMarkers is None:
            self.specialMarkers = {}
            fade = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
                255, 255, 255, 255, 255, 255, 255, 252, 246, 240, 234, 228, 223,
                217, 211, 205, 199, 193, 188, 182, 176, 170, 164, 159, 153, 147,
                141, 135, 130, 124, 118, 112, 106, 101, 95, 89, 83, 77, 71, 66,
                60, 54, 48, 42, 37, 31, 25]
            self.markerHeight = len(fade)

            # pre-calculate animated "active" marker
            animation = []
            for iCycle in range(10):
                n = len(fade)
                nh = n//2
                rgba = []
                rgba_r = []
                c1 = 110, 110, 110 # basic color
                c2 = 170, 175, 200 # second color
                for iFade,f in enumerate(fade):
                    x = min(0, -(iFade - nh))
                    a = sin(pi*(4*(x / float(n))**2 - iCycle / 10.))**2
                    rgb = ''.join([chr(int(c1[i]*(1-a)+c2[i]*a)) for i in [0,1,2]]) + chr(f)
                    rgba.append(rgb*self.markerWidth)
                    x = -min(0, (iFade - nh))
                    a = sin(pi*(4*(x / float(n))**2 + iCycle / 10.))**2
                    rgb = ''.join([chr(int(c1[i]*(1-a)+c2[i]*a)) for i in [0,1,2]])  + chr(fade[n-1-iFade])
                    rgba_r.append(rgb*self.markerWidth)
                rgb = tuple([(int(c1[i]*(1-a)+c2[i]*a)) for i in [0,1,2]])
                rgba = ''.join(rgba)
                rgba_r = ''.join(rgba_r)
                animation.append((rgb, rgba, rgba_r))
            self.specialMarkers[self.m_active] = animation

            # pre-calculate marker for "finish" and "error".
            for iMarker, c in ((self.m_finish, (255,220,0)),
                    (self.m_error, (255,100,100))):
                rgb = chr(c[0])+chr(c[1])+chr(c[2])
                rgba = ''.join([(rgb+chr(f))*self.markerWidth for f in fade])
                rgba_r = ''.join([(rgb+chr(f))*self.markerWidth for f in reversed(fade)])
                rgb = c
                self.specialMarkers[iMarker] = rgb, rgba, rgba_r

    def drawMarker(self, iMarker, cycle=0):
        # load special marker RGBA images
        if iMarker == self.m_active:
            rgb, rgba, rgba_r = self.specialMarkers[iMarker][cycle]
        else:
            rgb, rgba, rgba_r = self.specialMarkers[iMarker]

        editor.rGBAImageSetWidth(self.markerWidth)
        editor.rGBAImageSetHeight(self.markerHeight)
        editor.markerDefine(iMarker, Npp.MARKERSYMBOL.LEFTRECT)
        editor.markerSetBack(iMarker, rgb)
        editor.markerDefineRGBAImage(iMarker+1, rgba)
        editor.markerDefine(iMarker+1, Npp.MARKERSYMBOL.RGBAIMAGE)
        editor.markerDefineRGBAImage(iMarker+2, rgba_r)
        editor.markerDefine(iMarker+2, Npp.MARKERSYMBOL.RGBAIMAGE)

    def setMarkers(self, iLineStart, iLineEnd, block=None, iMarker=None, bufferID=None, startAnimation=True):
        '''Set markers at the beginning and end of the executed
        code block, to show the user which part is actually executed
        and if the code is still running or finished or if errors
        occurred.'''
        if block:
            lineHasCode = [len(line) > 0 and not (line.isspace() or line.startswith('#')) for line in block.splitlines()]
            linesWithCode = [i for i, c in enumerate(lineHasCode) if c]
            iLineEnd = iLineStart + linesWithCode[-1]
            iLineStart = iLineStart + linesWithCode[0]
        nMarkedLines = iLineEnd - iLineStart + 1
        markerIDs = []
        if bufferID is None:
            bufferID = notepad.getCurrentBufferID()
        self.hideMarkers(bufferID)
        if nMarkedLines <= 4:
            for iLine in range(nMarkedLines):
                markerIDs.append(editor.markerAdd(iLineStart+iLine, iMarker))
        else:
            markerIDs.append(editor.markerAdd(iLineStart, iMarker))
            markerIDs.append(editor.markerAdd(iLineStart+1, iMarker+1))
            markerIDs.append(editor.markerAdd(iLineEnd, iMarker))
            markerIDs.append(editor.markerAdd(iLineEnd-1, iMarker+2))
        self.markers[bufferID] = markerIDs
        if startAnimation and iMarker == self.m_active:
            self.onMarkerTimer(init=True)

    def onMarkerTimer(self, init=False):
        if self.bufferActive:
            if init:
                self.markerCycle = 0
            else:
                self.markerCycle = (self.markerCycle + 1) % 10
                self.drawMarker(self.m_active, cycle=self.markerCycle)
            self.threadMarker = threading.Timer(0.1, self.onMarkerTimer)
            self.threadMarker.start()
        else:
            self.drawMarker(self.m_active)
            self.threadMarker = None

    def changeMarkers(self, iMarker, bufferID=None):
        if bufferID != notepad.getCurrentBufferID():
            self.bufferMarkerAction[bufferID] = iMarker
            return
        iLines = []
        for i in self.markers[bufferID]:
            iLine = editor.markerLineFromHandle(i)
            #if iLine == -1:
            #    notepad.activateBufferID(bufferID)
            #    iLine = editor.markerLineFromHandle(i)
            iLines.append(iLine)
        if iLines:
            self.setMarkers(min(iLines), max(iLines), iMarker=iMarker, bufferID=bufferID)

    def hideMarkers(self, bufferID=None):
        '''Hide all markers of the current buffer ID.'''
        if bufferID is None: bufferID = notepad.getCurrentBufferID()
        markers = self.markers.get(bufferID,[])
        while markers:
            editor.markerDeleteHandle(markers.pop())

    def stdout(self, s):
        console.editor.beginUndoAction()
        console.write(s)
        console.editor.endUndoAction()
        console.editor.setReadOnly(0)

    def stderr(self, s):
        console.editor.beginUndoAction()
        console.writeError(s)
        console.editor.endUndoAction()
        console.editor.setReadOnly(0)

    def outBuffer(self, buffer):
        console.editor.beginUndoAction()
        out = []
        mode = True
        for err, line in buffer:
            if err:
                console.writeError(line)
            else: console.write(line)
        console.editor.endUndoAction()
        console.editor.setReadOnly(0)

    def onMouseDwell(self, args):
        '''Show a call tip window about the current content
        of a selected variable'''
        #if self.bufferActive or self.interp.active(): return
        #if editor.callTipActive(): return
        pos = editor.positionFromPoint(args['x'], args['y'])
        self.showCalltip(pos)

    def showCalltip(self, pos=None):
        iStart = editor.getSelectionStart()
        iEnd = editor.getSelectionEnd()
        if pos is None:
            pos = editor.getCurrentPos()
            CT_unselected = False
            CT_expression = False
        else:
            CT_unselected = self.popupForUnselectedVariable
            CT_expression = self.popupForSelectedExpression
        if iEnd != iStart and iStart <= pos <= iEnd:
            if CT_expression and iEnd - iStart > 1:
                expression = editor.getTextRange(iStart, iEnd)
                if expression =='False':
                    self.activeCalltip = False
                    editor.callTipShow(iStart, 'set to True')
                elif expression =='True':
                    self.activeCalltip = True
                    editor.callTipShow(iStart, 'set to False')
                elif not '\n' in expression:
                    ret = self.interp.getCallTip(None, expression)
                    if ret and (CT_unselected or ret[-1] != 'value error'):
                        element, nHighlight, calltip = ret
                        self.activeCalltip = 'doc'
                        editor.callTipShow(iStart, ''.join(calltip))
                        editor.callTipSetHlt(0, int(nHighlight))
            else:
                iLineStart = editor.positionFromLine(editor.lineFromPosition(iStart))
                var = editor.getTextRange(iStart, iEnd)
                line = editor.getTextRange(iLineStart, iEnd)
                if var == '.':
                    autoCompleteList = self.interp.autoCompleteObject(self.getUncompleteLine(iStart+1))
                    if autoCompleteList:
                        editor.autoCSetSeparator(ord('\t'))
                        editor.autoCSetIgnoreCase(False)
                        editor.autoCSetCaseInsensitiveBehaviour(False)
                        editor.autoCSetOrder(0)
                        editor.autoCSetDropRestOfWord(True)
                        editor.autoCShow(0, autoCompleteList)
                else:
                    ret = self.interp.getCallTip(line, var)
                    if ret:
                        element, nHighlight, calltip = ret
                        if element == var =='False':
                            self.activeCalltip = False
                            editor.callTipShow(iStart, 'set to True')
                        elif element == var =='True':
                            self.activeCalltip = True
                            editor.callTipShow(iStart, 'set to False')
                        elif ret[-1] != 'value error':
                            self.activeCalltip = 'doc'
                            editor.callTipShow(iStart, ''.join(calltip))
                            editor.callTipSetHlt(0, int(nHighlight))
        elif CT_unselected and iStart == iEnd and pos >= 0:
            iLine = editor.lineFromPosition(pos)
            line = editor.getLine(iLine)
            iLineStart = editor.positionFromLine(iLine)
            posInLine = pos - iLineStart
            iWordEnd=0
            for iWordStart in range(posInLine, -1, -1):
                s = line[iWordStart]
                if not ('a' <= s <= 'z' or 'A' <= s <= 'Z' or '0' <= s <= '9' or s == '_'):
                    iWordStart += 1
                    break
            if iWordStart <= posInLine:
                for iWordEnd in range(posInLine+1, len(line)):
                    s = line[iWordEnd]
                    if not ('a' <= s <= 'z' or 'A' <= s <= 'Z' or '0' <= s <= '9' or s == '_'):
                        iWordEnd -= 1
                        break
            var = line[iWordStart:iWordEnd+1]
            if var:
                var = line[iWordStart:iWordEnd+1]
                ret = self.interp.getCallTip(line[0:iWordEnd+1], var)
                pos = iLineStart + iWordStart
                if ret:
                    element, nHighlight, calltip = ret
                    if calltip != 'value error':
                        self.activeCalltip = 'doc'
                        editor.callTipShow(pos, ''.join(calltip))
                        editor.callTipSetHlt(0, int(nHighlight))


    def onCalltipClick(self, args):
        '''When clicked on the calltip write the full calltip in the output console.'''
        if self.activeCalltip == 'doc':# and args['position']==0:
            var, calltip = self.interp.getFullCallTip()
            head = '='*(40 - len(var)//2 - 3) + ' Info: ' + var + ' ' + '='*(40 - len(var)//2 - 3)
            foot = '='*len(head)
            self.stdout('\n' + head + '\n' + ''.join(calltip) + '\n' + foot + '\n')
        elif self.activeCalltip == True:
            editor.replaceSel('False')
        elif self.activeCalltip == False:
            editor.replaceSel('True')
        editor.callTipCancel()
        self.activeCalltip = None

    def onAutocomplete(self, args):
        '''Check if auto complete data can be added and displayed:
        "." after objects: show auto completion list with properties and methods
        "[" after dict: show auto completion list with keys
        "(" after functions: insert template and display a call tip with the doc string.'''
        if args['ch'] == 46 and args['code'] == 2001: # character "."
            iPos = editor.getCurrentPos()
            autoCompleteList = self.interp.autoCompleteObject(self.getUncompleteLine(iPos))
            if autoCompleteList is None: return
            if autoCompleteList:
                editor.autoCSetSeparator(ord('\t'))
                editor.autoCSetIgnoreCase(False)
                editor.autoCSetCaseInsensitiveBehaviour(False)
                editor.autoCSetOrder(2)
                editor.autoCSetDropRestOfWord(True)
                editor.autoCShow(0, autoCompleteList)
        elif args['ch'] == 40 and args['code'] == 2001: # character "("
            iPos = editor.getCurrentPos()
            r = self.interp.autoCompleteFunction(self.getUncompleteLine(iPos))
            if r is None: return
            n, funcParam, callTip = r
            if callTip:
                editor.callTipShow(max(0,iPos-n), callTip)
                editor.callTipSetHlt(0, max(0, callTip.find('\n')))
                self.activeCalltip = 'doc'
            if funcParam and iPos == editor.getCurrentPos():
                editor.insertText(iPos,funcParam+')')
                editor.setSelectionStart(iPos)
                editor.setSelectionStart(iPos + len(funcParam) + 1)
                editor.setCurrentPos(iPos)
        elif args['ch'] == 91 and args['code'] == 2001: # character "["
            iPos = editor.getCurrentPos()
            autoCompleteList = self.interp.autoCompleteDict(self.getUncompleteLine(iPos))
            if autoCompleteList:
                editor.autoCSetSeparator(ord('\t'))
                editor.autoCSetIgnoreCase(False)
                editor.autoCSetCaseInsensitiveBehaviour(False)
                editor.autoCSetOrder(0)
                editor.autoCSetDropRestOfWord(True)
                editor.autoCShow(0, autoCompleteList)


# lexer for special comments "#%%" for block execution
class EnhancedPythonLexer(object):
    def __init__(self):
        self.__is_lexer_doc = False
        self.get_lexer_name = lambda: notepad.getLanguageName(notepad.getLangType())
        self.indicator = 0

    @staticmethod
    def paint_it(indicator, pos, length):
        current_line = editor.lineFromPosition(pos)
        editor.setIndicatorCurrent(indicator)
        editor.indicatorFillRange(pos,length)

    def style(self):
        line_number = editor.getFirstVisibleLine()
        start_position = editor.positionFromLine(line_number)
        end_position = editor.getLineEndPosition(line_number + editor.linesOnScreen())
        editor.setIndicatorCurrent(self.indicator)
        editor.indicatorClearRange(start_position, end_position-start_position)

        flag = 0
        editor.research('^# ?%%(.*)$', lambda m: self.paint_it(self.indicator, m.span(flag)[0],
                m.span(flag)[1] - m.span(flag)[0]), 0, start_position, end_position)

    def set_lexer_doc(self,bool_value):
        editor.setProperty(self.__class__.__name__, 1 if bool_value is True else -1)
        self.__is_lexer_doc = bool_value

    def on_bufferactivated(self,args):
        if (self.get_lexer_name() == self.lexer_name):# and (editor.getPropertyInt(self.__class__.__name__) != -1):
            self.__is_lexer_doc = True
        else:
            self.__is_lexer_doc = False

    def on_updateui(self,args):
        if self.__is_lexer_doc:
            self.style()

    def on_langchanged(self,args):
        self.set_lexer_doc(True if self.get_lexer_name() == self.lexer_name else False)

    def main(self):
        self.lexer_name = 'Python'
        editor.indicSetFore(self.indicator, (80, 160, 120))
        editor.indicSetStyle(self.indicator, Npp.INDICATORSTYLE.COMPOSITIONTHICK)
        self.set_lexer_doc(True)
        self.style()
