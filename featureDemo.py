# This test file demonstrates features of PyPadPlusPlus

#%% Execution with Keyboard and Mouse

# <Ctrl> + <Return> executes the smalles possible piece of code
# that includes the line at the cursor or next to the cursor.

print "hello world"

# The value of a single expression line will be printed
1+2

# Muliline commands are executed as a whole and can be started
# from any line inside the indented block. A yellow line shows
# which lines have been executed.

for i in 1,2,3:
    s = str(i) * 8
    print "loop", s

# Multiple lines can be executed by selection and <Ctrl> + <Return>.
# The selection doesn't have to cover the whole line.
# With the middle mouse button (mouse wheel button) a single or
# multi line command or a selection can be executed.

print "* First line"
print "* Second line"


#%% Blocks of code can be started from special comments "#%%"

# The end of the block is defined by the next comment with "#%%"
# or the end of file.

multiline = """Multi line commands without
indent have do be started from the
first line or above"""


#%% Marker lines

# An animated dark line indicates that python is busy.
import time
for i in 1,2,3,4,5:
    print "wait for", i, '*'*i
    time.sleep(1)
    # you can interrupt and restart the kernel with <Alt> - <R>

# A red line indicates an syntax or runtime error.
# The python traceback error message is clickable.

# find the syntax error
a = [(1,13), (4,12),
     (6,11), (2,15),
     (1,12), (5,7)),
     (1,12), (5,14)]
     
def test(x):
    print 'We now divide', x, 'by zero.'
    print 'The result is:'
    print x / 0
    print "Now you"
    print 'removed the '
    print 'runtime error'

test(5)  # runtime error


#%% Code completion and call tips

# A code completion list is shown for any objects.
class car:
    nWheels = 4
    speed = 100
    color = "red"
car  # add a point "." after the variable to display the list

# Code completion is also available for dictionarys.
# This also works for h5py file objects.
bike = {
    'nWheels': 2,
    'speed': 20,
    'color': "blue"
    }
bike  # add a bracket "[" after the variable to display the list

# add a parenthesis "(" after the function to display the doc string
def twice(x, factor=2):
    """This function returns twice or more what it gets"""
    return factor*x
twice  # add a parenthesis "(" after the function to display the doc string

#%% Tool tips

var1 = {'two': 2}
var2 = [1,2,3]
var3 = (1,2,3)
var4 = "test"

# Select each variable (double click) and hover with the mouse.
# The type and string representation will be shown in a tooltip
# When clicking at the tooltip the full content is printed in
# the console. Use <Ctrl> - <Z> in the console to remove it again.
var1, var2, var3, var4, test, time

# Select the "True" and click at the tooltip to change to "False"
swich = True


#%% Console

# The console window can be cleaned with the selected keyboard short cut
# <Ctrl> - <Shift> - <C>

# When the console is closed, it can be restored by <Ctrl> - <Alt> - <C>

# The console has an undo buffer. Print some lines, click in the console
# and press undo (<Ctrl> - <Z>) to unto the print.
print '1.', multiline
print '2.', multiline
print '3.', multiline


#%% Matplotlib

# When an external python kernel is used that has matplotlib installed,
# multiple interactive plots can be plotted at the same time

import matplotlib.pyplot as plt
import numpy

fig = plt.figure()
x = numpy.linspace(0,10,500)
for i in 1,2,3:
    y = 0.2*numpy.cumsum(numpy.random.randn(500))
    plt.plot(x, y+5*i)
    plt.fill_between(x, y+5*i-0.1*y-1, y+5*i+0.1*y+1, alpha=0.2)
plt.show()

# The next figure can be shown while the first is visible

fig = plt.figure()
n, (r0, r1) = 100, numpy.random.rand(2)
for i in range(n):
    t = numpy.linspace(i,(i+1),250)
    x = (1 - 0.9*t/n) * numpy.cos(1.5*2*numpy.pi*(t+r0))
    y = (1 - 0.9*t/n) * (numpy.sin(3.008*2*numpy.pi*t) + numpy.sin(1.5*numpy.pi*(t+r1)))
    plt.plot(x, y, color=plt.cm.plasma(float(i)/n), alpha=0.9, lw=0.8)
plt.show()




