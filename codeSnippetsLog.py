import Npp, datetime, os
text = Npp.editor.getTextRange(editor.getSelectionStart(), editor.getSelectionEnd()).rstrip()
 
filename = 'codeSnippetsLog.txt'
logDir = os.path.expanduser("~")

path = os.path.join(logDir, filename)

if text:
    with file(path,'a') as f:
        f.write('# ' + '-'*50 + ' ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' ' + '-'*50 + '\n\n' + text.replace('\r','').strip()+'\n'*2)
    n = len(text.splitlines())
    Npp.notepad.messageBox('%i lines logged to %s'%(n,filename))
else:
    notepad.open(path)
    notepad.setLangType(Npp.LANGTYPE.PYTHON)