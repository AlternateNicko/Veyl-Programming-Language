# Veyl libraries
import os, re
import time
import sys
from pathlib import Path

from veyl import VEY
from bil_helper.bil_string_complete import StringToolkit

t, m, r, sys, json, au = None, None, None, None, None, None
class libraries:
    """
    This module is specialized for built in libraries and helpers for veyl,
    The class holds a parser that parses and executes an instruction for multiple built in libraries.
    
    most libraries here mostly use pythons actual libraries, mostly built ins and doesn't requires any
    more library installations
    Libraries available
    python type libraries
    - math
    - files
    - random
    - time
    - os
    
    custom built ins
    - sys
    - smart
    - debug
    """
    def __init__(self, data):
        self.__dict__ = data.__dict__
        self.eval = data.eval
        self.special_split = data.special_split
        self.special_find = data.special_find
        self.error = data.error
    
    def process(self, line, vars, variant="av"):
        global t, m, r, sys, json, au
        t = self.py_modules.get("time")
        m = self.py_modules.get("math")
        r = self.py_modules.get("random")
        json = self.py_modules.get("json")
        sys = self.py_modules.get("sys")
        au = self.py_modules.get("au")
        self.variables = vars
        if variant == "av":
            res = self.assign_variables(line, variant)
            return tuple([self.variables])
        else:
            res = self.one_line(line, variant)
            return res
            
    def one_line(self, line, var):
        global t, m, json, sys, r, au
        if var == "ol":
            instruction = line
            try:
                if "time" in self.library and instruction.startswith(self.library_name["time"] + "."):
                    man = self.special_split(instruction, ".", ("'", '"'), ("'", '"'))[1]
                    if man.startswith("sleep(") and man.endswith(")"):
                        args = man[6:-1].strip()
                        val = self.eval(args, {}, vars, from_lib=True)
                        t.sleep(val)
                if "files" in self.library and instruction.startswith(self.library_name["files"] + "."):
                    man = self.special_split(instruction, ".", ("'", '"'), ("'", '"'))[1]
                    if man.startswith("dump(") and man.endswith(")"):
                        args = man[5:-1].strip().split(",")
                        file = self.eval(args[1].strip(), {}, self.variables, from_lib=True)
                        dictionary = self.eval(args[0], {}, self.variables, from_lib=True)
                        try:
                            json.dump(dictionary, file)
                        except Exception as e:
                            if not self.attempt:
                                print("\033[31mTraceback(most_recent_call_back):\033[0m")
                                for i in self.traceback:
                                    print(f"    TB - [ File `<{self.path / Path(self.file_name).with_suffix(self.file_extension)}>` line: {self.traceback[i]}, in {i} ],")
                                print(f"    TB - [ File `<{self.path / Path(self.file_name).with_suffix(self.file_extension)}>` TB found > line [{self.og_c}]: {self.Instructions[self.cnt]} in {i} ]")
                                print(f"\nValueError: value type of `{file}` is not a file type")
                                self.Errors["ValueError"] = True
                                return None
                            
                if "sys" in self.library and instruction.startswith(self.library_name["sys"] + "."):
                    man = self.special_split(instruction, ".", ("'", '"'), ("'", '"'))[1]
                    if man.startswith("jump(") and man.endswith(")"):
                        args = man[5:-1].strip()
                        value = self.eval(args, {}, self.variables, from_lib=True)
                        if not isinstance(value, int):
                            if not self.attempt:
                                print("\033[31mTraceback(most_recent_call_back):\033[0m")
                                for i in self.traceback:
                                    print(f"    TB - [ File `<{self.path / Path(self.file_name).with_suffix(self.file_extension)}>` line: {self.traceback[i]}, in {i} ],")
                                print(f"    TB - [ File `<{self.path / Path(self.file_name).with_suffix(self.file_extension)}>` TB found > line [{self.og_c}]: {self.Instructions[self.cnt]} in {i} ]")
                                print(f"\nTypeError: sys.jump() expects argument `{args}` to be an int, but got `{type(value)}` instead")
                                self.Errors["TypeError"] = True
                                return None
                        self.cnt = value
                    elif man.startswith("clear_term(") and man.endswith(")"):
                        print("\033c", end="")
                    elif man.startswith("stdwrite(") and man.endswith(")"):
                        args = self.eval(man[9:-1].strip(), {}, self.variables, from_lib=True)
                        sys.stdout.write(args)
                    elif man.startswith("stderr(") and man.endswith(")"):
                        args = self.eval(man[7:-1].strip(), {}, self.variables, from_lib=True)
                        sys.stderr.write(args)
                    elif man.startswith("setrecursionlimit(") and man.endswith(")"):
                        args = self.eval(man[18:-1].strip(), {}, self.variables, from_lib=True)
                        sys.setrecursionlimit(args)
                    elif man.startswith("exit(") and man.endswith(")"):
                        args = self.eval(man[5:-1].strip(), {}, self.variables, from_lib=True)
                        sys.exit(args + "\n")
                    elif man.startswith("attempt(") and man.endswith(")"):
                        self.attempt = not self.attempt
                if "debug" in self.library and instruction.startswith(self.library_name["debug"] + "."):
                    man = self.special_split(instruction, ".", ("'", '"'), ("'", '"'))[1]
                    if man.startswith("buzz(") and man.endswith(")"):
                        print("buzz")
                    elif man.startswith("fizz(") and man.endswith(")"):
                        print("fizz")
                    elif man.startswith("fizzbuzz(") and man.endswith(")"):
                        print("fizzbuzz")
                    elif man.startswith("defined(") and man.endswith(")"):
                        args = man[8:-1].strip()
                        if args in self.variables.keys():
                            print(f"<NDB>> VARIABLE <{args}> IS DEFINED")
                        else:
                            print(f"<NDB>> VARIABLE <{args}> IS NOT DEFINED")
                    elif man.startswith("def_func(") and man.endswith(")"):
                        args = man[9:-1].strip()
                        if args in self.functions.keys():
                            print(f"<NDB>> FUNCTION <{args}> IS DEFINED")
                        else:
                            print(f"<NDB>> FUNCTION <{args}> IS NOT DEFINED")
                    elif man.startswith("attributes(") and man.endswith(")"):
                        args = man[10:-1].strip()
                        if args not in self.classes.keys():
                            if not self.attempt:
                                print("\033[31mTraceback(most_recent_call_back):\033[0m")
                                for i in self.traceback:
                                    print(f"    TB - [ File `<{self.path / Path(self.file_name).with_suffix(self.file_extension)}>` line: {self.traceback[i]}, in {i} ],")
                                print(f"    TB - [ File `<{self.path / Path(self.file_name).with_suffix(self.file_extension)}>` TB found > line [{self.og_c}]: {self.Instructions[self.cnt]} in {i} ]")
                                print(f"\nNameError: given name is not a defined class object")
                                self.Errors["NameError"] = True
                                return None
                        print(self.classes[args])
                    elif man.startswith("isattribute(") and man.endswith(")"):
                        args = man[12:-1].strip().split(",", 1)
                        if args[0] not in self.classes.keys():
                            if not self.attempt:
                                print("\033[31mTraceback(most_recent_call_back):\033[0m")
                                for i in self.traceback:
                                    print(f"    TB - [ File `<{self.path / Path(self.file_name).with_suffix(self.file_extension)}>` line: {self.traceback[i]}, in {i} ],")
                                print(f"    TB - [ File `<{self.path / Path(self.file_name).with_suffix(self.file_extension)}>` TB found > line [{self.og_c}]: {self.Instructions[self.cnt]} in {i} ]")
                                print(f"\nNameError: given name is not a defined class object")
                                self.Errors["NameError"] = True
                                return None
                        elif args[1] not in self.classes[args[0]]["variables"].keys():
                            print(f"<NDB>> ATTRIBUTE {args[1]} IS A DEFINED ATTRIBUTE")
                        else:
                            print(f"<NDB>> ATTRIBUTE {args[1]} IS NOT A DEFINED ATTRIBUTE")
                    elif man.startswith("wait(") and man.endswith(")"):
                        import time
                        args = man[6:-1].strip()
                        v = self.eval(args, {}, self.variables, from_lib=True)
                        time.sleep(v)
                    elif man.startswith("debug(") and man.endswith(")"):
                        arg = man[6:-1].strip()
                        wait_time = self.eval(arg, {}, self.variables, from_lib=True) if arg else 0
                        return ("$<<DEBUGGED>>", wait_time)
                    elif man.startswith("adv_debug(") and man.endswith(")"):
                        arg = man[10:-1].strip()
                        wait_time = self.eval(arg, {}, self.variables, from_lib=True) if arg else 0
                        return ("$<<ADV_DEBUGGED>>", wait_time)
                    elif man.startswith("self_eval"):
                        return ("$<<SELF EVAL>>")
                    elif man.startswith("in_function(") and man.endswith(")"):
                        print(self.current_func)
                    elif man.startswith("in_class(") and man.endswith(")"):
                        print(self.in_class)
                    elif man.startswith("functions(") and man.endswith(")"):
                        print(self.functions)
                    elif man.startswith("errors(") and man.endswith(")"):
                        args = man[7:-1].strip()
                        if args == "":
                            for e in self.Errors.keys():
                                print(f"{e}: {self.Errors[e]}")
                        else:
                            print(self.Errors[args])
                    
                return (self.variables, self.cnt)
            except Exception as e:
                print(e)
                
    def assign_variables(self, line, var):
        global t, m, r, json, sys, au
        """
        This function is specialized mostly for variable assignments like
        var = module.function()
        """
        if var == "av":
            inst = line
            left = inst[0]
            right = inst[1]
            libs = False
            if "math" in self.library and right.startswith(self.library_name["math"] + "."):
                man = self.special_split(right, ".", ("'", '"'), ("'", '"'))[1]
                # constants
                if man.startswith("pi"):
                    self.variables[left] = m.pi
                elif man.startswith("e"):
                    self.variables[left] = m.e
                elif man.startswith("tau"):
                    self.variables[left] = m.tau
                elif man.startswith("inf"):
                    self.variables[left] = m.inf
                elif man.startswith("nan"):
                    self.variables[left] = m.nan
                # functions and methods
                elif man.startswith("ceil(") and man.endswith(")"):
                    args = man[5:-1].strip()
                    a = self.eval(args, {}, self.variables, from_lib=True)
                    self.variables[left] = m.ceil(a)
                elif man.startswith("floor(") and man.endswith(")"):
                    args = man[6:-1].strip()
                    a = self.eval(args, {}, self.variables, from_lib=True)
                    self.variables[left] = m.floor(a)
                elif man.startswith("trunc(") and man.endswith(")"):
                    args = man[6:-1].strip()
                    a = self.eval(args, {}, self.variables, from_lib=True)
                    self.variables[left] = m.trunc(a)
                elif man.startswith("factorial(") and man.endswith(")"):
                    args = man[10:-1].strip()
                    a = self.eval(args, {}, self.variables, from_lib=True)
                    self.variables[left] = m.factorial(a)
                elif man.startswith("fabs(") and man.endswith(")"):
                    args = man[5:-1].strip()
                    a = self.eval(args, {}, self.variables, from_lib=True)
                    self.variables[left] = m.fabs(a)
                elif man.startswith("fmod(") and man.endswith(")"):
                    args = man[5:-1].strip().strip(",")
                    a = self.eval(args[0], {}, self.variables, from_lib=True)
                    b = self.eval(args[1], {}, self.variables, from_lib=True)
                    self.variables[left] = m.fmod(a, b)
                elif man.startswith("remainder(") and man.endswith(")"):
                    args = man[10:-1].strip().strip(",")
                    a = self.eval(args[0], {}, self.variables, from_lib=True)
                    b = self.eval(args[1], {}, self.variables, from_lib=True)
                    self.variables[left] = m.remainder(a, b)
                elif man.startswith("modf(") and man.endswith(")"):
                    args = man[5:-1].strip()
                    a = self.eval(args, {}, self.variables, from_lib=True)
                    self.variables[left] = m.modf(a)
                elif man.startswith("copysign(") and man.endswith(")"):
                    args = man[9:-1].strip().strip(",")
                    a = self.eval(args[0], {}, self.variables, from_lib=True)
                    b = self.eval(args[1], {}, self.variables, from_lib=True)
                    self.variables[left] = m.copysign(a, b)
                elif man.startswith("exp(") and man.endswith(")"):
                    args = man[4:-1].strip()
                    a = self.eval(args, {}, self.variables, from_lib=True)
                    self.variables[left] = m.exp(a)
                elif man.startswith("log(") and man.endswith(")"):
                    args = man[4:-1].strip().split(",")
                    a = self.eval(args[0], {}, self.variables, from_lib=True)
                    if len(args) > 1:
                        b = self.eval(args[1], {}, self.variables, from_lib=True)
                    else:
                        b = m.e
                    self.variables[left] = m.log(a, b)
                elif man.startswith("log10(") and man.endswith(")"):
                    args = man[6:-1].strip()
                    a = self.eval(args, {}, self.variables, from_lib=True)
                    self.variables[left] = m.log10(a)
                elif man.startswith("log2(") and man.endswith(")"):
                    args = man[5:-1].strip()
                    a = self.eval(args, {}, self.variables, from_lib=True)
                    self.variables[left] = m.log2(a)
                elif man.startswith("sqrt(") and man.endswith(")"):
                    args = man[5:-1].strip()
                    a = self.eval(args, {}, self.variables, from_lib=True)
                    self.variables[left] = m.sqrt(a)
                elif man.startswith("cbrt(") and man.endswith(")"):
                    args = man[5:-1].strip()
                    a = self.eval(args, {}, self.variables, from_lib=True)
                    self.variables[left] = m.cbrt(a)
                elif man.startswith("sin(") and man.endswith(")"):
                    args = man[4:-1].strip()
                    a = self.eval(args, {}, self.variables, from_lib=True)
                    self.variables[left] = m.sin(a)
                elif man.startswith("cos(") and man.endswith(")"):
                    args = man[4:-1].strip()
                    a = self.eval(args, {}, self.variables, from_lib=True)
                    self.variables[left] = m.cos(a)
                elif man.startswith("tan(") and man.endswith(")"):
                    args = man[4:-1].strip()
                    a = self.eval(args, {}, self.variables, from_lib=True)
                    self.variables[left] = m.tan(a)
                elif man.startswith("asin(") and man.endswith(")"):
                    args = man[5:-1].strip()
                    a = self.eval(args, {}, self.variables, from_lib=True)
                    self.variables[left] = m.asin(a)
                elif man.startswith("acos(") and man.endswith(")"):
                    args = man[5:-1].strip()
                    a = self.eval(args, {}, self.variables, from_lib=True)
                    self.variables[left] = m.acos(a)
                elif man.startswith("atan(") and man.endswith(")"):
                    args = man[5:-1].strip()
                    a = self.eval(args, {}, self.variables, from_lib=True)
                    self.variables[left] = m.atan(a)
                elif man.startswith("degrees(") and man.endswith(")"):
                    args = man[8:-1].strip()
                    a = self.eval(args, {}, self.variables, from_lib=True)
                    self.variables[left] = m.degrees(a)
                elif man.startswith("radians(") and man.endswith(")"):
                    args = man[8:-1].strip()
                    a = self.eval(args, {}, self.variables, from_lib=True)
                    self.variables[left] = m.radians(a)
                elif man.startswith("sinh(") and man.endswith(")"):
                    args = man[5:-1].strip()
                    a = self.eval(args, {}, self.variables, from_lib=True)
                    self.variables[left] = m.sinh(a)
                elif man.startswith("cosh(") and man.endswith(")"):
                    args = man[5:-1].strip()
                    a = self.eval(args, {}, self.variables, from_lib=True)
                    self.variables[left] = m.cosh(a)
                elif man.startswith("tanh(") and man.endswith(")"):
                    args = man[5:-1].strip()
                    a = self.eval(args, {}, self.variables, from_lib=True)
                    self.variables[left] = m.tanh(a)
                elif man.startswith("asinh(") and man.endswith(")"):
                    args = man[6:-1].strip()
                    a = self.eval(args, {}, self.variables, from_lib=True)
                    self.variables[left] = m.asinh(a)
                elif man.startswith("acosh(") and man.endswith(")"):
                    args = man[6:-1].strip()
                    a = self.eval(args, {}, self.variables, from_lib=True)
                    self.variables[left] = m.acosh(a)
                elif man.startswith("atanh(") and man.endswith(")"):
                    args = man[6:-1].strip()
                    a = self.eval(args, {}, self.variables, from_lib=True)
                    self.variables[left] = m.atanh(a)
                elif man.startswith("erf(") and man.endswith(")"):
                    args = man[4:-1].strip()
                    a = self.eval(args, {}, self.variables, from_lib=True)
                    self.variables[left] = m.erf(a)
                elif man.startswith("gamma(") and man.endswith(")"):
                    args = man[6:-1].strip()
                    a = self.eval(args, {}, self.variables, from_lib=True)
                    self.variables[left] = m.gamma(a)
                elif man.startswith("isfinite(") and man.endswith(")"):
                    args = man[9:-1].strip()
                    a = self.eval(args, {}, self.variables, from_lib=True)
                    self.variables[left] = m.isfinite(a)
                elif man.startswith("isinf(") and man.endswith(")"):
                    args = man[6:-1].strip()
                    a = self.eval(args, {}, self.variables, from_lib=True)
                    self.variables[left] = m.isinf(a)
                elif man.startswith("isnan(") and man.endswith(")"):
                    args = man[6:-1].strip()
                    a = self.eval(args, {}, self.variables, from_lib=True)
                    self.variables[left] = m.isnan(a)
                elif man.startswith("fsum(") and man.endswith(")"):
                    args = man[5:-1].strip()
                    a = self.eval(args, {}, self.variables, from_lib=True)
                    self.variables[left] = m.fsum(a)
                elif man.startswith("prod(") and man.endswith(")"):
                    args = man[6:-1].strip().strip(",")
                    a = self.eval(args[0], {}, self.variables, from_lib=True)
                    if len(args) > 1:
                        b = self.eval(args[1], {}, self.variables, from_lib=True)
                    else:
                        b = 1
                    self.variables[left] = m.prod(a, b)
                elif man.startswith("dist(") and man.endswith(")"):
                    args = man[5:-1].strip().strip(",")
                    a = self.eval(args[0], {}, self.variables, from_lib=True)
                    b = self.eval(args[1], {}, self.variables, from_lib=True)
                    self.variables[left] = m.dist(a, b)
                return tuple([self.variables])
            if "random" in self.library and right.startswith(self.library_name["random"] + "."):
                man = self.special_split(right, ".", ("'", '"'), ("'", '"'))[1]
                if man.startswith("randint(") and man.endswith(")"):
                    libs = True
                    arg = man[8:-1].split(",")
                    vars = self.variables.copy()
                    arg[0] = self.eval(arg[0].strip(), {}, vars, from_lib=True)
                    arg[1] = self.eval(arg[1].strip(), {}, vars, from_lib=True)
                    if not isinstance(arg[0], int) or not isinstance(arg[1], int):
                        if not self.attempt:
                            print("\033[31mTraceback(most_recent_call_back):\033[0m")
                            for i in self.traceback:
                                print(f"    TB - [ File `<{self.path / Path(self.file_name).with_suffix(self.file_extension)}>` line: {self.traceback[i]}, in {i} ],")
                            print(f"    TB - [ File `<{self.path / Path(self.file_name).with_suffix(self.file_extension)}>` TB found > line [{self.og_c}]: {self.Instructions[self.cnt]} in {i} ]")
                            print(f"\nTypeError: randint() method expects interger arguments, not {type(arg[0])}, {type(arg[1])}")
                        self.Errors["TypeError"] = True
                        return None
                    self.variables[left] = r.randint(arg[0], arg[1])
                elif man.startswith("choice(") and man.endswith(")"):
                    libs = True
                    arg = self.eval(man[7:-1].strip(), {}, self.variables, from_lib=True)
                    if not isinstance(arg, (list, dict)):
                        if not self.attempt:
                            print("\033[31mTraceback(most_recent_call_back):\033[0m")
                            for i in self.traceback:
                                print(f"    TB - [ File `<{self.path / Path(self.file_name).with_suffix(self.file_extension)}>` line: {self.traceback[i]}, in {i} ],")
                            print(f"    TB - [ File `<{self.path / Path(self.file_name).with_suffix(self.file_extension)}>` TB found > line [{self.og_c}]: {self.Instructions[self.cnt]} in {i} ]")
                            print(f"\nTypeError: choice() method expects list or dict arguments, not {type(arg)}")
                        self.Errors["TypeError"] = True
                        return None
                    self.variables[left] = r.choice(arg)
                elif man.startswith("num(") and man.endswith(")"):
                    libs = True
                    if man[4:-1] == "":
                        arg = 10
                    else: arg = self.eval(man[4:-1].strip(), {}, self.variables, from_lib=True) * 10
                    self.variables[left] = r.randint(1, arg) / 10
                elif man.startswith("shuffle(") and man.endswith(")"):
                    args = man[8:-1].strip()
                    value = self.eval(args, {}, self.variables, from_lib=True)
                    r.shuffle(value)
                    self.variables[left] = value
                elif man.startswith("random(") and man.endswith(")"):
                    args = man[7:-1].strip()
                    self.variables[left] = r.random()
                elif man.startswith("uniform(") and man.endswith(")"):
                    args = man[8:-1].strip()
                    args = self.special_split(args, ",", ("'", '"'), ("'", '"'))
                    a = self.eval(args[0], {}, self.variables, from_lib=True)
                    b = self.eval(args[1], {}, self.variables, from_lib=True)
                    self.variables[left] = r.uniform(a, b)
                    
                return tuple([self.variables])
                
            if "time" in self.library and right.startswith(self.library_name["time"] + "."):
                man = self.special_split(right, ".", ("'", '"'), ("'", '"'))[1]
                if man.startswith("time(") and man.endswith(")"):
                    self.variables[left] = t.time()
                elif man.startswith("time_ns(") and man.endswith(")"):
                    self.variables[left] = t.time_ns()
                elif man.startswith("monotonic(") and man.endswith(")"):
                    self.variables[left] = t.monotonic()
                elif man.startswith("monotonic_ns(") and man.endswith(")"):
                    self.variables[left] = t.monotonic_ns()
                elif man.startswith("counter(") and man.endswith(")"):
                    self.variables[left] = t.perf_counter()
                elif man.startswith("counter_ns(") and man.endswith(")"):
                    self.variables[left] = t.perf_counter_ns()
                elif man.startswith("asctime(") and man.endswith(")"):
                    args = man[8:-1].strip()
                    try:
                        value = self.eval(args, {}, self.variables, from_lib=True)
                    except Exception:
                        self.variables[left] = t.asctime()
                        return
                    if value is None:
                        value = ""
                    self.variables[left] = t.asctime(value)
                elif man.startswith("localtime(") and man.endswith(")"):
                    args = man[10:-1].strip()
                    try:
                        value = self.eval(args, {}, self.variables, from_lib=True)
                    except Exception:
                        self.variables[left] = t.localtime()
                        return
                    self.variables[left] = t.localtime(value)
                elif man.startswith("ctime(") and man.endswith(")"):
                    args = man[6:-1].strip()
                    try:
                        value = self.eval(args, {}, self.variables, from_lib=True)
                    except Exception:
                        self.variables[left] = t.ctime()
                        return
                    self.variables[left] = t.ctime(value)
                elif man.startswith("strftime(") and man.endswith(")"):
                    args = man[9:-1].strip().split(",")
                    format = args[0]
                    t_tuple = self.eval(args[1], {}, self.variables, from_lib=True)
                    self.variables[left] = t.strftime(format, t_tuple)
                elif man.startswith("strptime"):
                    args = man[9:-1].strip().split(",")
                    string = self.eval(args[0], {}, self.variables, from_lib=True)
                    format = args[1]
                    self.variables[left] = t.strptime(string, format)
                return tuple([self.variables])
            if "smart" in self.library and right.startswith(self.library_name["smart"] + "."):
                man = self.special_split(right, ".", ("'", '"'), ("'", '"'))[1]
            
                if man.startswith("sm_split(") and man.endswith(")"):
                    args = man[9:-1].strip()
                    args = self.special_split(args, ",", ("'", '"'), ("'", '"'))
                    string = self.eval(args[0].strip(), {}, self.variables, from_lib=True)
                    if string is None:
                        string = " "
                    split_ch = self.eval(args[1].strip(), {}, self.variables, from_lib=True)
                    length = len(args)
                    in_char1, in_char2 = [], []
                    ret_cap_gr = False
                    limit = -1
                    ranges = [0, -1]
                    if length >= 3:
                        in_char1 = self.eval(args[2].strip(), {}, self.variables, from_lib=True)
                    if length >= 4:
                        in_char2 = self.eval(args[3].strip(), {}, self.variables, from_lib=True)
                    if length >= 5:
                        ret_cap_gr = self.eval(args[4].strip(), {}, self.variables, from_lib=True)
                    if length >= 6:
                        limit = self.eval(args[5].strip(), {}, self.variables, from_lib=True)
                    if length >= 7:
                        ranges = self.eval(args[6].strip(), {}, self.variables, from_lib=True)
                    self.variables[left] = self.vey.special_split(string, split_ch, in_char1, in_char2, ret_cap_gr, limit, ranges)
            
                elif man.startswith("sm_strip(") and man.endswith(")"):
                    args = man[9:-1].strip()
                    args = self.special_split(args, ",", ("'", '"', "("), ("'", '"', ")"))
                    string = self.eval(args[0].strip(), {}, self.variables, from_lib=True)
                    strip_target = self.eval(args[1].strip(), {}, self.variables, from_lib=True)
                    mode = "rl"
                    limit = -1
                    ranges = [0, -1]
                    length = len(args)
                    if length >= 3:
                        mode = self.eval(args[2].strip(), {}, self.variables, from_lib=True)
                    if length >= 4:
                        limit = self.eval(args[3].strip(), {}, self.variables, from_lib=True)
                    if length >= 5:
                        ranges = self.eval(args[4].strip(), {}, self.variables, from_lib=True)
                    self.variables[left] = self.strip(string, strip_target, mode, limit, ranges)
            
                elif man.startswith("sm_find(") and man.endswith(")"):
                    args = man[8:-1].strip()
                    args = self.special_split(args, ",", ("'", '"', "("), ("'", '"', ")"))
                    line = self.eval(args[0].strip(), {}, self.variables, from_lib=True)
                    target = self.eval(args[1].strip(), {}, self.variables, from_lib=True)
                    inner_group, outer_group = [], []
                    ranges = [0, -1]
                    length = len(args)
                    if length >= 3:
                        inner_group = self.eval(args[2].strip(), {}, self.variables, from_lib=True)
                    if length >= 4:
                        outer_group = self.eval(args[3].strip(), {}, self.variables, from_lib=True)
                    if length >= 5:
                        ranges = self.eval(args[4].strip(), {}, self.variables, from_lib=True)
                    self.variables[left] = self.find(line, target, inner_group, outer_group, ranges)
            
                elif man.startswith("find_index(") and man.endswith(")"):
                    args = man[11:-1].strip()
                    args = self.special_split(args, ",", ("'", '"', "("), ("'", '"', ")"))
                    list_value = self.eval(args[0].strip(), {}, self.variables, from_lib=True)
                    target = self.eval(args[1].strip(), {}, self.variables, from_lib=True)
                    limit = -1
                    ranges = [0, -1]
                    length = len(args)
                    if length >= 3:
                        limit = self.eval(args[2].strip(), {}, self.variables, from_lib=True)
                    if length >= 4:
                        ranges = self.eval(args[3].strip(), {}, self.variables, from_lib=True)
                    self.variables[left] = self.find_index(list_value, target, limit, ranges)
            
                elif man.startswith("find_str_index(") and man.endswith(")"):
                    args = man[15:-1].strip()
                    args = self.special_split(args, ",", ("'", '"', "("), ("'", '"', ")"))
                    line = self.eval(args[0].strip(), {}, self.variables, from_lib=True)
                    target = self.eval(args[1].strip(), {}, self.variables, from_lib=True)
                    limit = -1
                    ranges = [0, -1]
                    length = len(args)
                    if length >= 3:
                        limit = self.eval(args[2].strip(), {}, self.variables, from_lib=True)
                    if length >= 4:
                        ranges = self.eval(args[3].strip(), {}, self.variables, from_lib=True)
                    self.variables[left] = self.find_str_index(line, target, limit, ranges)
            
                elif man.startswith("find_key(") and man.endswith(")"):
                    args = man[9:-1].strip()
                    args = self.special_split(args, ",", ("'", '"', "("), ("'", '"', ")"))
                    dict_map = self.eval(args[0].strip(), {}, self.variables, from_lib=True)
                    target_key = self.eval(args[1].strip(), {}, self.variables, from_lib=True)
                    value_type = "any"
                    has_value = True
                    ranges = [0, -1]
                    length = len(args)
                    if length >= 3:
                        value_type = self.eval(args[2].strip(), {}, self.variables, from_lib=True)
                    if length >= 4:
                        has_value = self.eval(args[3].strip(), {}, self.variables, from_lib=True)
                    if length >= 5:
                        ranges = self.eval(args[4].strip(), {}, self.variables, from_lib=True)
                    self.variables[left] = self.find_key(dict_map, target_key, value_type, has_value, ranges)
            
                elif man.startswith("isindict(") and man.endswith(")"):
                    args = man[9:-1].strip()
                    args = self.special_split(args, ",", ("'", '"', "("), ("'", '"', ")"))
                    value = self.eval(args[0].strip(), {}, self.variables, from_lib=True)
                    dict_map = self.eval(args[1].strip(), {}, self.variables, from_lib=True)
                    self.variables[left] = value in dict_map.values()
            
                elif man.startswith("sm_replace(") and man.endswith(")"):
                    args = man[8:-1].strip()
                    args = self.special_split(args, ",", ("'", '"', "("), ("'", '"', ")"))
                    line = self.eval(args[0].strip(), {}, self.variables, from_lib=True)
                    target_chars = self.eval(args[1].strip(), {}, self.variables, from_lib=True)
                    replacement_chars = self.eval(args[2].strip(), {}, self.variables, from_lib=True)
                    limit = -1
                    ranges = [0, -1]
                    length = len(args)
                    if length >= 4:
                        limit = self.eval(args[3].strip(), {}, self.variables, from_lib=True)
                    if length >= 5:
                        ranges = self.eval(args[4].strip(), {}, self.variables, from_lib=True)
                    self.variables[left] = self.replace(line, target_chars, replacement_chars, limit, ranges)
            
                return tuple([self.variables])
            if "sys" in self.library and right.startswith(self.library_name["sys"] + "."):
                man = self.special_split(right, ".", ("'", '"'), ("'", '"'), limit=1)[1]
                if man.startswith("cnt"):
                    self.variables[left] = self.cnt
                elif man.startswith("variables"):
                    self.variables[left] = self.variables.copy()
                elif man.startswith("load_var(") and man.endswith(")"):
                    args = man[9:-1].strip()
                    value = self.eval(args, {}, self.variables, from_lib=True)
                    self.variables[left] = self.variables[value]
                elif man.startswith("stdinp()"):
                    self.variables[left] = sys.stdin.readline().strip()
                elif man.startswith("get."):
                    args = man[4:].strip()
                    if args.startswith("recursionlimit"):
                        self.variables[left] = sys.getrecursionlimit()
                    elif args.startswith("sizeof(") and args.endswith(")"):
                        arg = self.eval(args[7:-1].strip(), {}, self.variables)
                        self.variables[left] = sys.getsizeof(arg)
                    elif args.startswith("maxsize"):
                        self.variables[left] = sys.maxsize
                elif man.startswith("version"):
                    self.variables[left] = self.version
                elif man.startswith("platform"):
                    self.variables[left] = sys.platform
                elif man.startswith("sync_variables"):
                    self.variables[left] = self.sync_variables.copy()
                elif man.startswith("classes"):
                    self.variables[left] = self.classes
                return tuple([self.variables])
            if "files" in self.library and right.startswith(self.library_name["files"] + "."):
                man = self.special_split(right, ".", ("'", '"'), ("'", '"'), limit=1)[1]
                if man.startswith("load(") and man.endswith(")"):
                    args = man[5:-1].strip()
                    value = self.eval(args, {}, self.variables, from_lib=True)
                    self.variables[left] = json.load(value)
                elif man.startswith("dumps(") and man.endswith(")"):
                    args = man[6:-1].strip()
                    value = self.eval(args, {}, self.variables, from_lib=True)
                    self.variables[left] = json.dumps(value)
                elif man.startswith("loads(") and man.endswith(")"):
                    args = man[6:-1].strip()
                    value = self.eval(args, {}, self.variables, from_lib=True)
                    self.variables[left] = json.loads(value)      
                return tuple([self.variables])
            if "os" in self.library and right.startswith(self.library_name["os"] + "."):
                man = self.special_split(right, ".", ("'", '"'), ("'", '"'), limit=1)[1].strip()
                self.variables[left] = self._os_dispatch(man)
                return tuple([self.variables])
            if "string" in self.library and right.startswith(self.library_name["string"] + "."):
                man = self.special_split(right, ".", ("'", '"'), ("'", '"'), limit=1)[1]
                self.variables[left] = self.string_dispatch(man.strip())
                return tuple([self.variables])
    
    # class methods for other library functions
    def arguments(self, arg):
        # this parses pre assigned arguments like arg=60
        given = self.special_split(arg, "=", ('"', "'", "(", "[", "{"), ('"', "'", ")", "]", "}"), limit=1)
        name = given[0].strip()
        value = given[1].strip()
        return self.eval(value, {}, self.variables, from_lib=True)

    def _type_check(self, value, expected, expected_name, ctx):
        """
        Shared type guard for string_dispatch. Fires error 101 (reusing the
        existing "Function `{arg1}` expects a `{arg2}` argument type, but got
        `{arg3}`" message - the string library never had its own error codes
        registered in error_metadata.py/errormd.json, so codes 1001-1004 and
        109 that used to appear here would KeyError inside handle.stderr()
        the moment they fired) and returns False, or returns True if fine.
        """
        if not isinstance(value, expected):
            self.error(101, ctx, expected_name, type(value).__name__)
            return False
        return True

    def _dispatch_args(self, inst, prefix):
        """
        Splits the parenthesized, comma separated argument list of a
        `string.<prefix>(...)` call into raw (unevaluated) argument strings.

        Deliberately NOT self.special_split(raw, ",", ('"', "'", "(", "[", "{"),
        ('"', "'", ")", "]", "}")) - that convention treats the open/close
        sets as flat membership tests rather than a real stack, so a quoted
        argument containing a bracket character (e.g. find_encloser("a [b] c",
        "[", "]"), or a list literal of quoted strings like multi_split(s,
        [",", ";"])) closes the "inside a quote" state on the bracket char
        instead of the matching quote, and the whole split desyncs from
        there (IndexError / SyntaxError further down at eval() time). This
        walks the text with an explicit bracket stack and single-char quote
        toggling instead, so nesting is tracked correctly.
        """
        raw = inst[len(prefix):-1].strip()
        if raw == "":
            return []
        closers = {"(": ")", "[": "]", "{": "}"}
        args = []
        current = ""
        stack = []
        in_string = None
        i = 0
        while i < len(raw):
            ch = raw[i]
            if in_string:
                current += ch
                if ch == in_string:
                    in_string = None
                i += 1
                continue
            if ch in ("'", '"'):
                in_string = ch
                current += ch
                i += 1
                continue
            if ch in closers:
                stack.append(closers[ch])
                current += ch
                i += 1
                continue
            if stack and ch == stack[-1]:
                stack.pop()
                current += ch
                i += 1
                continue
            if ch == "," and not stack:
                args.append(current.strip())
                current = ""
                i += 1
                continue
            current += ch
            i += 1
        args.append(current.strip())
        return args

    def string_dispatch(self, inst):
        inst = inst.strip()
        if not inst.endswith(")"):
            self.error(68, f"string method call `{inst}` is missing a closing `)`")
            return None

        # ---- hand-rolled methods (pre-existing, bug-fixed) ----
        if inst.startswith("proper("):
            arg = inst[len("proper("):-1].strip()
            string = self.eval(arg, {}, self.variables)
            if not self._type_check(string, str, "str", "string.proper()"):
                return
            return self._string_proper(string)
        elif inst.startswith("random("):
            arg = inst[len("random("):-1].strip()
            string = self.eval(arg, {}, self.variables)
            if not self._type_check(string, str, "str", "string.random()"):
                return
            import random
            result = ""
            # was `for t in text` - `text` didn't exist (NameError) and `t`
            # shadowed the module-level `time` alias; renamed to `ch`/`string`
            for ch in string:
                if ch.isalpha() and ch.isascii():
                    result += random.choice([ch.upper(), ch.lower()])
                else:
                    result += ch
            return result
        elif inst.startswith("morse("):
            arg = inst[len("morse("):-1].strip()
            string = self.eval(arg, {}, self.variables)
            if not self._type_check(string, str, "str", "string.morse()"):
                return
            MORSE = {
                'A': '.-',    'B': '-...',  'C': '-.-.',  'D': '-..',
                'E': '.',     'F': '..-.',  'G': '--.',   'H': '....',
                'I': '..',    'J': '.---',  'K': '-.-',   'L': '.-..',
                'M': '--',    'N': '-.',    'O': '---',   'P': '.--.',
                'Q': '--.-',  'R': '.-.',   'S': '...',   'T': '-',
                'U': '..-',   'V': '...-',  'W': '.--',   'X': '-..-',
                'Y': '-.--',  'Z': '--..',
                '0': '-----', '1': '.----', '2': '..---', '3': '...--',
                '4': '....-', '5': '.....', '6': '-....', '7': '--...',
                '8': '---..', '9': '----.'
            }
            return ' '.join(MORSE.get(char, '/') for char in string.upper())
        elif inst.startswith("autocorrect("):
            arg = inst[len("autocorrect("):-1].strip()
            string = self.eval(arg, {}, self.variables)
            if not self._type_check(string, str, "str", "string.autocorrect()"):
                return
            global au
            spell = au(lang="en")
            words = string.split()  # was `text.split()` - `text` didn't exist
            corrected_words = []
            for word in words:
                match = re.match(r"^([^a-z0-9]*)([a-z0-9'-]+)([^a-z0-9]*)$", word)
                if match:
                    prefix, core, suffix = match.group(1), match.group(2), match.group(3)
                    if re.search(r"[a-z]", core):
                        core = spell(core)
                    word = prefix + core + suffix
                corrected_words.append(word)
            return " ".join(corrected_words)
        elif inst.startswith("ascii("):
            arg = inst[len("ascii("):-1].strip()
            string = self.eval(arg, {}, self.variables)
            if not self._type_check(string, str, "str", "string.ascii()"):
                return
            return [ord(char) for char in string.strip()]
        elif inst.startswith("decode_ascii("):
            arg = inst[len("decode_ascii("):-1].strip()
            numbers = self.eval(arg, {}, self.variables)
            if not self._type_check(numbers, (list, tuple), "list", "string.decode_ascii()"):
                return
            return "".join(chr(number) for number in numbers)
        elif inst.startswith("contains("):
            arg = self._dispatch_args(inst, "contains(")
            string = self.eval(arg[0], {}, self.variables)
            string1 = self.eval(arg[1], {}, self.variables)
            if not self._type_check(string, str, "str", "string.contains()"):
                return
            is_surround = True if len(arg) == 3 and self.eval(arg[2], {}, self.variables) else False
            if not is_surround:
                string1 = " " + string1 + " "
            return string1 in string
        elif inst.startswith("wordstrwith("):
            arg = self._dispatch_args(inst, "wordstrwith(")
            string = self.eval(arg[0], {}, self.variables)
            string1 = self.eval(arg[1], {}, self.variables)
            if not self._type_check(string, str, "str", "string.wordstrwith()"):
                return
            # was `string.strip.split(" ")` - missing call parens on .strip
            return any(a.startswith(string1) for a in string.strip().split(" "))
        elif inst.startswith("mask("):
            arg = self._dispatch_args(inst, "mask(")
            string = self.eval(arg[0], {}, self.variables)
            interger = self.eval(arg[1], {}, self.variables)
            if not self._type_check(string, str, "str", "string.mask()"):
                return
            if not self._type_check(interger, int, "int", "string.mask()"):
                return
            new_str = ""
            for i in range(len(string)):
                if i < interger:  # was missing the trailing colon (SyntaxError)
                    new_str += "*"
                    continue
                new_str += string[i]
            return new_str
        elif inst.startswith("find_encloser("):
            # was `inst[5:-1]` (copy-pasted from mask()'s 5-char prefix instead
            # of find_encloser('s actual 14), which mangled the argument text
            arg = self._dispatch_args(inst, "find_encloser(")
            string = self.eval(arg[0], {}, self.variables)
            enc1 = self.eval(arg[1], {}, self.variables)
            enc2 = self.eval(arg[2], {}, self.variables)
            if not self._type_check(string, str, "str", "string.find_encloser()"):
                return
            if not isinstance(enc1, str) or not isinstance(enc2, str):
                bad = enc1 if not isinstance(enc1, str) else enc2
                self.error(101, "string.find_encloser()", "str", type(bad).__name__)
                return
            # was searching in an undefined `text` instead of `string`
            start = string.find(enc1)
            if start == -1:
                return ""
            start += len(enc1)
            end = string.find(enc2, start)
            if end == -1:
                return ""
            return string[start:end]

        # ---- StringToolkit-backed methods (bil_string_complete.py) ----

        # search & query
        elif inst.startswith("find_all("):
            args = self._dispatch_args(inst, "find_all(")
            string = self.eval(args[0].strip(), {}, self.variables)
            delims = self.eval(args[1].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.find_all()"):
                return
            return StringToolkit.find_all(string, delims)
        elif inst.startswith("find_words("):
            args = self._dispatch_args(inst, "find_words(")
            string = self.eval(args[0].strip(), {}, self.variables)
            target = self.eval(args[1].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.find_words()"):
                return
            return StringToolkit.find_words(string, target)
        elif inst.startswith("find_after("):
            args = self._dispatch_args(inst, "find_after(")
            string = self.eval(args[0].strip(), {}, self.variables)
            target = self.eval(args[1].strip(), {}, self.variables)
            target_after = self.eval(args[2].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.find_after()"):
                return
            return StringToolkit.find_after(string, target, target_after)
        elif inst.startswith("find_before("):
            args = self._dispatch_args(inst, "find_before(")
            string = self.eval(args[0].strip(), {}, self.variables)
            target = self.eval(args[1].strip(), {}, self.variables)
            target_before = self.eval(args[2].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.find_before()"):
                return
            return StringToolkit.find_before(string, target, target_before)
        elif inst.startswith("contains_any("):
            args = self._dispatch_args(inst, "contains_any(")
            string = self.eval(args[0].strip(), {}, self.variables)
            delims = self.eval(args[1].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.contains_any()"):
                return
            return StringToolkit.contains_any(string, delims)
        elif inst.startswith("contains_all("):
            args = self._dispatch_args(inst, "contains_all(")
            string = self.eval(args[0].strip(), {}, self.variables)
            delims = self.eval(args[1].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.contains_all()"):
                return
            return StringToolkit.contains_all(string, delims)
        elif inst.startswith("startswith_any("):
            args = self._dispatch_args(inst, "startswith_any(")
            string = self.eval(args[0].strip(), {}, self.variables)
            delims = self.eval(args[1].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.startswith_any()"):
                return
            return StringToolkit.startswith_any(string, delims)
        elif inst.startswith("endswith_any("):
            args = self._dispatch_args(inst, "endswith_any(")
            string = self.eval(args[0].strip(), {}, self.variables)
            delims = self.eval(args[1].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.endswith_any()"):
                return
            return StringToolkit.endswith_any(string, delims)
        elif inst.startswith("multi_split("):
            args = self._dispatch_args(inst, "multi_split(")
            string = self.eval(args[0].strip(), {}, self.variables)
            delims = self.eval(args[1].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.multi_split()"):
                return
            return StringToolkit.multi_split(string, delims)

        # extraction
        elif inst.startswith("extract_emails("):
            args = self._dispatch_args(inst, "extract_emails(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.extract_emails()"):
                return
            return StringToolkit.extract_emails(string)
        elif inst.startswith("extract_url("):
            args = self._dispatch_args(inst, "extract_url(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.extract_url()"):
                return
            return StringToolkit.extract_url(string)
        elif inst.startswith("extract_numericals("):
            args = self._dispatch_args(inst, "extract_numericals(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.extract_numericals()"):
                return
            return StringToolkit.extract_numericals(string)
        elif inst.startswith("extract_integers("):
            args = self._dispatch_args(inst, "extract_integers(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.extract_integers()"):
                return
            return StringToolkit.extract_integers(string)
        elif inst.startswith("extract_decimals("):
            args = self._dispatch_args(inst, "extract_decimals(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.extract_decimals()"):
                return
            return StringToolkit.extract_decimals(string)
        elif inst.startswith("extract_dates("):
            args = self._dispatch_args(inst, "extract_dates(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.extract_dates()"):
                return
            fmt = self.eval(args[1].strip(), {}, self.variables) if len(args) > 1 else "dd/mm/yy"
            return StringToolkit.extract_dates(string, fmt)
        elif inst.startswith("extract_encloser("):
            args = self._dispatch_args(inst, "extract_encloser(")
            string = self.eval(args[0].strip(), {}, self.variables)
            left = self.eval(args[1].strip(), {}, self.variables)
            right = self.eval(args[2].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.extract_encloser()"):
                return
            return StringToolkit.extract_encloser(string, left, right)

        # similarity
        elif inst.startswith("similarity("):
            args = self._dispatch_args(inst, "similarity(")
            text1 = self.eval(args[0].strip(), {}, self.variables)
            text2 = self.eval(args[1].strip(), {}, self.variables)
            if not self._type_check(text1, str, "str", "string.similarity()"):
                return
            if not self._type_check(text2, str, "str", "string.similarity()"):
                return
            method = self.eval(args[2].strip(), {}, self.variables) if len(args) > 2 else "levenshtein"
            try:
                return StringToolkit.similarity(text1, text2, method)
            except (ValueError, ZeroDivisionError) as e:
                self.error(70, f"string.similarity() - {e}")
                return

        # case conversion
        elif inst.startswith("snake_case("):
            args = self._dispatch_args(inst, "snake_case(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.snake_case()"):
                return
            return StringToolkit.snake_case(string)
        elif inst.startswith("camel_case("):
            args = self._dispatch_args(inst, "camel_case(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.camel_case()"):
                return
            return StringToolkit.camel_case(string)
        elif inst.startswith("pascal_case("):
            args = self._dispatch_args(inst, "pascal_case(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.pascal_case()"):
                return
            return StringToolkit.pascal_case(string)
        elif inst.startswith("kebab_case("):
            args = self._dispatch_args(inst, "kebab_case(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.kebab_case()"):
                return
            return StringToolkit.kebab_case(string)
        elif inst.startswith("screaming_snake_case("):
            args = self._dispatch_args(inst, "screaming_snake_case(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.screaming_snake_case()"):
                return
            return StringToolkit.screaming_snake_case(string)
        elif inst.startswith("dot_case("):
            args = self._dispatch_args(inst, "dot_case(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.dot_case()"):
                return
            return StringToolkit.dot_case(string)
        elif inst.startswith("path_case("):
            args = self._dispatch_args(inst, "path_case(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.path_case()"):
                return
            return StringToolkit.path_case(string)
        elif inst.startswith("alternating_case("):
            args = self._dispatch_args(inst, "alternating_case(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.alternating_case()"):
                return
            return StringToolkit.alternating_case(string)
        elif inst.startswith("detect_case("):
            args = self._dispatch_args(inst, "detect_case(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.detect_case()"):
                return
            return StringToolkit.detect_case(string)

        # masking / redaction
        elif inst.startswith("redact("):
            args = self._dispatch_args(inst, "redact(")
            string = self.eval(args[0].strip(), {}, self.variables)
            target = self.eval(args[1].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.redact()"):
                return
            return StringToolkit.redact(string, target)
        elif inst.startswith("mask_emails("):
            args = self._dispatch_args(inst, "mask_emails(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.mask_emails()"):
                return
            return StringToolkit.mask_emails(string)
        elif inst.startswith("mask_urls("):
            args = self._dispatch_args(inst, "mask_urls(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.mask_urls()"):
                return
            return StringToolkit.mask_urls(string)
        elif inst.startswith("mask_numbers("):
            args = self._dispatch_args(inst, "mask_numbers(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.mask_numbers()"):
                return
            return StringToolkit.mask_numbers(string)

        # formatting
        elif inst.startswith("wrap("):
            args = self._dispatch_args(inst, "wrap(")
            string = self.eval(args[0].strip(), {}, self.variables)
            width = self.eval(args[1].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.wrap()"):
                return
            if not self._type_check(width, int, "int", "string.wrap()"):
                return
            return StringToolkit.wrap(string, width)
        elif inst.startswith("indent("):
            args = self._dispatch_args(inst, "indent(")
            string = self.eval(args[0].strip(), {}, self.variables)
            width = self.eval(args[1].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.indent()"):
                return
            if not self._type_check(width, int, "int", "string.indent()"):
                return
            return StringToolkit.indent(string, width)
        elif inst.startswith("dedent("):
            args = self._dispatch_args(inst, "dedent(")
            string = self.eval(args[0].strip(), {}, self.variables)
            width = self.eval(args[1].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.dedent()"):
                return
            if not self._type_check(width, int, "int", "string.dedent()"):
                return
            return StringToolkit.dedent(string, width)
        elif inst.startswith("align_left("):
            args = self._dispatch_args(inst, "align_left(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.align_left()"):
                return
            width = self.eval(args[1].strip(), {}, self.variables) if len(args) > 1 else None
            return StringToolkit.align_left(string, width)
        elif inst.startswith("align_right("):
            args = self._dispatch_args(inst, "align_right(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.align_right()"):
                return
            width = self.eval(args[1].strip(), {}, self.variables) if len(args) > 1 else None
            return StringToolkit.align_right(string, width)
        elif inst.startswith("align_center("):
            args = self._dispatch_args(inst, "align_center(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.align_center()"):
                return
            width = self.eval(args[1].strip(), {}, self.variables) if len(args) > 1 else None
            return StringToolkit.align_center(string, width)
        elif inst.startswith("box("):
            args = self._dispatch_args(inst, "box(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.box()"):
                return
            return StringToolkit.box(string)
        elif inst.startswith("column("):
            args = self._dispatch_args(inst, "column(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.column()"):
                return
            split_by = self.eval(args[1].strip(), {}, self.variables) if len(args) > 1 else ","
            return StringToolkit.column(string, split_by)
        elif inst.startswith("justify("):
            args = self._dispatch_args(inst, "justify(")
            string = self.eval(args[0].strip(), {}, self.variables)
            width = self.eval(args[1].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.justify()"):
                return
            if not self._type_check(width, int, "int", "string.justify()"):
                return
            return StringToolkit.justify(string, width)
        elif inst.startswith("number_lines("):
            args = self._dispatch_args(inst, "number_lines(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.number_lines()"):
                return
            start = self.eval(args[1].strip(), {}, self.variables) if len(args) > 1 else 1
            return StringToolkit.number_lines(string, start)
        elif inst.startswith("replace_between("):
            args = self._dispatch_args(inst, "replace_between(")
            string = self.eval(args[0].strip(), {}, self.variables)
            enc1 = self.eval(args[1].strip(), {}, self.variables)
            enc2 = self.eval(args[2].strip(), {}, self.variables)
            replacement = self.eval(args[3].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.replace_between()"):
                return
            return StringToolkit.replace_between(string, enc1, enc2, replacement)

        # encoding / decoding
        elif inst.startswith("base64_encode("):
            args = self._dispatch_args(inst, "base64_encode(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.base64_encode()"):
                return
            return StringToolkit.base64_encode(string)
        elif inst.startswith("base64_decode("):
            args = self._dispatch_args(inst, "base64_decode(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.base64_decode()"):
                return
            try:
                return StringToolkit.base64_decode(string)
            except Exception:
                self.error(70, f"string.base64_decode() - `{string}` is not valid base64")
                return
        elif inst.startswith("hex_encode("):
            args = self._dispatch_args(inst, "hex_encode(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.hex_encode()"):
                return
            return StringToolkit.hex_encode(string)
        elif inst.startswith("hex_decode("):
            args = self._dispatch_args(inst, "hex_decode(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.hex_decode()"):
                return
            try:
                return StringToolkit.hex_decode(string)
            except Exception:
                self.error(70, f"string.hex_decode() - `{string}` is not valid hex")
                return
        elif inst.startswith("url_encode("):
            args = self._dispatch_args(inst, "url_encode(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.url_encode()"):
                return
            return StringToolkit.url_encode(string)
        elif inst.startswith("url_decode("):
            args = self._dispatch_args(inst, "url_decode(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.url_decode()"):
                return
            return StringToolkit.url_decode(string)
        elif inst.startswith("html_encode("):
            args = self._dispatch_args(inst, "html_encode(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.html_encode()"):
                return
            return StringToolkit.html_encode(string)
        elif inst.startswith("html_decode("):
            args = self._dispatch_args(inst, "html_decode(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.html_decode()"):
                return
            return StringToolkit.html_decode(string)

        # ciphers
        elif inst.startswith("rot13("):
            args = self._dispatch_args(inst, "rot13(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.rot13()"):
                return
            return StringToolkit.rot13(string)
        elif inst.startswith("atbash("):
            args = self._dispatch_args(inst, "atbash(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.atbash()"):
                return
            return StringToolkit.atbash(string)
        elif inst.startswith("reverse_words("):
            args = self._dispatch_args(inst, "reverse_words(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.reverse_words()"):
                return
            return StringToolkit.reverse_words(string)
        elif inst.startswith("bacon("):
            args = self._dispatch_args(inst, "bacon(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.bacon()"):
                return
            decode = self.eval(args[1].strip(), {}, self.variables) if len(args) > 1 else False
            return StringToolkit.bacon(string, decode)

        # corrections
        elif inst.startswith("detect_typo("):
            args = self._dispatch_args(inst, "detect_typo(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.detect_typo()"):
                return
            return StringToolkit.detect_typo(string)
        elif inst.startswith("fuzzy_search("):
            args = self._dispatch_args(inst, "fuzzy_search(")
            string = self.eval(args[0].strip(), {}, self.variables)
            choices = self.eval(args[1].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.fuzzy_search()"):
                return
            if not self._type_check(choices, (list, tuple), "list", "string.fuzzy_search()"):
                return
            threshold = self.eval(args[2].strip(), {}, self.variables) if len(args) > 2 else 0.6
            return StringToolkit.fuzzy_search(string, choices, threshold)

        # unicode
        elif inst.startswith("unicode_info("):
            args = self._dispatch_args(inst, "unicode_info(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.unicode_info()"):
                return
            return StringToolkit.unicode_info(string)
        elif inst.startswith("unicode_name("):
            args = self._dispatch_args(inst, "unicode_name(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.unicode_name()"):
                return
            return StringToolkit.unicode_name(string)
        elif inst.startswith("codepoints("):
            args = self._dispatch_args(inst, "codepoints(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.codepoints()"):
                return
            return StringToolkit.codepoints(string)
        elif inst.startswith("from_codepoints("):
            args = self._dispatch_args(inst, "from_codepoints(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.from_codepoints()"):
                return
            try:
                return StringToolkit.from_codepoints(string)
            except Exception:
                self.error(70, f"string.from_codepoints() - `{string}` is not a valid codepoint list")
                return
        elif inst.startswith("normalize_unicode("):
            args = self._dispatch_args(inst, "normalize_unicode(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.normalize_unicode()"):
                return
            form = self.eval(args[1].strip(), {}, self.variables) if len(args) > 1 else "NFC"
            try:
                return StringToolkit.normalize_unicode(string, form)
            except Exception:
                self.error(70, f"string.normalize_unicode() - `{form}` is not a valid unicode normalization form")
                return
        elif inst.startswith("remove_accents("):
            args = self._dispatch_args(inst, "remove_accents(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.remove_accents()"):
                return
            return StringToolkit.remove_accents(string)
        elif inst.startswith("is_emoji("):
            args = self._dispatch_args(inst, "is_emoji(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.is_emoji()"):
                return
            return StringToolkit.is_emoji(string)
        elif inst.startswith("emoji_count("):
            args = self._dispatch_args(inst, "emoji_count(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.emoji_count()"):
                return
            return StringToolkit.emoji_count(string)
        elif inst.startswith("graphemes("):
            args = self._dispatch_args(inst, "graphemes(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.graphemes()"):
                return
            return StringToolkit.graphemes(string)

        # statistics
        elif inst.startswith("stats("):
            args = self._dispatch_args(inst, "stats(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.stats()"):
                return
            return StringToolkit.stats(string)

        # diffs
        elif inst.startswith("diff_lines("):
            args = self._dispatch_args(inst, "diff_lines(")
            s1 = self.eval(args[0].strip(), {}, self.variables)
            s2 = self.eval(args[1].strip(), {}, self.variables)
            if not self._type_check(s1, str, "str", "string.diff_lines()"):
                return
            if not self._type_check(s2, str, "str", "string.diff_lines()"):
                return
            return StringToolkit.diff_lines(s1, s2)
        elif inst.startswith("diff_words("):
            args = self._dispatch_args(inst, "diff_words(")
            s1 = self.eval(args[0].strip(), {}, self.variables)
            s2 = self.eval(args[1].strip(), {}, self.variables)
            if not self._type_check(s1, str, "str", "string.diff_words()"):
                return
            if not self._type_check(s2, str, "str", "string.diff_words()"):
                return
            return StringToolkit.diff_words(s1, s2)
        elif inst.startswith("diff_chars("):
            args = self._dispatch_args(inst, "diff_chars(")
            s1 = self.eval(args[0].strip(), {}, self.variables)
            s2 = self.eval(args[1].strip(), {}, self.variables)
            if not self._type_check(s1, str, "str", "string.diff_chars()"):
                return
            if not self._type_check(s2, str, "str", "string.diff_chars()"):
                return
            return StringToolkit.diff_chars(s1, s2)
        elif inst.startswith("patch("):
            args = self._dispatch_args(inst, "patch(")
            s1 = self.eval(args[0].strip(), {}, self.variables)
            s2 = self.eval(args[1].strip(), {}, self.variables)
            if not self._type_check(s1, str, "str", "string.patch()"):
                return
            if not self._type_check(s2, str, "str", "string.patch()"):
                return
            return StringToolkit.patch(s1, s2)

        # parsing
        elif inst.startswith("parse_kv("):
            args = self._dispatch_args(inst, "parse_kv(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.parse_kv()"):
                return
            pair_sep = self.eval(args[1].strip(), {}, self.variables) if len(args) > 1 else ";"
            kv_sep = self.eval(args[2].strip(), {}, self.variables) if len(args) > 2 else "="
            return StringToolkit.parse_kv(string, pair_sep, kv_sep)

        # validation (bool)
        elif inst.startswith("is_email("):
            args = self._dispatch_args(inst, "is_email(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.is_email()"):
                return
            return StringToolkit.is_email(string)
        elif inst.startswith("is_url("):
            args = self._dispatch_args(inst, "is_url(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.is_url()"):
                return
            return StringToolkit.is_url(string)
        elif inst.startswith("is_uuid("):
            args = self._dispatch_args(inst, "is_uuid(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.is_uuid()"):
                return
            return StringToolkit.is_uuid(string)
        elif inst.startswith("is_ipv4("):
            args = self._dispatch_args(inst, "is_ipv4(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.is_ipv4()"):
                return
            return StringToolkit.is_ipv4(string)
        elif inst.startswith("is_ipv6("):
            args = self._dispatch_args(inst, "is_ipv6(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.is_ipv6()"):
                return
            return StringToolkit.is_ipv6(string)
        elif inst.startswith("is_json("):
            args = self._dispatch_args(inst, "is_json(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.is_json()"):
                return
            return StringToolkit.is_json(string)
        elif inst.startswith("is_xml("):
            args = self._dispatch_args(inst, "is_xml(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.is_xml()"):
                return
            return StringToolkit.is_xml(string)
        elif inst.startswith("is_base64("):
            args = self._dispatch_args(inst, "is_base64(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.is_base64()"):
                return
            return StringToolkit.is_base64(string)

        # validation (dict)
        elif inst.startswith("validate_email("):
            args = self._dispatch_args(inst, "validate_email(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.validate_email()"):
                return
            return StringToolkit.validate_email(string)
        elif inst.startswith("validate_url("):
            args = self._dispatch_args(inst, "validate_url(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.validate_url()"):
                return
            return StringToolkit.validate_url(string)
        elif inst.startswith("validate_ip("):
            args = self._dispatch_args(inst, "validate_ip(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.validate_ip()"):
                return
            return StringToolkit.validate_ip(string)
        elif inst.startswith("validate_uuid("):
            args = self._dispatch_args(inst, "validate_uuid(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.validate_uuid()"):
                return
            return StringToolkit.validate_uuid(string)
        elif inst.startswith("validate_hex("):
            args = self._dispatch_args(inst, "validate_hex(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.validate_hex()"):
                return
            return StringToolkit.validate_hex(string)
        elif inst.startswith("validate_json("):
            args = self._dispatch_args(inst, "validate_json(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.validate_json()"):
                return
            return StringToolkit.validate_json(string)

        # misc
        elif inst.startswith("shuffle("):
            args = self._dispatch_args(inst, "shuffle(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.shuffle()"):
                return
            return StringToolkit.shuffle(string)
        elif inst.startswith("scramble_words("):
            args = self._dispatch_args(inst, "scramble_words(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.scramble_words()"):
                return
            return StringToolkit.scramble_words(string)
        elif inst.startswith("letter_frequency("):
            args = self._dispatch_args(inst, "letter_frequency(")
            string = self.eval(args[0].strip(), {}, self.variables)
            if not self._type_check(string, str, "str", "string.letter_frequency()"):
                return
            return StringToolkit.letter_frequency(string)

        else:
            self.error(6, inst.split("(", 1)[0])
            return None
            
            
        
        
        
        
        
    def _morse(self, text: str) -> str:
        pass
    
    def _string_proper(self, text: str) -> str:
        global au
        spell = au(lang="en")
        text = text.lower()
        text = re.sub(r"[\n\r\t]+", " ", text)
        text = re.sub(r"[^a-z0-9\s.,!?'\-]", "", text)
        text = re.sub(r"\s+([.,!?])", r"\1", text)
        while True:
            old_text = text
    
            # Remove spaces between punctuation marks
            text = re.sub(r"([.!?])\s+([.!?])", r"\1\2", text)
    
            # Any consecutive punctuation becomes ONE mark.
            # If multiple different marks occur, keep the LAST one.
            text = re.sub(
                r"[.!?]+",
                lambda m: m.group(0)[-1],
                text
            )
    
            if text == old_text:
                break
        text = re.sub(r"([.!?])([a-zA-Z0-9])", r"\1 \2", text)
        text = re.sub(r"\s+", " ", text).strip()
        words = text.split()
        corrected_words = []
    
        for word in words:
    
            match = re.match(
                r"^([^a-z0-9]*)([a-z0-9'-]+)([^a-z0-9]*)$",
                word
            )
    
            if match:
                prefix = match.group(1)
                core = match.group(2)
                suffix = match.group(3)
    
                if re.search(r"[a-z]", core):
                    core = spell(core)
    
                word = prefix + core + suffix
    
            corrected_words.append(word)
    
        text = " ".join(corrected_words)
        
        def add_number_commas(match):
            number = match.group(0)
            return f"{int(number):,}"
    
        text = re.sub(r"\b\d+\b", add_number_commas, text)
        text = re.sub(
            r"^[a-z]",
            lambda m: m.group(0).upper(),
            text
        )
        text = re.sub(
            r"([.!?]\s+)([a-z])",
            lambda m: m.group(1) + m.group(2).upper(),
            text
        )
        text = re.sub(r"\s+", " ", text).strip()
    
        return text
        
    def find(self, line, target, inner_group, outer_group, range=[0, -1]):
        """
        smart.find() - checks if target exists inside line/list/tuple/set,
        respecting inner_group/outer_group nesting, scoped to a range window.
        Reuses self.vey.special_find() directly since it now supports range.
        """
        return self.vey.special_find(line, target, inner_group, outer_group, range=range)
    
    
    def find_index(self, list_value, target, limit=-1, range=[0, -1]):
        """
        smart.find_index() - returns a list of indices in list_value
        where target occurs, scoped to range, capped at limit matches.
        """
        start, end = range
        end = len(list_value) if end == -1 else end + 1
        window = list_value[start:end]
    
        indices = []
        count = 0
        for i, item in enumerate(window):
            if limit != -1 and count >= limit:
                break
            if item == target:
                indices.append(i + start)  # offset back to original index
                count += 1
        return indices
    
    
    def find_str_index(self, line, target: list, limit=-1, range=[0, -1]):
        """
        smart.find_str_index() - scans line left to right, checking at every
        position if any substring in target matches starting there.
        Returns a single flattened list of positions (original string indices),
        capped at limit matches total, regardless of which target string hit.
        """
        start, end = range
        end = len(line) if end == -1 else end + 1
        window = line[start:end]
    
        indices = []
        count = 0
        i = 0
        while i < len(window):
            if limit != -1 and count >= limit:
                break
            matched = False
            for t in target:
                if window[i:i + len(t)] == t:
                    indices.append(i + start)  # offset back to original index
                    count += 1
                    matched = True
                    break
            i += 1
        return indices
    
    
    def replace(self, line, target_chars: list, replacement_chars: list, limit=-1, range=[0, -1]):
        """
        smart.replace() - replaces each occurrence of target_chars[i] with
        replacement_chars[i] (matched by index), scoped to range, capped at
        limit total replacements across the whole call.
        """
        if len(target_chars) != len(replacement_chars):
            # mismatched lengths, can't map 1:1
            return line
    
        start, end = range
        end = len(line) if end == -1 else end + 1
        before = line[:start]
        window = line[start:end]
        after = line[end:]
    
        count = 0
        result = ""
        i = 0
        while i < len(window):
            if limit != -1 and count >= limit:
                result += window[i:]
                break
            matched = False
            for t, r in zip(target_chars, replacement_chars):
                if window[i:i + len(t)] == t:
                    result += r
                    i += len(t)
                    count += 1
                    matched = True
                    break
            if not matched:
                result += window[i]
                i += 1
        else:
            pass  # loop finished naturally
    
        return before + result + after
    
    def strip(self, line, strip_target: list, mode="rl", limit=-1, range=[0, -1]):
        """
        smart.strip() - strips characters in strip_target from line, scoped to range.
        
        mode:
          "rl"  - strip scanning right to left
          "lr"  - strip scanning left to right (string reversed, stripped, reversed back)
          "alr" - like "lr", but mirrors enclosing pairs ( ) [ ] { } < > during the
                  reversal so they strip correctly instead of ending up backwards
        """
        start, end = range
        end = len(line) if end == -1 else end + 1
        before = line[:start]
        window = line[start:end]
        after = line[end:]
    
        mirror_pairs = {
            "(": ")", ")": "(",
            "[": "]", "]": "[",
            "{": "}", "}": "{",
            "<": ">", ">": "<",
        }
    
        def mirror_reverse(s):
            # reverses the string, swapping any enclosing pair characters
            # so they stay logically correct instead of flipped backwards
            return "".join(mirror_pairs.get(c, c) for c in reversed(s))
    
        def plain_reverse(s):
            return s[::-1]
    
        if mode == "rl":
            working = window
        elif mode == "lr":
            working = plain_reverse(window)
        elif mode == "alr":
            working = mirror_reverse(window)
        else:
            working = window  # fallback, unknown mode does nothing special
    
        count = 0
        i = 0
        result = []
        while i < len(working):
            if limit != -1 and count >= limit:
                result.append(working[i:])
                break
            if working[i] in strip_target:
                count += 1
                i += 1
                continue
            result.append(working[i])
            i += 1
        working = "".join(result)
    
        if mode == "lr":
            working = plain_reverse(working)
        elif mode == "alr":
            working = mirror_reverse(working)
    
        return before + working + after
    
    
    def find_key(self, dict_map: dict, target_key: str, value_type="any", has_value=True, range=[0, -1]):
        """
        smart.find_key() - returns a list of indices (positions within
        dict_map.keys(), as if listed via .keys()) where target_key is found,
        scoped to range, filtered by value_type and has_value.
        """
        keys = list(dict_map.keys())
        start, end = range
        end = len(keys) if end == -1 else end + 1
        window = keys[start:end]
    
        indices = []
        for i, k in enumerate(window):
            if k != target_key:
                continue
            value = dict_map[k]
            if has_value and not bool(value):
                continue  # falsy value (None, "", [], 0, False, etc.) - skip
            if value_type != "any" and type(value).__name__ != value_type:
                continue
            indices.append(i + start)  # offset back to original position
    
        return indices

    def _os_resolve(self, rel_path):
        """Resolves a path string relative to self.path (the language's own
        working directory), never Python's real process cwd."""
        return Path(self.path) / rel_path if rel_path else Path(self.path)
    
    def _os_error(self, error_type, message):
        """Manual/static error print for os operations. Doesn't use
        self.error()/error_metadata.py since library errors are injected here
        directly rather than through the numbered core error codes."""
        if not self.attempt:
            print("\033[31mTraceback(most_recent_call_back):\033[0m")
            print(f"    TB - [ File `<{self.path / Path(self.file_name).with_suffix(self.file_extension)}>` line: {self.og_c} ]")
            print(f"\n{error_type}: {message}")
        self.Errors[error_type] = True
    
    def file_type(self, file_name, multiple_reference=False):
        """
        os.file_type() - finds file(s) in self.path matching file_name
        (with or without an extension already given), returns a list of
        matching extensions (without the dot), sorted by name for a
        deterministic "first reference" / "last reference" order.
        multiple_reference=False returns only the first match (still a list).
        multiple_reference=True returns every match found.
        """
        p = Path(self.path)
        stem = Path(file_name).stem if "." in file_name else file_name
        matches = []
        for f in sorted(p.iterdir()):
            if f.is_file() and f.stem == stem:
                matches.append(f.suffix.lstrip("."))
        if not matches:
            return []
        return matches if multiple_reference else [matches[0]]

    def _os_dispatch(self, man):
        """
        Shared dispatch for the os library, used by both one_line() (bare
        statements, e.g. os.mkdir("test")) and assign_variables() (assignments,
        e.g. x = os.listdir()). Returns a value for value-producing calls,
        or None for action-only calls (mkdir, rmdir, chdir, delete, rename).
        """
        if man.startswith("mkdir(") and man.endswith(")"):
            args = man[6:-1].strip()
            target = self.eval(args, {}, self.variables, from_lib=True)
            p = self._os_resolve(target)
            try:
                p.mkdir()
            except FileExistsError:
                self._os_error("FileExistsError", f"Directory `{target}` already exists")
            except FileNotFoundError:
                self._os_error("FileNotFoundError", f"Parent directory for `{target}` does not exist")
            return None
    
        elif man.startswith("listdir("):
            args = man[8:-1].strip()
            target = self.eval(args, {}, self.variables, from_lib=True) if args else None
            p = self._os_resolve(target)
            try:
                return [f.name for f in sorted(p.iterdir())]
            except FileNotFoundError:
                self._os_error("FileNotFoundError", f"Directory `{target}` does not exist")
                return []
    
        elif man.startswith("exists(") and man.endswith(")"):
            args = man[7:-1].strip()
            target = self.eval(args, {}, self.variables, from_lib=True)
            return self._os_resolve(target).exists()
    
        elif man.startswith("isfile(") and man.endswith(")"):
            args = man[7:-1].strip()
            target = self.eval(args, {}, self.variables, from_lib=True)
            return self._os_resolve(target).is_file()
    
        elif man.startswith("isdir(") and man.endswith(")"):
            args = man[6:-1].strip()
            target = self.eval(args, {}, self.variables, from_lib=True)
            return self._os_resolve(target).is_dir()
    
        elif man.startswith("rmdir(") and man.endswith(")"):
            args = man[6:-1].strip()
            target = self.eval(args, {}, self.variables, from_lib=True)
            p = self._os_resolve(target)
            try:
                p.rmdir()
            except FileNotFoundError:
                self._os_error("FileNotFoundError", f"Directory `{target}` does not exist")
            except OSError:
                self._os_error("OSError", f"Directory `{target}` is not empty")
            return None
    
        elif man.startswith("chdir(") and man.endswith(")"):
            args = man[6:-1].strip()
            target = self.eval(args, {}, self.variables, from_lib=True)
            new_path = self._os_resolve(target)
            if not new_path.is_dir():
                self._os_error("FileNotFoundError", f"Directory `{target}` does not exist")
            else:
                # reserved-key convention: veyl.py consumes and deletes this
                # after each library call to propagate self.path back to the
                # live VEY instance (see execute_functions / assign_variable)
                self.variables["$<<new_path>>"] = str(new_path.resolve())
            return None
    
        elif man.startswith("delete(") and man.endswith(")"):
            args = man[7:-1].strip()
            target = self.eval(args, {}, self.variables, from_lib=True)
            p = self._os_resolve(target)
            if not p.exists():
                self._os_error("FileNotFoundError", f"File `{target}` does not exist")
            elif p.is_dir():
                self._os_error("IsADirectoryError", f"`{target}` is a directory, use os.rmdir() instead")
            else:
                p.unlink()
            return None
    
        elif man.startswith("rename(") and man.endswith(")"):
            args = man[7:-1].strip()
            args = self.special_split(args, ",", ("'", '"', "(", "[", "{"), ("'", '"', ")", "]", "}"))
            old = self.eval(args[0].strip(), {}, self.variables, from_lib=True)
            new = self.eval(args[1].strip(), {}, self.variables, from_lib=True)
            old_p = self._os_resolve(old)
            new_p = self._os_resolve(new)
            if not old_p.exists():
                self._os_error("FileNotFoundError", f"File `{old}` does not exist")
            else:
                old_p.rename(new_p)
            return None
    
        elif man.startswith("name("):
            return os.name
    
        elif man.startswith("system(") and man.endswith(")"):
            args = man[7:-1].strip()
            command = self.eval(args, {}, self.variables, from_lib=True)
            return os.system(command)
    
        elif man.startswith("cpu_count("):
            return os.cpu_count()
    
        elif man.startswith("file_type(") and man.endswith(")"):
            args = man[10:-1].strip()
            args = self.special_split(args, ",", ("'", '"', "(", "[", "{"), ("'", '"', ")", "]", "}"))
            file_name = self.eval(args[0].strip(), {}, self.variables, from_lib=True)
            multiple_reference = False
            if len(args) >= 2:
                multiple_reference = self.eval(args[1].strip(), {}, self.variables, from_lib=True)
            return self.file_type(file_name, multiple_reference)
    
        elif man.startswith("getcwd("):
            return str(self.path)
    
        return None
    
    def get_injections(self):
        """
        Metadata describing methods this library wants veyl.py's execution
        loop to invoke directly, outside the normal instruction-dispatch path.
        Keyed by name; each entry holds the bound method and the names of any
        extra arguments it needs beyond what __init__ already captured via
        **self.__dict__ (which covers most live VEY state already).
        """
        return {
            "clear_debug_screen": {
                "method": self.clear_debug_screen,
                "args": []
            },
            "render_debug_interface": {
                "method": self.render_debug_interface,
                "args": ["instruction"]
            }
        }
    
    def clear_debug_screen(self):
        if self.debug or self.adv_debug:
            print("\033c", end="")
    
    def _debug_instruction_type(self, instruction):
        stripped = instruction.strip()
        if stripped.startswith("class"):
            return "class definition"
        if stripped.startswith(("public func", "private func")):
            return "function definition"
        if "=" in stripped and not any(op in stripped for op in ["==", "!=", "<=", ">="]) \
                and not stripped.startswith(("if", "while", "else")):
            return "variable assignment"
        return "keyword"
    
    def _debug_assignment_change(self, instruction):
        if "=" not in instruction:
            return {}
        left = instruction.split("=", 1)[0].strip()
        names = [n.strip() for n in left.split(",")]
        return {n: self.variables[n] for n in names if n in self.variables}
    
    def _print_debug(self, instruction):
        print("\n=== DEBUG ===")
        print(f"Instruction : {instruction}")
        print(f"Count       : {self.cnt}  (og_c: {self.og_c})")
        print(f"Func scope  : {self.current_func if self.in_func else '<module>'}")
        print(f"Class scope : {self.in_class[0] if self.in_class[1] else None}")
        itype = self._debug_instruction_type(instruction)
        print(f"Instr type  : {itype}")
        if itype == "variable assignment":
            for name, val in self._debug_assignment_change(instruction).items():
                print(f"  {name} -> {val!r}")
        print("=============")
    
    def _print_adv_debug(self, instruction):
        print("\n=== ADV DEBUG ===")
        print(f"Instruction : {instruction}")
        print(f"Count       : {self.cnt}  (og_c: {self.og_c})")
        print(f"Func scope  : {self.current_func if self.in_func else '<module>'}")
        print(f"Class scope : {self.in_class[0] if self.in_class[1] else None}")
        itype = self._debug_instruction_type(instruction)
        print(f"Instr type  : {itype}")
        if itype == "variable assignment":
            for name, val in self._debug_assignment_change(instruction).items():
                print(f"  {name} -> {val!r}")
    
        print(f"\nFile        : {self.path / Path(self.file_name).with_suffix(self.file_extension)}")
    
        print("\n-- Instructions --")
        for i, line in enumerate(self.Instructions):
            prefix = "> " if i == self.cnt else "- "
            print(f"{prefix}{line}")
    
        print("\n-- Variables --")
        for name, value in self.variables.items():
            const_state = self.constants[name][0] if hasattr(self, "constants") and name in self.constants else None
            print(f"  {name} = {value!r}  (const: {const_state})")
    
        print("\n-- Modules --")
        for imported, name in zip(self.library, list(self.library_name.values())):
            injected = self.nplibs[imported] if imported in self.nplibs.keys() else None
            print(f"  {name:<10} | {imported:<10} | {injected}")
    
        print("\n-- Functions --")
        print(f"  {list(self.functions.keys())}")
    
        print("\n-- Classes --")
        print(f"  {list(self.classes.keys())}")
    
        print("\n-- Flags --")
        print(f"  in_class : {self.in_class}")
        print(f"  attempt  : {self.attempt}")
        print(f"  in_func  : {self.in_func}")
        print(f"  is_pub   : {self.is_pub}")
        print(f"  is_priv  : {self.is_priv}")
        print("==================")
    
    def render_debug_interface(self, instruction):
        if self.adv_debug:
            self._print_adv_debug(instruction)
            time.sleep(self.adv_debug_wait)
        elif self.debug:
            self._print_debug(instruction)
            time.sleep(self.debug_wait)