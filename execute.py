instructions = r"""
"""

from veyl import VEY
from vdebug import debug
from library.test import Test

import time

module = {
}

#OPTIONAL
path = None # put directory path
file = "veyl_run" # put name here, with no extensions

vey = VEY(instructions, module, path=path, file=file)
start = time.perf_counter()
#results = vey.execute()
try:
    results = vey.execute()
except Exception as e:
    vey.error(1000, type(e).__name__, e)

est = time.perf_counter() - start
print(f"\n{est:.4f}s") # estimates time, not required

ndb = debug(1) # turn to 0 if you do not want any after-execution debug info
ndb.print_init(vey)
ndb.print_functions(vey)
ndb.print_classes(vey)
ndb.print_libraries(vey)