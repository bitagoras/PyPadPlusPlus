#
# PyPadPlusPlus: Execute command
#
# Put a shortcut on this script to start the interactive programming
# Recommended is <Ctrl> + <Enter>

externalPython = False  # User external Python installation of the system, not yet implemented.

import sys, Npp
class PseudoFileOut2:
    def __init__(self, write):
        self.write = write
    def write(self, s): pass
try:
    assert pypad != None
except:
    sys.stdout=PseudoFileOut2(Npp.console.write)
    sys.stderr=PseudoFileOut2(Npp.console.writeError)
    sys.stdout.outp=PseudoFileOut2(Npp.console.write)
    import pyPadPlusPlus
    pypad = pyPadPlusPlus.pyPad(externalPython)
    Npp.pypad = pypad

pypad.execute()

