import Npp, datetime, os
text = Npp.editor.getTextRange(editor.getSelectionStart(), editor.getSelectionEnd()).rstrip()
 
filename = 'codeSnippetsLog.txt'
logDir = os.path.expanduser("~")

path = os.path.join(logDir, filename)

if text:
    with file(path,'a') as f:
        f.write('#%% ' + '_'*25 + ' ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' ' + '_'*25 + '\n\n' + text.replace('\r','').strip() + '\n\n')
    n = len(text.splitlines())
    Npp.notepad.messageBox('%i lines logged to %s'%(n,filename))
else:
    notepad.open(path)
    notepad.setLangType(Npp.LANGTYPE.PYTHON)