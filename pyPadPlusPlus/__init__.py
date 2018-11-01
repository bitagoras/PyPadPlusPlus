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
        self.delayedMarker = False
        self.activeCalltip = None
        editor.grabFocus()
        editor.setTargetStart(0)
        
        if externalPython:
            self.interp = pyPadHost.interpreter()
        else:
            self.interp = pyPadClient.interpreter()
            
		# Marker
        self.markerWidth = 3
        editor.setMarginWidthN(3, self.markerWidth)
        editor.setMarginMaskN(3, (256+128+64) * (1 + 2**3 + 2**6))
        fade = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
            255, 255, 255, 255, 255, 255, 255, 252, 246, 240, 234, 228, 223,
            217, 211, 205, 199, 193, 188, 182, 176, 170, 164, 159, 153, 147,
            141, 135, 130, 124, 118, 112, 106, 101, 95, 89, 83, 77, 71, 66,
            60, 54, 48, 42, 37, 31, 25]
            
        self.markers = {}
        self.m_active, self.m_error, self.m_finish = [6 + 3*i for i in 0,1,2]
        for iMarker,c in ((self.m_active, (150,150,150)),
                          (self.m_error,  (255,100,100)),
                          (self.m_finish, (255,220,0))):
            rgb = chr(c[0])+chr(c[1])+chr(c[2])
            rgba = ''.join([(rgb+chr(f))*self.markerWidth for f in fade])
            rgba_r = ''.join([(rgb+chr(f))*self.markerWidth for f in reversed(fade)])
            editor.rGBAImageSetWidth(self.markerWidth)
            editor.rGBAImageSetHeight(len(fade))
            editor.markerDefine(iMarker, Npp.MARKERSYMBOL.LEFTRECT)
            editor.markerSetBack(iMarker, c)
            editor.markerDefineRGBAImage(iMarker+1, rgba)
            editor.markerDefine(iMarker+1, Npp.MARKERSYMBOL.RGBAIMAGE)
            editor.markerDefineRGBAImage(iMarker+2, rgba_r)
            editor.markerDefine(iMarker+2, Npp.MARKERSYMBOL.RGBAIMAGE)
        
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
                pos = editor.positionFromPoint(x-x0, y-y0)
                iLineClick = editor.lineFromPosition(pos)
                iLineStart = editor.lineFromPosition(editor.getSelectionStart())
                iLineEnd = editor.lineFromPosition(editor.getSelectionEnd())
                if iLineStart <= iLineClick <= iLineEnd:
                    self.execute(moveCursor=False)
                elif 0 <= pos < editor.getLength():
                    self.execute(moveCursor=False, singleLine=iLineClick)

        self.middleButton = middleButton
        if self.timerCount > 10:
            if not self.lock:
                err, result = self.interp.flush()
                if result:
                    self.outBuffer(result)
        threading.Timer(0.02, self.onTimer).start()

    def execute(self, moveCursor=True, singleLine=None):
        '''Executes the smallest possible code element for
        the current selection. Or execute one marked block.'''
        if self.lock: return
        iSelStart = editor.getSelectionStart()
        iSelEnd = editor.getSelectionEnd()
        selection = iSelStart != iSelEnd
        if singleLine is None:
            iPos = editor.getCurrentPos()
            iLineStart = editor.lineFromPosition(iSelStart)
            iLineEnd = max(iLineStart, editor.lineFromPosition(iSelEnd-1))
        else:
            iLineStart = iLineEnd = singleLine
        getLineEnd = self.completeBlockEnd(iLineStart, iLineMin=iLineEnd, iLineMax=editor.getLineCount()-1)
        iLineEnd, isEmpty, expectMoreLinesBefore = next(getLineEnd)
        if isEmpty:
            self.hideMarkers()
            return
        iLineStart = self.completeBlockStart(iLineStart, expectMoreLinesBefore)
            
        requireMore = True
        filename = notepad.getCurrentFilename()
        lang = notepad.getLangType()
        if lang == Npp.LANGTYPE.TXT and '.' not in filename:
            notepad.setLangType(Npp.LANGTYPE.PYTHON)
        elif lang != Npp.LANGTYPE.PYTHON: return

        err = None

        iStart = editor.positionFromLine(iLineStart)
        iDocEnd = editor.getLength()
        
        line = editor.getLine(iLineStart).rstrip()
        if not selection and (line.startswith('#%%') or line.startswith('# %%')):
            iMatch = []
            editor.research('^# ?%%(.*)$', lambda m: iMatch.append(m.span(0)[0]-1), 0, iStart+4, iDocEnd-1, 1)
            iEnd = iMatch[0]-1 if len(iMatch) else iDocEnd
            iLineEnd = editor.lineFromPosition(iEnd)
            block = editor.getTextRange(iStart, iEnd).rstrip()
            err, requireMore, isValue = self.interp.tryCode(iLineStart, filename, block)
            if requireMore:
                self.hideMarkers()
                return

        else:
            # add more lines until the parser is happy or finds
            # a syntax error
            while requireMore:
                iEnd = editor.getLineEndPosition(iLineEnd)
                block = editor.getTextRange(iStart, iEnd).rstrip()
                err, requireMore, isValue = self.interp.tryCode(iLineStart, filename, block)
                if requireMore:
                    iLineEnd, isEmpty, expectMoreLinesBefore = next(getLineEnd, -1)
                    if iEnd == -1:
                        iLineEnd = iLineStart
                        break

        self.setMarkers((iLineStart, iLineEnd), block, iMarker=(self.m_active if not err else self.m_error))

        if err is not None:
            if moveCursor:
                editor.setSelectionStart(iPos)
                editor.scrollCaret()
            if err is not True: self.outBuffer(err)

        else:

            # Start a thread to execute the code

            if moveCursor:
                iNewPos = max(iPos, editor.positionFromLine(iLineEnd + 1))
                editor.setSelectionStart(iNewPos)
                editor.setCurrentPos(iNewPos)
                if iNewPos >= iDocEnd and iLineEnd == editor.getLineCount()-1:
                    editor.newLine()
                editor.scrollCaret()

            self.lock = True
            if isValue:
                self.thread = threading.Thread(name='threadValue', target=self.threadValue, args=())
            else:
                self.thread = threading.Thread(name='threadCode', target=self.threadCode, args=())

            if not err:
                self.thread.start()
        if err:
            self.changeMarkers(iMarker=self.m_error)
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

    def completeBlockStart(self, iLine, expectMoreLines):
        '''Add preceding lines that are required to execute
        the selected code, e.g. the beginning of an indented
        code block.'''
        iFirstCodeLine = iLine
        while iLine >= 0:
            line = editor.getLine(iLine).rstrip()
            isCodeLine = len(line) > 0 and not line.startswith('#')
            isDecorator = line.startswith('@')
            isIndent = line.startswith(' ') or line.startswith('\t')
            requireMoreLine = isIndent or line.startswith('else:') or line.startswith('elif') \
                    or line.startswith('except:') or line.startswith('finally:')
            satisfied = not requireMoreLine and not expectMoreLines and isCodeLine
            satisfied = satisfied or (not requireMoreLine and not isCodeLine and not expectMoreLines)
            if isDecorator:
                satisfied = False
            if isCodeLine:
                iFirstCodeLine = iLine
                if not isIndent: expectMoreLines = False
            if satisfied:
                break
            iLine -= 1
        return max(0, iFirstCodeLine)

    def completeBlockEnd(self, iLine, iLineMin, iLineMax, isEmpty=True, expectMoreLinesBefore=False):
        '''Add following lines that are required to execute
        the selected code, without leaving code that cannot
        be executed seperately in the next step.'''
        iLastCodeLine = iLineMin
        expectMoreLines = False
        while iLine <= iLineMax:
            line = editor.getLine(iLine).rstrip()
            isCodeLine = len(line) > 0 and not line.startswith('#')
            mightBelongToBlock = not isCodeLine
            isIndent = line.startswith(' ') or line.startswith('\t')
            requireMoreLine = line.startswith('else:') or line.startswith('elif') \
                    or line.startswith('except:') or line.startswith('finally:') \
                    or line.startswith('@')
            if requireMoreLine or isIndent: expectMoreLines = True
            if isEmpty and isIndent: expectMoreLinesBefore = True
            if isCodeLine: isEmpty = False
            if isCodeLine and not requireMoreLine: expectMoreLines = False
            satisfied = not isIndent and isCodeLine and not expectMoreLines and not requireMoreLine
            if iLine >= iLineMin and satisfied:
                yield iLastCodeLine, isEmpty, expectMoreLinesBefore
            if isCodeLine:
                iLastCodeLine = max(iLineMin, iLine)
            iLine += 1
        yield iLastCodeLine, isEmpty, expectMoreLinesBefore

    def threadValue(self):
        '''Thread of the running code in case the code is
        a value. When finished, the execution markers are
        set to the corresponding color.'''
        err, result = self.interp.evaluate()
        if not err:
            self.changeMarkers(iMarker=self.m_finish)
            if result: self.stdout(result+'\n')
        else:
            self.changeMarkers(iMarker=self.m_error)
            self.outBuffer(result)
        self.lock = False

    def threadCode(self):
        '''Thread of the running code in case the code is
        not a value. When finished, the execution markers are
        set to the corresponding color.'''
        err, result = self.interp.execute()
        if not err:
            self.changeMarkers(iMarker=self.m_finish)
        else:
            self.changeMarkers(iMarker=self.m_error)
        self.outBuffer(result)
        self.lock = False

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

    def setMarkers(self, iRange=(0, 0), block=None, iMarker=None):
        '''Set markers at the beginning and end of the executed
        code block, to show the user which part is actually executed
        and if the code is still running or finished or if errors
        occurred.'''
        if block:
            iLineStart, iLineEnd = iRange
            lineHasCode = [len(line) > 0 and not (line.isspace() or line.startswith('#')) for line in block.splitlines()]
            linesWithCode = [i for i, c in enumerate(lineHasCode) if c]
            firstMarker = iLineStart + linesWithCode[0]
            lastMarker = iLineStart + linesWithCode[-1]
            nExtraLines = lastMarker - firstMarker + 1
            markerIDs = []
            id = notepad.getCurrentBufferID()
            self.hideMarkers(id)
            if nExtraLines <= 4:
                for iLine in range(nExtraLines):
                    markerIDs.append(editor.markerAdd(firstMarker+iLine, iMarker))
            else:
                markerIDs.append(editor.markerAdd(firstMarker, iMarker))
                markerIDs.append(editor.markerAdd(firstMarker+1, iMarker+1))
                markerIDs.append(editor.markerAdd(lastMarker-1, iMarker+2))
                markerIDs.append(editor.markerAdd(lastMarker, iMarker))
            self.markers[id] = markerIDs

    def changeMarkers(self, iMarker):
        id = notepad.getCurrentBufferID()
        markerIDs = []
        iLines = []
        markerLong = (0, 1, 2, 0)
        markerShort = (0, 0, 0, 0)
        for i in self.markers[id]:
            iLines.append(editor.markerLineFromHandle(i))
            editor.markerDeleteHandle(i)
        if iLines[-1] - iLines[0] < 4:
            markerTypes = markerShort
        else:
            markerTypes = markerLong
        for i,m in enumerate(self.markers[id]):
            markerIDs.append(editor.markerAdd(iLines[i], iMarker+markerTypes[i]))
            editor.markerDeleteHandle(m)
        self.markers[id] = markerIDs
            
    def textModified(self, args):
        '''When the text is modified the execution markers
        will be hidden, except when the code is running or
        when the color just has changed in the last few seconds.'''
        if args['text']:
            id = notepad.getCurrentBufferID()
            if self.markers.get(id, None) is not None and not self.lock and len(self.markers[id]) > 0:
                iCurrentLine = editor.lineFromPosition(editor.getCurrentPos())
                line0 = editor.markerLineFromHandle(self.markers[id][0])
                line1 = editor.markerLineFromHandle(self.markers[id][-1])
                if line0 <= iCurrentLine <= line1:
                    self.hideMarkers(id)

    def hideMarkers(self, id=None):
        if id is None: id = notepad.getCurrentBufferID()
        markers = self.markers.get(id,[])
        while markers:
            editor.markerDeleteHandle(markers.pop())

    def onCalltipClick(self, args):
        if self.activeCalltip == 'doc':# and args['position']==0:
            var, calltip = self.interp.getFullCallTip()
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
