# PyPadPlusPlus
### Addon for Notepad++ and PythonScript for interactive Python development

PyPadPlusPlus is an interactive Python environment based on Notepad++ (https://notepad-plus-plus.org/) and PythonScript (https://github.com/bruderstein/PythonScript/).

It's concept is to fuse the interactive Python shell and editor to one single tool and unify the advantages of both. You never have to copy code any more from the editor to the interactive shell and back, depending on whether you want to work interactively with the code or keep it permanently in your algorithm. Instead, your editor becomes an interactive workbench where your algorithm is both tried out piece by piece and finally assembled.

To execute one line or a piece of code press `<Shift> + <Enter>`. This will run the current line or the smallest piece of code the can run individually. By selecting several lines (or the whole script with `<Ctrl> + <A>`) you can execute any part of your program. Cells of code can be defined by special comments starting with `#%%`. You have always the choice whether you want to execute cells, single lines or code selections. With the mouse wheel button you can execute any line or code piece by one click. The output is shown in an output console frame. The console has also an undo buffer for every execution that produced any output.

By selecting a variable and hovering over it with the mouse or pressing `<Shift> + <Ctrl> + <Space>` will show a calltip with information about it's current type and value. Autocompletion lists for objects and dictionaries allows you to explore the current run-time information of a variable.

The editor comes with another little feature that fits perfectly in the workflow of PyPadPlusPlus. It allows you to log small pieces of code you wish to keep but don't know where to store. Just select any piece of code and press the keyboard shortcut `<Alt> + <S>`. The selection will be added to a file `codeSnippetsLog.txt` with the time and date in a comment line. Pressing the shortcut again without any selection opens this file. It acts as a kind of "Python diary" for code snippets.

  <img src="https://raw.githubusercontent.com/bitagoras/PyPadPlusPlus/master/demo/pyPadDemo.gif">  

#### Features

* Run Python code line-by-line with `<Shift> + <Enter>`
* Run selected Python code (intelligent selection, no accurate selection is required)
* Run line or selection with middle mouse button
* Run cells of python code defined by `#%%` comments with `<Shift> + <Enter>`
* A color marker highlights last executed lines
* Animated color marker for active lines
* Calltip popup for object inspection of selected items and mouse hover or `<Shift> + <Ctrl> + <Space>`
* Calltip with size information of numpy arrays
* Evaluate variables or any selected expression, even some code is running
* Code auto completion for run-time defined object properties, dictionary keys, function calls
* Calltip popup for function calls, doc string and module help
* Special popup to switch quickly between `True` and `False`
* Click on popup to show full string or help text in output console
* Output console has an undo buffer
* Internal or external Python distribution
* Reset and restart Python kernel (e.g. when stuck in endless loop, not available when using the internal Python)
* Matplotlib event handler to hold multiple active plot windows

#### Roadmap
Planned feature:
* Remote kernel mode to run the code via network on any remote server that has Python installed, e.g. on raspberry PI.

#### Download

PyPadPlusPlus requires Notepad++ and PythonScript. Since the installation is quite cumbersome you can download the newest [release](https://github.com/bitagoras/PyPadPlusPlus/releases) ready-to-play in a bundle with Notepad++ v7.8 and PythonScript v1.5.2.0 as portable version:
* Download [`Npp7.8_32bit_PyPadPlusPlus1.2.zip`](https://github.com/bitagoras/PyPadPlusPlus/releases/download/1.2.0/Npp7.8_32bit_PyPadPlusPlus1.2.zip), unzip it into a folder and start `notepad++.exe`.

#### Installation

If you need to install PyPadPlusPlus in another version of Notepad++ you have to go the hard way:

1. Install Python Script from https://github.com/bruderstein/PythonScript/releases/ or in the plugin manager of Notepad++.
2. Download the sources or the latest [release](https://github.com/bitagoras/PyPadPlusPlus/releases) of PyPadPlusPlus and extract the files into the script folder of PythonScript:
  <br>`notepad++\plugins\PythonScript\scripts\` ("machine scripts")
  <br>or `notepad++\plugins\config\PythonScript\scripts\` ("user scripts")
3. Open the file `pyPadStart.py` and set `pythonPath` to the path of your pythonw.exe file.
4. Start Notepad++ and go to the menu "Plugins → Python Script → Configuration..."
5. Select "Machine Scripts" (or "User Scripts") and add the scripts to Menu items:
    * `pyPadClear.py` clears the console output
    * `pyPadExecute.py` executes the current line or selection
    * `pyPadExecuteFix.py` same as pyPadExecute but keeps the cursor at its position
    * `pyPadRestart.py`  restarts the python kernel or cleans the variables
    * `codeSnippetsLog.py`  optional: to store code snippets
    * `pyPadCalltip.py`     Shows a calltip with the content of the variable below the cursor or the evaluation of the selected expression.
6. Press OK, restart Notepad++ and go to menu "Settings → Shortcut mapper" and define in the tab "Plugin commands" the shortcuts:
    * `pyPadExecute.py     <Shift> + <Enter>`
    * `pyPadExecuteFix.py  <Shift> + <Ctrl> + <Enter>`
    * `pyPadClear.py       <Shift> + <Ctrl> + <C>`
    * `pyPadCalltip.py     <Shift> + <Ctrl> + <Space>`
    * `Show Console        <Ctrl> + <Alt> + <C>`
    * `pyPadRestart.py     <Alt> + <R>`
    * `codeSnippetsLog.py  <Alt> + <S>`
7. When Notepad++ does not allow you to define a shortcut on `<Shift> + <Enter>`, use `<Shift> + <Alt> + <Enter>` as preliminary shortcut. Then go to "Settings / Shortcut mapper / Scintilla commands" and unset `<Shift> + <Enter>` for `SCI_NEWLINE`. Now open `shortcuts.xml` in the Notepad++ Folder. Check if there is a line `<ScintKey ScintID="2329" menuCmdID="0" Ctrl="no" Alt="no" Shift="no" Key="13" />`. If not try to find it in the `C:\Users\<user name>\AppData\Roaming\Notepad++\` or  `C:\Users\<user name>\AppData\Local\Notepad++\` folder when Notepad++ was installed with the installer. Now search the line
    * `<PluginCommand moduleName="PythonScript.dll" internalID="8" Ctrl="no" Alt="yes" Shift="yes" Key="13" />`
    * The `internalID` can differ from yours. Then change the `Alt="yes"` into `Alt="no"`. 
8. If you want to use the Python installation of your system, open the file 
  `notepad++\plugins\PythonScript\scripts\` and set the variable `pythonPath` to the path that contains `pythonw.exe`.
