#
# PyPadPlusPlus: Execute command while cursor stays at position
#
# Put a shortcut on this script to start the interactive programming
# Recommended is <Shift> + <Ctrl> + <Enter>

try:
    Npp.pypad.execute(moveCursor=False)
except:
    import Npp, pyPadPlusPlus
    # Use of an external Python interpreter is not implemented yet.
    Npp.pypad = pyPadPlusPlus.pyPad(externalPython=False)
    Npp.pypad.execute(moveCursor=False)
