# PyPadPlusPlus: A Notepad++ plugin for interactive Python development,
# based on the Python Script plugin

__author__ = "Christian Schirm"
__copyright__ = "Copyright 2018"
__license__ = "GPLv3"
__version__ = "0.3"

import Npp
from Npp import editor, console, notepad
import code, sys, time, os
from codeop import compile_command
import introspect  # Module for code introspection from the wxPython project
import traceback
import threading
import textwrap
import pyPadHost
import pyPadClient
import win32api, win32con, win32gui

class pyPad:
    def __init__(self, externalPython=None):
        '''Initializes PyPadPlusPlus to prepare Notepad++
        for interactive Python development'''
        console.show()

        # EnhancedPythonLexer().main()

        self.thread = None
        self.lock = True
        self.holdMarker = False
        self.activeCalltip = None
        editor.grabFocus()
        editor.setTargetStart(0)
        if externalPython:
            self.interp = pyPadHost.interpreter()
        else:
            self.interp = pyPadClient.interpreter()

		# Marker margin
        self.markerWidth = 3
        self.markers = None
        self.hideMarkers()
        editor.markerDefine(8, Npp.MARKERSYMBOL.LEFTRECT)
        editor.markerDefine(7, Npp.MARKERSYMBOL.RGBAIMAGE)
        editor.markerDefine(6, Npp.MARKERSYMBOL.RGBAIMAGE)
        editor.setMarginWidthN(3, self.markerWidth)
        editor.setMarginMaskN(3, 256+128+64)

        self.fade = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
            255, 255, 255, 255, 255, 255, 255, 252, 246, 240, 234, 228, 223,
            217, 211, 205, 199, 193, 188, 182, 176, 170, 164, 159, 153, 147,
            141, 135, 130, 124, 118, 112, 106, 101, 95, 89, 83, 77, 71, 66,
            60, 54, 48, 42, 37, 31, 25]

        editor.setMouseDwellTime(300)
        editor.clearCallbacks([Npp.SCINTILLANOTIFICATION.CALLTIPCLICK])
        editor.callback(self.onCalltipClick, [Npp.SCINTILLANOTIFICATION.CALLTIPCLICK])
        editor.clearCallbacks([Npp.SCINTILLANOTIFICATION.CHARADDED])
        editor.callback(self.onAutocomplete, [Npp.SCINTILLANOTIFICATION.CHARADDED])
        editor.clearCallbacks([Npp.SCINTILLANOTIFICATION.DWELLSTART])
        editor.callback(self.onMouseDwell, [Npp.SCINTILLANOTIFICATION.DWELLSTART])
        editor.clearCallbacks([Npp.SCINTILLANOTIFICATION.MODIFIED])
        editor.callback(self.textModified, [Npp.SCINTILLANOTIFICATION.MODIFIED])

        editor.callTipSetBack((255,255,225))
        editor.autoCSetSeparator(ord('\t'))
        editor.autoCSetIgnoreCase(False)
        editor.autoCSetCaseInsensitiveBehaviour(False)
        editor.autoCSetCancelAtStart(False)
        editor.autoCSetDropRestOfWord(True)

        console.clear()
        console.editor.setReadOnly(0)

        self.timer = False
        self.timerCount = 0
        self.middleButton = 0

        filename = notepad.getCurrentFilename()
        path = os.path.split(filename)[0]
        self.interp.tryCode(0, 'none', 'import os; os.chdir("'+path+'")')
        self.lock = False

    def __del__(self):
        '''Clear call backs on exit.'''
        editor.clearCallbacks([Npp.SCINTILLANOTIFICATION.CALLTIPCLICK])
        editor.clearCallbacks([Npp.SCINTILLANOTIFICATION.CHARADDED])
        editor.clearCallbacks([Npp.SCINTILLANOTIFICATION.DWELLSTART])
        editor.clearCallbacks([Npp.SCINTILLANOTIFICATION.MODIFIED])

    def onTimer(self):
        self.timer = True
        self.timerCount += 1
        middleButton = win32api.GetKeyState(win32con.VK_MBUTTON)
        if middleButton < 0 and self.middleButton >= 0:
            x,y = win32api.GetCursorPos()
            hwnd = win32gui.WindowFromPoint((x,y))
            x0,y0,x1,y1 = win32gui.GetWindowRect(hwnd)
            if x0 <= x <= x1 and y0 <= y <= y1 and win32gui.GetParent(hwnd) == win32gui.GetForegroundWindow():
                p = editor.positionFromPoint(x-x0, y-y0)
                iStart = editor.getSelectionStart()
                iEnd = editor.getSelectionEnd()
                if iStart != iEnd and iStart <= p <= iEnd:
                    self.execute(moveCursor=False)
                elif 0 <= p < editor.getLength():
                    editor.setSelectionStart(p)
                    editor.setSelectionEnd(p)
                    self.execute(moveCursor=False)

        self.middleButton = middleButton
        if self.timerCount > 10:
            if not self.lock:
                err, result = self.interp.flush()
                if result:
                    self.outBuffer(result)
        threading.Timer(0.02, self.onTimer).start()

    def execute(self, moveCursor=True):
        '''Executes the smallest possible code element for
        the current selection. Or execute one marked block.'''
        if self.lock: return
        iPos = editor.getCurrentPos()
        iLineStart = editor.lineFromPosition(editor.getSelectionStart())
        iLineEnd = max(iLineStart, editor.lineFromPosition(editor.getSelectionEnd()-1))
        iLineStart, iStart = self.completeBlockStart(iLineStart)
        getEnd = self.completeBlockEnd(iLineEnd)
        requireMore = True
        iEnd = next(getEnd)
        if iEnd == -1:
            self.hideMarkers()
            return
        iDocEnd = editor.getLength()-1
        filename = notepad.getCurrentFilename()
        lang = notepad.getLangType()
        if lang == Npp.LANGTYPE.TXT and '.' not in filename:
            notepad.setLangType(Npp.LANGTYPE.PYTHON)
        elif lang != Npp.LANGTYPE.PYTHON: return

        err = None

        line = editor.getTextRange(iStart, iStart + 4)
        if line.startswith('#%%') or line.startswith('# %%'):
            iMatch = []
            editor.research('^# ?%%(.*)$', lambda m: iMatch.append(m.span(0)[0]-1), 0, iStart+3, iDocEnd, 1)
            iEnd = iMatch[0] if len(iMatch) else iDocEnd
            block = editor.getTextRange(iStart, iEnd).rstrip()
            err, requireMore, isValue = self.interp.tryCode(iLineStart, filename, block)
            if requireMore:
                self.hideMarkers()
                return

        else:
            # add more lines until the parser is happy or finds
            # a syntax error
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
            self.outBuffer(err)

        else:

            # Start a thread to execute the code

            iNewPos = max(iPos, editor.positionFromLine(iLineEnd + 1))
            if moveCursor:
                editor.setSelectionStart(iNewPos)
                editor.setCurrentPos(iNewPos)
                if iNewPos > iDocEnd and iLineEnd == editor.getLineCount()-1:
                    print iNewPos, iDocEnd, iLineEnd,  editor.getLineCount(), editor.positionFromLine(iLineEnd), editor.positionFromLine(iLineEnd + 1)
                    editor.newLine()
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
            self.lock = False

        if not self.timer:
            self.onTimer()  # start periodic timer to check output of process

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
        return max(0, iLine), iStart

    def completeBlockEnd(self, iLine):
        '''Add following lines that are required to execute
        the selected code, without leaving code that cannot
        be executed seperately in the next step.'''
        n = editor.getLineCount()
        hasCode = False
        #print "iLine=",iLine
        while iLine < n:
            iStartTest = editor.positionFromLine(iLine)
            iEndTest = editor.getLineEndPosition(iLine)
            lineTest = editor.getTextRange(iStartTest, iEndTest).rstrip()
            isCodeLine = len(lineTest) > 0 and not lineTest.startswith('#')
            lineBelongsToBlock = len(lineTest)==0 or lineTest.startswith(' ') \
                    or lineTest.startswith('\t') or lineTest.startswith('else:') \
                    or lineTest.startswith('elif') or lineTest.startswith('except:') \
                    or lineTest.startswith('finally:')
            if isCodeLine:
                hasCode = True
            if not lineBelongsToBlock and isCodeLine:
                yield iEndTest
            iLine += 1
        #print "iLineEnd=",iLine
        yield iEndTest if hasCode else -1

    def threadValue(self):
        '''Thread of the running code in case the code is
        a value. When finished, the execution markers are
        set to the corresponding color.'''
        err, result = self.interp.evaluate()
        if not err:
            self.setMarkers(color='f')
            if result: self.stdout(result+'\n')
        else:
            self.setMarkers(color='r')
            self.outBuffer(result)
        self.lock = False

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
        self.outBuffer(result)
        self.lock = False

        # wait some seconds until the markers can hide
        time.sleep(3)
        self.holdMarker = False

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
        for err, line in buffer:
            if err: console.writeError(line)
            else: console.write(line)
        console.editor.endUndoAction()
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
        if block or color is None:
            self.hideMarkers()
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
                self.hideMarkers()
                self.markers = id

    def hideMarkers(self):
        editor.markerDeleteAll(6)
        editor.markerDeleteAll(7)
        editor.markerDeleteAll(8)

    def onCalltipClick(self, args):
        if self.activeCalltip == 'doc':# and args['position']==0:
            #self.stdout(str(args))
            var, calltip = self.interp.getFullCallTip()
            #if len(var) > 50: var = var[:50] + '...'
            head = '='*(40 - len(var)//2 - 3) + ' Calltip: ' + var + ' ' + '='*(40 - len(var)//2 - 3)
            foot = '='*len(head)
            self.stdout('\n' + head + '\n' + ''.join(calltip) + '\n' + foot + '\n')
        elif self.activeCalltip == True:
            editor.replaceSel('False')
        elif self.activeCalltip == False:
            editor.replaceSel('True')
        editor.callTipCancel()
        self.activeCalltip = None

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
                    element, nHighlight, calltip = self.interp.getCallTip(line, var)
                    if element == var =='False':
                        self.activeCalltip = False
                        editor.callTipShow(iStart, 'set to True')
                    elif element == var =='True':
                        self.activeCalltip = True
                        editor.callTipShow(iStart, 'set to False')
                    else:
                        self.activeCalltip = 'doc'
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
                editor.autoCSetIgnoreCase(False)
                editor.autoCSetCaseInsensitiveBehaviour(False)
                editor.autoCSetOrder(0)
                editor.autoCSetDropRestOfWord(True)
                editor.autoCShow(0, autoCompleteList)
        elif args['ch'] == 40 and args['code'] == 2001: # character "("
            iPos = editor.getCurrentPos()
            n, funcParam, callTip = self.interp.autoCompleteFunction(self.getUncompleteLine(iPos))
            if callTip:
                editor.callTipShow(max(0,iPos-n), callTip)
                editor.callTipSetHlt(0, max(0, callTip.find('\n')))
                self.activeCalltip = 'doc'
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
                editor.autoCSetIgnoreCase(False)
                editor.autoCSetCaseInsensitiveBehaviour(False)
                editor.autoCSetOrder(0)
                editor.autoCSetDropRestOfWord(True)
                editor.autoCShow(0, autoCompleteList)


# lexer for special comments "# %%" for block execution

# ensure that only a single instance is used to prevent getting
# multiple callbacks executed
class SingletonEnhancedPythonLexer(type):
    _instance = None
    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SingletonEnhancedPythonLexer, cls).__call__(*args, **kwargs)
        return cls._instance

