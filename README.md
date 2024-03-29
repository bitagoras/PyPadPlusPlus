# PyPadPlusPlus
### Addon for Notepad++ and PythonScript for interactive Python development

PyPadPlusPlus is an interactive Python environment based on Notepad++ (https://notepad-plus-plus.org/) and PythonScript (https://github.com/bruderstein/PythonScript/).

Its special property is a fusion of the interactive Python shell with the editor to one single tool. This means that the editor can be used for both interactive testing and storing the final code. So, you never have to copy code lines again from the editor to the shell or back. The output appears in a second frame, which is an output-only area, while the editor is an input-only area.

To execute one line or a piece of code press `<Shift> + <Enter>`. This executes the current line or the smallest number of lines belonging syntatically to the selection. No precise selection is required in order to execute valid parts of the code. The whole script can be executed with the selection of all lines by `<Ctrl> + <A>`. Cells of code can be optionally defined by special comments starting with `#%%`. In any case you have the choice whether you want to execute cells, single lines or code selections. With the mouse wheel button you can execute any line or piece of code by one click. The output is shown in an output console frame. The console has an undo buffer for every execution that produced some output.

Selecting a variable and hovering over it with the mouse or selecting any expresion and pressing `<Alt> + <Space>` will show a popup with information about its current type and value. This also supports numpy shape information. Autocompletion lists for objects and dictionaries allows you to explore the current run-time information of a variable.

The extension comes with another little feature that fits perfectly in the workflow of PyPadPlusPlus. It allows you to log small pieces of code you wish to keep but don't know where to store. Just select any piece of code and press the keyboard shortcut `<Alt> + <S>`. The selection will be added to a file `codeSnippetsLog.txt` with the time and date in a comment line. Pressing the shortcut again without any selection opens this file. It acts as a kind of "Python diary" for code snippets.

<img src="https://raw.githubusercontent.com/bitagoras/PyPadPlusPlus/master/demo/pyPadDemo.gif">

#### Features

* Run Python code line-by-line with `<Shift> + <Enter>`
* Run selected Python code (intelligent selection, no accurate selection is required)
* Run line or selection with middle mouse button
* Run line or selection multiple times while cursor does not propagate (`<Shift> + <Ctrl> + <Enter>`)
* Run cells of python code defined by `#%%` comments with `<Shift> + <Enter>` whey the cursor is at this comment line
* A color marker highlights last executed lines
* Animated color marker for active lines
* Tooltip for run-time variable and object inspection of selected items and mouse hover or `<Alt> + <Space>`.
* Evaluate any selected expression with `<Alt> + <Space>`, even while the code is still running
* Special Tooltip with size and shape information of numpy arrays
* Code auto completion for run-time defined object properties, dictionary keys, function calls
* Calltip for function calls, doc string and module help
* Special Tooltip to quickly switch between `True` and `False`
* Click on any Tooltip to show full string or help text in output console
* Output console has an undo buffer (click inside and press `<Ctrl> + <z>`). This can also be used to show the Python version and initialization text after startup.
* Clear output console with `<Shift> + <Ctrl> + <C>`.
* Internal or external Python distribution can be used for Python 3 kernels.
* Take controll over Notepad++ with the Npp module provided by PythonScript (only available when using the internal Python. Load library with `import Npp`)
* Reset and restart Python kernel with `<Alt> + <R>`, e.g. when stuck in endless loop. (only available when using an external Python, otherwise this only performs a variable reset. This function is currently broken.)
* Matplotlib event handler to hold multiple active plot windows

#### Tutorial
Tutorial video on PyPadPlusPlus by Amit Christian:

<a href="https://youtu.be/qSwbavkYE3w"><img src="https://i.imgur.com/QAdLlON.png" width="400"></a>

#### Download

PyPadPlusPlus requires Notepad++ and PythonScript. Since the installation is quite cumbersome you can download the [latest release](https://github.com/bitagoras/PyPadPlusPlus/releases/latest) ready-to-play in a bundle with Notepad++ v8.6, PythonScript v3.0.16.0 and Python 3.10 as portable version:
* Download [`Npp8.6_32bit_PyPadPlusPlus1.3.0_Python3.10.11.zip`](https://github.com/bitagoras/PyPadPlusPlus/releases/download/v1.3.0/Npp8.6_32bit_PyPadPlusPlus1.3.0_Python3.10.11.zip), unzip it into a folder and start `notepad++.exe`.

#### Installation

If you need to install PyPadPlusPlus in another version of Notepad++ there is some more work to do:

1. Install Python Script from https://github.com/bruderstein/PythonScript/releases/ or in the plugin manager of Notepad++.
2. Download the sources or the latest [release](https://github.com/bitagoras/PyPadPlusPlus/releases) of PyPadPlusPlus and extract the files into the user script folder of PythonScript:
  <br>`notepad++\plugins\config\PythonScript\scripts\` ("user scripts")
3. Start Notepad++ and go to the menu "Plugins → Python Script → Configuration..."
4. Select "User Scripts" and add the scripts to Menu items:
    * `pyPadClear.py` clears the console output
    * `pyPadExecute.py` executes the current line or selection
    * `pyPadExecuteFix.py` same as pyPadExecute but keeps the cursor at its position
    * `pyPadRestart.py`  restarts the python kernel or cleans the variables
    * `codeSnippetsLog.py`  optional: to store code snippets
    * `pyPadCalltip.py`     Shows a calltip with the content of the variable below the cursor or the evaluation of the selected expression.
5. Press OK, restart Notepad++ and go to menu "Settings → Shortcut mapper" and define in the tab "Plugin commands" the shortcuts:
    * `pyPadExecute.py     <Shift> + <Enter>`
    * `pyPadExecuteFix.py  <Shift> + <Ctrl> + <Enter>`
    * `pyPadClear.py       <Shift> + <Ctrl> + <C>`
    * `pyPadCalltip.py     <Alt> + <Space>`
    * `Show Console        <Ctrl> + <Alt> + <C>`
    * `pyPadRestart.py     <Alt> + <R>`
    * `codeSnippetsLog.py  <Alt> + <S>`
    
    Note that you have to unset some conflicting shortcuts (Shortcuts can be removed by choosing "None" in the list of keys).
6. If you want to use the Python installation of your system, open the file
  `notepad++\plugins\PythonScript\scripts\` and set the variable `pythonPath` to the path that contains your `pythonw.exe`.
