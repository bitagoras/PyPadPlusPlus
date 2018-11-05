#
# PyPadPlusPlus: Clear console
#
# Use this script for a shortcut to clear the console output
# Recommended is <Shift> + <Ctrl> + <C>

try:
    Npp.pypad != None
except:
    import Npp, pyPadPlusPlus
    Npp.pypad = pyPadPlusPlus.pyPad()
Npp.console.show()
Npp.editor.grabFocus()
Npp.console.clear()
Npp.console.editor.setReadOnly(0)