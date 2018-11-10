#
# PyPadPlusPlus: Execute command
#
# Put a shortcut on this script to start the interactive programming
# Recommended is <Ctrl> + <Enter>

try:
    Npp.pypad.runCodeAtCursor()
except:
    import Npp, pyPadPlusPlus
    Npp.pypad = pyPadPlusPlus.pyPad()
    Npp.pypad.runCodeAtCursor()

