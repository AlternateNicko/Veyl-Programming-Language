import sys
from pathlib import Path
import json

class handle:
    def __init__(self, data):
        self.__dict__ = data
        with open("VeylPL/errormd.json", "r") as file:
            self.meta = json.load(file)
            # this is a file that contains each error codes and outputs.
    
    def stderr(self, code, arg1=None, arg2=None, arg3=None):
        # code: error code based on what error type it is
        # arg1: what argument is needed in response
        # arg2: secondary argument (None if not needed based on error)
        
        # all arguments used MUST be arg1 and arg2 aswell, misspelled variables throws out an error aswell

        if not self.attempt:
            code = str(code)
            if self.cause_raise:
                raise VeylInternalSystemError(f"[Error type: {self.meta[code]['error']}] [Error code: {code}]\nThis is an built in error handling for python, only run by an external API access")
            print("\033[31mTraceback(most_recent_call_back):\033[0m")
            
            for i in self.traceback:
                print(f"    TB - [ File `<{self.path / Path(self.file_name).with_suffix(self.file_extension)}>` line: {self.traceback[i]}, in {i} ],")
            print(f"    TB - [ File `<{self.path / Path(self.file_name).with_suffix(self.file_extension)}>` TB found > line [{self.og_c}]: {self.Instructions[self.cnt]} in {i} ]")
            print()
            if arg1 is None and arg2 is None:
                response = self.meta[code]["response"]
            elif arg2 is None and arg3 is None and "{arg1}" in self.meta[code]:
                response = self.meta[code]["response"].format(arg1=arg1)
            elif arg3 is None and "{arg1}" in self.meta[code] and "{arg2}" in self.meta[code]:
                response = self.meta[code]["response"].format(arg1=arg1, arg2=arg2)
            else:
                response = self.meta[code]["response"].format(arg1=arg1, arg2=arg2, arg3=arg3)
            print(response)
            self.Errors[self.meta[code]["error"]] = True
            print("EC", code)
        return self.Errors