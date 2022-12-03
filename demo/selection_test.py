# Perform selection test in every single line

try: 1
except: 2
3

if True:
    1
elif True: 2
else: 3

if True: 1
elif True:2
else:
    3

if True: 1
if True: 1

elif True: 2
#
else: 3

for i in 1,2: 1
else: 2

while 0: 1
else: 2

while 0: 1
else:
    2
if True: 1

for i in 1,2:
    5

if True: 1

try:
    1
except:
    2

    3
#

finally:
    3

if True: 1

a = 3
b = 6 \
    + 3
c = 4

# TODO: too many lines are selected !!!
class a:
    def __enter__(self, *a): pass
    def __exit__(self, *a):pass

#
with a() as b,\
        a() as c:
    if True:
        pass
 
with a() as b,\
        a() as c:
    if True:
        pass

def test(x):
    pass



@test
@test
def test2():
    pass

numbers = list(map(int, numbers.split(',')) # EOF error!











