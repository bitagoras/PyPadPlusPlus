#
# PyPadPlusPlus: Startup script
#

# Set the path to pythonw.exe, e.g. "C:\\programs\\Anaconda2\\pythonw.exe".
# If pythonPath is None, the internal python of Notepad++ PythonScript 
# is used. Some features are only available for the external python kernel.
# Python 3 is not supported, only Python 2. 

pythonPath = None

# To use multiple interactive matplotlib windows, pyPadPlusPlus
# runs an internal matplotlib event handler during idle time.
# In case this causes problems, set to False

matplotlib_EventHandler = True


# Start pyPadPlusPlus
import Npp, pyPadPlusPlus
Npp.pypad = pyPadPlusPlus.pyPad(externalPython=pythonPath,
        matplotlib_EventHandler=matplotlib_EventHandler)