# main class
class EnhancedPythonLexer(object):

    __metaclass__ = SingletonEnhancedPythonLexer

    def __init__(self):
        editor.callbackSync(self.on_updateui, [Npp.SCINTILLANOTIFICATION.UPDATEUI])
        notepad.callback(self.on_langchanged, [Npp.NOTIFICATION.LANGCHANGED])
        notepad.callback(self.on_bufferactivated, [Npp.NOTIFICATION.BUFFERACTIVATED])
        self.__is_lexer_doc = False
        self.get_lexer_name = lambda: notepad.getLanguageName(notepad.getLangType())

    @staticmethod
    def paint_it(indicator, pos, length):
        current_line = editor.lineFromPosition(pos)
        line_start_position = editor.positionFromLine(current_line)
        editor.setIndicatorCurrent(indicator)
        editor.indicatorFillRange(pos,length)

    def style(self):
        line_number = editor.getFirstVisibleLine()
        start_position = editor.positionFromLine(line_number)
        end_position = editor.getLineEndPosition(line_number + editor.linesOnScreen())
        editor.setIndicatorCurrent(0)
        editor.indicatorClearRange(start_position, end_position-start_position)
        indicator = 0
        flag = 0
        editor.research('^# ?%%(.*)$', lambda m: self.paint_it(indicator, m.span(flag)[0],
                m.span(flag)[1] - m.span(flag)[0]), 0, start_position, end_position)

    def set_lexer_doc(self,bool_value):
        editor.setProperty(self.__class__.__name__, 1 if bool_value is True else -1)
        self.__is_lexer_doc = bool_value

    def on_bufferactivated(self,args):
        if (self.get_lexer_name() == self.lexer_name) and (editor.getPropertyInt(self.__class__.__name__) != -1):
            self.__is_lexer_doc = True
        else:
            self.__is_lexer_doc = False

    def on_updateui(self,args):
        if self.__is_lexer_doc:
            self.style()

    def on_langchanged(self,args):
        self.set_lexer_doc(True if self.get_lexer_name() == self.lexer_name else False)

    # customize, if needed
    def main(self):
        # basically what is returned by notepad.getLanguageName(notepad.getLangType())
        self.lexer_name = 'Python'
        indicator = 0
        editor.indicSetFore(indicator, (80, 160, 120))
        editor.indicSetStyle(indicator, Npp.INDICATORSTYLE.COMPOSITIONTHICK)
        #editor.indicSetStyle(indicator, INDICATORSTYLE.ROUNDBOX)

        self.set_lexer_doc(True)
        self.style()
