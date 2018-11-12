# PyPadPlusPlus
### Notepad++ plugin for interactive Python development

PyPadPlusPlus is a plugin for Notepad++ (https://notepad-plus-plus.org/) to interactivly work with Python. You can run your Python script interactively line by line or in selected blocks or run the entire file. Just go with the cursor somwehere in your code and press `<Ctrl> + <Enter>`. This will execute the current line or the smallest piece of code the can run individually. By selecting several lines or the whole script (with `<Ctrl> + <A>`) you can execute any part of your program. Blocks of code can be defined by a comment starting with `#%%`. With the mouse wheel button any selected code can be executed. The output is shown in a console frame. The console has an undo buffer for every output. By selecting a variable and hovering over it with the mouse you can get a calltip with information about it's current type and value. The autocompletion list for objects and dictionaries allows you to explore the current elements.

#### Installation

This plugin is a python script for the "Python Script" plugin for Notepad++.

To install pyPadPlusPlus:
* Install Python Script from https://github.com/bruderstein/PythonScript/releases/.
* Download a release of PyPadPlusPlus and extract the files into the script folder of PythonScript:
  <br>`notepad++\plugins\PythonScript\scripts\`
* Open the file `pyPadStart.py` and set `pythonPath` to the path of your the pythonw.exe file.
* Start Notepad++ and go to the menu "Plugins / Python Script / Configuration..."
* Select "Machine Scripts" and add the scripts to Menu items:
  *  `pyPadClear.py`
  *  `pyPadExecute.py`
  *  `pyPadExecuteFix.py`
  *  `pyPadRestart.py`
* Press OK and restart Notepad++ and go to menu "Settings / Shortcut mapper" and define in the tab "Plugin commands" the shortcuts:
  <br>`pyPadExecute.py     <Ctrl> + <Enter>`
  <br>`pyPadExecuteFix.py  <Shift> + <Ctrl> + <Enter>`
  <br>`pyPadClear.py       <Shift> + <Ctrl> + <C>`
  <br>`pyPadRestart.py     <Alt> + <R>`
