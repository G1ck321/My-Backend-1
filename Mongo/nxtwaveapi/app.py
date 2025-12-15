import time, sys

MY = 60
def timer():
    global MY
    none = MY-1
    time.sleep(1)
    print(none)
    MY = none
    if MY<0:
        sys.exit(1)
    timer()
timer()