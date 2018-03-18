try:
    assert pypad != None
except:
    import pyPadPlusPlus
    pypad = pyPadPlusPlus.pyPad()

pypad.execute()

