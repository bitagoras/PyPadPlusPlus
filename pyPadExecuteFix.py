#
# PyPadPlusPlus: Execute command while cursor stays at position
#
# Put a shortcut on this script to start the interactive programming.
# Recommended is <Ctrl> + <Shift> + <Enter>

try: Npp.pypad != None
except: from pyPadStart import *

Npp.pypad.runCodeAtCursor(moveCursor=False)
