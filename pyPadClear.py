#
# PyPadPlusPlus: Clear console
#
# Use this script for a shortcut to clear the console output
# Recommended is <Shift> + <Ctrl> + <C>

try:
    Npp.pypad != None
except:
    import Npp, pyPadPlusPlus
    # Use of an external Python interpreter is not implemented yet.
    Npp.pypad = pyPadPlusPlus.pyPad(externalPython=False)
Npp.console.show()
Npp.console.clear()
Npp.console.editor.setReadOnly(0)