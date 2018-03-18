#
# PyPadPlusPlus: Execute command
#
# Put a shortcut on this script to start the interactive programming
# Recommended is <Ctrl> + <Enter>

try:
    assert pypad != None
except:
    import pyPadPlusPlus
    pypad = pyPadPlusPlus.pyPad()

pypad.execute()

