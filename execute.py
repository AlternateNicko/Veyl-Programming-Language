from VeylPL.veyl import VEY
from VeylPL.vdebug import debug
from VeylPL.library.test import Test

import time

instructions = r"""
import test

test.test_print("hello")

var = 20

test2 = test.test_add(10, var)
output(test2)
"""

module = {
    "test": Test
}

#OPTIONAL
path = None # put directory path
file = "veyl_run" # put name here, with no extensions

vey = VEY(instructions, module)
start = time.perf_counter()

results = vey.execute()

est = time.perf_counter() - start
print(f"{est:.4f}s")

ndb = debug(1)
ndb.print_init(vey)
ndb.print_functions(vey)
ndb.print_classes(vey)
ndb.print_libraries(vey)