# PyPadPlusPlus
Notepad++ plugin for interactive Python development

PyPadPlusPlus is a plugin for Notepad++ to interactivly work with Python. You can run your Python script interactively line by line or in selected blocks or run the entire file. Just go with the cursor somwehere in your code and press `<Ctrl> + <Enter>`. This will execute the current line or the smallest piece of code the can run individually. By selecting several lines or the whole script (with `<Ctrl> + <A>`) you can execute any part of your program. Blocks of code can be defined by a comment starting with `#%%`. With the mouse wheel button any selected code can be executed. The output is shown in a console frame. The console has an undo buffer for every output. By selecting a variable and hovering over it with the mouse you can get a calltip with information about it's current type and value. The autocompletion list for objects and dictionaries allows you to explore the current elements.

This plugin is based on the "Python Script" plugin for Notepad++. As a prerequisit, you need to install Python Script from
https://github.com/bruderstein/PythonScript/releases/, copy the files of PyPadPlusPlus into the script folder and define in Notepad++ a shortcut on `<Ctrl> + <Enter>` on pyPadExecute.py. Optional define a shortcut `<Ctrl> + <Enter>` on pyPadExecuteFix.py for execution while keeping the cursor fixed and you can add a shortcut to clean the console (`<Shift> + <Ctrl> + <C>` on pyPadClean.py).

