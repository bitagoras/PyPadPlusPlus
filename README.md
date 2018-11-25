# PyPadPlusPlus
### Notepad++ plugin for interactive Python development

PyPadPlusPlus is a plugin for Notepad++ (https://notepad-plus-plus.org/) to interactivly work with Python. You can run your Python script interactively line by line or in selected blocks or run the entire file. Just go with the cursor somewhere in your code and press `<Shift> + <Enter>`. This will execute the current line or the smallest piece of code the can run individually. By selecting several lines or the whole script (with `<Ctrl> + <A>`) you can execute any part or the whole program. Cells of code can be defined by a comment starting with `#%%`. You have always the choice whether you want to execute cells or single lines of code. With the mouse wheel button you can execute any selected code or single line with one click. The output is shown in a console frame. The console has an undo buffer for every output. By selecting a variable and hovering over it with the mouse you can get a calltip with information about it's current type and value. Autocompletion lists for objects and dictionaries allows you to explore the current run-time information of an element.

Another little optional feature fits perfectly in the workflow of PyPadPlusPlus and allows you to log small pieces of code you like to remember but you don't know where to store it. Just select any piece of code and press the keyboard shortcut `<Alt> + <S>`. The selection will be added to a file `codeSnippetsLog.txt` with the time and date in a comment line. Pressing the shortcut again without any selection opens this file. When you figured out something new about Python you can use this function to log your finding in this "Python diary". Some month later when you have a déjà vu at the same problem you can have a look in the code-snippets log file. You can run in directly from this file.

  <img src="https://raw.githubusercontent.com/bitagoras/PyPadPlusPlus/master/demo/pyPadDemo.gif">  

#### Features

* Run Python code line-by-line
* Run selected Python code
* Run line or selection with middle mouse button
* Run cells of python code defined by `#%%` comments
* Code completion for run-time defined object properties, dictionary keys, function calls
* Calltip popup for function calls, doc string and module help
* Special popup to switch quickly between `True` and `False`
* Click on popup to show full text in output console
* Output console has an undo buffer
* Object inspection for selected items with mouse hover
* Color marker to highlight last executed lines
* Animated color marker for active lines
* Internal or external Python distribution
* Reset and restart Python kernel (e.g. when stuck in endless loop, not available when using the internal Python)
* Matplotlib event handler to hold multiple active plot windows

#### Download

PyPadPlusPlus requires in PythonScript and Notepad++. Since the installation is quite cumbersome you can download the newest [release](https://github.com/bitagoras/PyPadPlusPlus/releases) ready-to-play in a bundle with Notepad++ v7.6 and PythonScript v1.3.0.0 as portable version:
* Download [`Npp7.6_32bit_PyPadPlusPlus1.1.0.zip`](https://github.com/bitagoras/PyPadPlusPlus/releases/download/v1.1.0/Npp7.6_32bit_PyPadPlusPlus1.1.0.zip), unzip it into a folder and start `notepad++.exe`.

#### Installation

If you need to install PyPadPlusPlus in another version of Notepad++ you have to go the hard way:

1. Install Python Script from https://github.com/bruderstein/PythonScript/releases/.
2. Download the sources or the latest [release](https://github.com/bitagoras/PyPadPlusPlus/releases) of PyPadPlusPlus and extract the files into the script folder of PythonScript:
  <br>`notepad++\plugins\PythonScript\scripts\`
3. Open the file `pyPadStart.py` and set `pythonPath` to the path of your pythonw.exe file.
4. Start Notepad++ and go to the menu "Plugins → Python Script → Configuration..."
5. Select "Machine Scripts" and add the scripts to Menu items:
    * `pyPadClear.py` clears the console output
    * `pyPadExecute.py` executes the current line or selection
    * `pyPadExecuteFix.py` same as pyPadExecute but keeps the cursor at its position
    * `pyPadRestart.py`  restarts the python kernel or cleans the variables
    * `codeSnippetsLog.py`  optional: to store code snippets
6. Press OK, restart Notepad++ and go to menu "Settings → Shortcut mapper" and define in the tab "Plugin commands" the shortcuts:
    * `pyPadExecute.py     <Shift> + <Enter>`
    * `pyPadExecuteFix.py  <Shift> + <Ctrl> + <Enter>`
    * `pyPadClear.py       <Shift> + <Ctrl> + <C>`
    * `pyPadRestart.py     <Alt> + <R>`
    * `codeSnippetsLog.py  <Alt> + <S>`
7. When Notepad++ does not allow you to define a shortcut on `<Shift> + <Enter>`, use `<Shift> + <Alt> + <Enter>` as preliminary shortcut. Then go to "Settings / Shortcut mapper / Scintilla commands" and unset `<Shift> + <Enter>` for `SCI_NEWLINE`. Now open `shortcuts.xml` in the Notepad++ Folder. Check if there is a line `<ScintKey ScintID="2329" menuCmdID="0" Ctrl="no" Alt="no" Shift="no" Key="13" />`. If not try to find it in the `C:\Users\<user name>\AppData\Roaming\Notepad++\` or  `C:\Users\<user name>\AppData\Local\Notepad++\` folder when Notepad++ was installed with the installer. Now search the line
    * `<PluginCommand moduleName="PythonScript.dll" internalID="8" Ctrl="no" Alt="yes" Shift="yes" Key="13" />`
    * The `internalID` can differ from yours. Then change the `Alt="yes"` into `Alt="no"`. 
8. If you want to use the Python installation of you system, open the file 
  `notepad++\plugins\PythonScript\scripts\` and set the variable `pythonPath` to the path that contains `pythonw.exe`.
