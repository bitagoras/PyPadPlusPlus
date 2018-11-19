# PyPadPlusPlus
### Notepad++ plugin for interactive Python development

PyPadPlusPlus is a plugin for Notepad++ (https://notepad-plus-plus.org/) to interactivly work with Python. You can run your Python script interactively line by line or in selected blocks or run the entire file. Just go with the cursor somewhere in your code and press `<Shift> + <Enter>`. This will execute the current line or the smallest piece of code the can run individually. By selecting several lines or the whole script (with `<Ctrl> + <A>`) you can execute any part or the whole program. Cells of code can be defined by a comment starting with `#%%`. You have allways the choice whether you want to execute cells or single lines of code. With the mouse wheel button you can executed any selected code or single line with one click. The output is shown in a console frame. The console has an undo buffer for every output. By selecting a variable and hovering over it with the mouse you can get a calltip with information about it's current type and value. Autocompletion lists for objects and dictionaries allows you to explore the current run-time information of an element.

Another little optional feature fits perfectly in the workflow of PyPadPlusPlus and allows you to log small pieces of code you like to remember but you don't know where to store it. Just select any piece of code and press the keyboard shortcut (e.g. `<Alt> + <S>`). The selection will be added to a file `codeSnippetsLog.txt` with the time and date in a comment line. Pressing the shortcut again without any selection opens this file. When you figured out something new about Python you can use this function to log your finding in this "Python diary". Some month later when you have a déjà vu at the same problem you can have a look in the code-snippets log file. You can run in directly from this file.

  <img src="https://raw.githubusercontent.com/bitagoras/PyPadPlusPlus/master/demo/pyPadDemo.gif">  

#### Features

* Run Python code line by line
* Run selected Python code
* Run line or selection with middle mouse button
* Run cells of python code defined by `#%%` comments
* Code completion for run-time defined object properties, dictionary keys, function calls
* Calltip popup for function calls
* Calltip popup to switch between `True` and `False`
* Click on calltip shows full text in output console
* Output console has an undo buffer
* Object inspection for selected items with mouse hover
* Color marker to highlight last executed lines
* Animated color marker for active lines
* Internal or external Python distribution
* Reset and restart Python kernel (e.g. when stuck in endless loop)
* Matplotlib event handler to hold multiple active plot windows

#### Installation

To install pyPadPlusPlus, several steps are required:
* Install Python Script from https://github.com/bruderstein/PythonScript/releases/.
* Download the sources or the latest [release](https://github.com/bitagoras/PyPadPlusPlus/releases) of PyPadPlusPlus and extract the files into the script folder of PythonScript:
  <br>`notepad++\plugins\PythonScript\scripts\`
* Open the file `pyPadStart.py` and set `pythonPath` to the path of your the pythonw.exe file.
* Start Notepad++ and go to the menu "Plugins / Python Script / Configuration..."
* Select "Machine Scripts" and add the scripts to Menu items:
  * `pyPadClear.py` clears the console output
  * `pyPadExecute.py` executes the current line or selection
  * `pyPadExecuteFix.py` same as pyPadExecute but keeps the cursor at its position
  * `pyPadRestart.py`  restarts the python kernel or cleans the variables
  * `codeSnippetsLog.py`  optional: to store code snippets
* Press OK, restart Notepad++ and go to menu "Settings / Shortcut mapper" and define in the tab "Plugin commands" the shortcuts (unset existing shortcuts in case of conflict):
  * `pyPadExecute.py     <Shift> + <Enter>`
  * `pyPadExecuteFix.py  <Ctrl> + <Enter>`
  * `pyPadClear.py       <Shift> + <Ctrl> + <C>`
  * `pyPadRestart.py     <Alt> + <R>`
  * `codeSnippetsLog.py  <Alt> + <S>`
* When Notepad++ does not allow you to define a shortcut on `<Shift> + <Enter>`, use `<Shift> + <Ctrl> + <Enter>` as preliminary shortcut. Then go to "Settings / Shortcut mapper / Scintilla commands" and unset `<Shift> + <Enter>` for `SCI_NEWLINE`. Now open `shortcuts.xml` in the Notepad++ Folder (when installed from zip file) or in the C:\Users\<user name>\AppData\Roaming\Notepad++\ folder for when Notepad++ was installed with the installer. Change the line
  * `<PluginCommand moduleName="PythonScript.dll" internalID="8" Ctrl="yes" Alt="no" Shift="yes" Key="13" />`
  * into `<PluginCommand moduleName="PythonScript.dll" internalID="8" Ctrl="no" Alt="no" Shift="yes" Key="13" />`
* If you want to use the Python installation of you system, open the file 
  `notepad++\plugins\PythonScript\scripts\` and set the variable `pythonPath` to the path of `pythonw.exe`.
