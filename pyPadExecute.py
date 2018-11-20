#
# PyPadPlusPlus: Execute command
#
# Put a shortcut on this script to start the interactive programming.
# Recommended is <Shift> + <Enter>

try: Npp.pypad != None
except: from pyPadStart import *

Npp.pypad.runCodeAtCursor()
