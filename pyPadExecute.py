#
# PyPadPlusPlus: Execute command
#
# Put a shortcut on this script to start the interactive programming
# Recommended is <Ctrl> + <Enter>

try:
    Npp.pypad.execute()
except:
    import Npp, pyPadPlusPlus
    # Use of an external Python interpreter is not implemented yet.
    Npp.pypad = pyPadPlusPlus.pyPad(externalPython=False)
    Npp.pypad.execute()

