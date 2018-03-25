#
# PyPadPlusPlus: Execute command while cursor stays at position
#
# Put a shortcut on this script to start the interactive programming
# Recommended is <Shift> + <Ctrl> + <Enter>

externalPython = False  # Use external Python installation of the system

try:
    assert pypad != None
except:
    import pyPadPlusPlus
    pypad = pyPadPlusPlus.pyPad(externalPython)

pypad.execute(moveCursor=False)

