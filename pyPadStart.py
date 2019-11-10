#
# PyPadPlusPlus: Startup script
#

# Set the path to the Python file or the folder that contains pythonw.exe, 
# e.g. "C:\\programs\\Anaconda3". If pythonPath is None, the internal Python
# distribution of Notepad++ PythonScript is used. Kernel restart features is 
# only available for the external Python kernel. Python 2.x and 3.x
# are supported. Make sure that the environment variables are set for the
# loaded Python installation.
#
pythonPath = None

# In case of problems with certain libraries (e.g. numpy, matplotlib, Qt) set
# the required environment variables of your Python distribution manually by:
# import os
# os.environ['PATH'] = 

# To use multiple interactive matplotlib windows, pyPadPlusPlus
# runs an internal matplotlib event handler during idle time.
# If this cases any problems, set it to False.
# The matplotlib event handler is activated when matplotlib
# is imported. In case matplotlib is imported implicitly by
# another module, you must add to a code line a comment that
# contains the word "matplotlib".
#
matplotlib_eventHandler = True

# Cell highlighter underlines comments starting with #%% to highlight
# code cells. This can slowdown Notepad++ during heavy computational load.
#
cellHighlight = True

# mouseDwellTime in milliseconds sets the time until a popup is shown
# when mouse movement stops at a certain variable.
#
mouseDwellTime=200

# When set to False popups appear only with mouse hover over selected variables.
#
popupForUnselectedVariable = False

# Evaluates any selected expression with mouse hover. Be carefull with this
# option set to true, since selected functions can be called unintentionally. 
#
popupForSelectedExpression = False

# The latter two options are recommended to be set to false. The two features
# are allways active for the defined keyboard shortcut to script pyPadCalltip.py.

# Start pyPadPlusPlus
import Npp, pyPad
Npp.pypad = pyPad.pyPadPlusPlus(
        externalPython=pythonPath,
        matplotlib_eventHandler=matplotlib_eventHandler,
        cellHighlight=cellHighlight,
        popupForUnselectedVariable=popupForUnselectedVariable,
        popupForSelectedExpression=popupForSelectedExpression,
        mouseDwellTime=mouseDwellTime)
