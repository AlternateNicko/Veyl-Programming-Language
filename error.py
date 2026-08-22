import sys
from pathlib import Path
import json

class handle:
    def __init__(self, Instructions, attempt, Errors, traceback, path, file_name, file_extension, og_c, cnt, **kwargs):
        self.attempt = attempt
        self.Errors = Errors
        self.Instructions = Instructions
        self.traceback = traceback
        self.path = path
        self.file_name = file_name
        self.file_extension = file_extension
        self.og_c = og_c
        self.cnt = cnt
        with open("VeylPL/errormd.json", "r") as file:
            self.meta = json.load(file)
            # this is a file that contains each error codes and outputs.
    
    def stderr(self, code, arg1=None, arg2=None, arg3=None):
        # code: error code based on what error type it is
        # arg1: what argument is needed in response
        # arg2: secondary argument (None if not needed based on error)
        
        # all arguments used MUST be arg1 and arg2 aswell, misspelled variables throws out an error aswell

        if not self.attempt:
            print("\033[31mTraceback(most_recent_call_back):\033[0m")
            
            for i in self.traceback:
                print(f"    TB - [ File `<{self.path / Path(self.file_name).with_suffix(self.file_extension)}>` line: {self.traceback[i]}, in {i} ],")
            print(f"    TB - [ File `<{self.path / Path(self.file_name).with_suffix(self.file_extension)}>` TB found > line [{self.og_c}]: {self.Instructions[self.cnt]} in {i} ]")
            print()
            code = str(code)
            if arg1 is None and arg2 is None:
                print(self.meta[code]["response"])
            elif arg2 is None and arg3 is None and "{arg1}" in self.meta[code]:
                print(self.meta[code]["response"].format(arg1=arg1))
            elif arg3 is None and "{arg1}" in self.meta[code] and "{arg2}" in self.meta[code]:
                print(self.meta[code]["response"].format(arg1=arg1, arg2=arg2))
            else:
                print(self.meta[code]["response"].format(arg1=arg1, arg2=arg2, arg3=arg3))
            self.Errors[self.meta[code]["error"]] = True
            print("EC", code)
        return self.Errors