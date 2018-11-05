#
# PyPadPlusPlus: Execute command while cursor stays at position
#
# Put a shortcut on this script to start the interactive programming
# Recommended is <Shift> + <Ctrl> + <Enter>

try:
    Npp.pypad.execute(moveCursor=False)
except:
    import Npp, pyPadPlusPlus
    Npp.pypad = pyPadPlusPlus.pyPad()
    Npp.pypad.execute(moveCursor=False)
