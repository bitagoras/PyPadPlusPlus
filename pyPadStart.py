#
# PyPadPlusPlus: Startup script
#

# Set the path to the folder that contains pythonw.exe, e.g.
# "C:\\programs\\Anaconda2". If pythonPath is None, the internal Python
# distribution of Notepad++ PythonScript is used. Some features are only
# available for the external Python kernel. Python 3 is currently not
# supported, only Python 2.

pythonPath = None

# To use multiple interactive matplotlib windows, pyPadPlusPlus
# runs an internal matplotlib event handler during idle time.
# If this cases any problems, set it to False.
# The matplotlib event handler is activated when matplotlib
# is imported. In case matplotlib is imported implicitly by
# another module, you must add to a code line a comment that
# contains the word "matplotlib".

matplotlib_EventHandler = True

# Cell highlighter underlines comments starting with #%% to highlight
# code cells. This can slowdown Notpad++ during heavy computational load.

cellHighlight = True


# Start pyPadPlusPlus
import Npp, pyPadPlusPlus
Npp.pypad = pyPadPlusPlus.pyPad(
        externalPython=pythonPath,
        matplotlib_EventHandler=matplotlib_EventHandler,
        cellHighlight=cellHighlight)
