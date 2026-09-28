import sys
from pathlib import Path
import json

# PLACEHOLDER FOR COPY/PASTE
#: {
#                "response": 
#                "error":
#                "catchable":
#            },

class handle:
    def __init__(self, data):
        self.__dict__ = data
        self.meta = {
            # ALL OF THE FOLLOWING ERROR CODES FROM 1-70 ARE PRE EXISTING ERROR CODES BEFORE 1.0 5
            # ERROR CODES ABOVE IT ARE UPDATED/ADDED ERRORS TO THE PROGRAMMING LANGUAGE
            # main important errors
            1: {
                "response": "SyntaxError: Instruction `{arg1}` is not a valid syntax",
                "error": "SyntaxError",
                "catchable": False
            },
            2: {
                "response": "ValueError: Give value is invalid",
                "error": "ValueError",
                "catchable": True
            },
            3: {
                "response": "TypeError: Invalid type for instruction `{arg1}`",
                "error": "TypeError",
                "catchable": True
            },
            4: {
                "response": "ZeroDivisionError: Cannot divide from 0",
                "error": "ZeroDivisionError",
                "catchable": True
            },
            5: {
                "response": "ModuleError: Module `{arg1}` is not found",
                "error": "ModuleError",
                "catchable": False
            },
            6: {
                "response": "SyntaxError: Given built in function `{arg1}` is not found",
                "error": "SyntaxError",
                "catchable": False
            },
            7: {
                "response": "MemoryError: Maximum memory is reached",
                "error": "MemoryError",
                "catchable": True
            },
            8: {
                "response": "SyntaxError: Built in method `{arg1}` is not found",
                "error": "SyntaxError",
                "catchable": False
            },
            9: {
                "response": "SyntaxError: No starting curly braces `{` at the start of an code block",
                "error": "SyntaxError",
                "catchable": False
            },
            10: {
                "response": "ParsingError: This is mostly Veyl's' source code fault and not a problem within your Veyl program",
                "error": "ParsingError",
                "catchable": False
            },
            # Errors from keywords
            11: {
                "response":  "TypeError: Expected value type of condition is `bool` but got `{arg1}`",
                "error": "TypeError",
                "catchable": True
            },
            12: {
                "response": "TypeError: Function `{arg1}` takes {arg2} amount of arguments, but {arg3} is given",
                "error": "TypeError",
                "catchable": True
            },
            13: {
                "response": "TypeError: Class method `{arg1}` takes {arg2} amount of arguments, but {arg3} is given",
                "error": "TypeError",
                "catchable": True
            },
            14: {
                "response": "IndexError: Length of `{arg1}` is `{arg2}` but `{arg3}` is out of range",
                "error": "IndexError",
                "catchable": True
            },
            15: {
                "response": "TypeError: Given variable `{arg1}` is not a list -> type `{arg2}`",
                "error": "TypeError",
                "catchable": True
            },
            16: {
                "response": "NameError: Inherited parent class `{arg1}` is not found in child class `{arg2}`",
                "error": "NameError",
                "catchable": True
            },
            17: {
                "response": "NameError: Method `{arg1}` is not found with in class `{arg2}",
                "error": "NameError",
                "catchable": True
            },
            18: {
                "response": "NameError: Name `{arg1}` is not a defined variable",
                "error": "NameError",
                "catchable": True
            },
            19: {
                "response": "SyntaxError: Syntax `break` is currently not inside a loop",
                "error": "SyntaxError",
                "catchable": False
            },
            20: {
                "response": "SyntaxError: Syntax `continue` is currently not inside a loop",
                "error": "SyntaxError",
                "catchable": False
            },
            21: {
                "response": "NameError: Name `{arg1}` is not a defined global variable",
                "error": "NameError",
                "catchable": True
            },
            22: {
                "response": "SyntaxError: Invalid use case of `else if` syntax, no if-statement starting line",
                "error": "SyntaxError",
                "catchable": False
            },
            23: {
                "response": "SyntaxError: invalid else statement syntax use, no if and/or else if statement use before else",
                "error": "SyntaxError",
                "catchable": False
            },
            24: {
                "response": "NameError: Error name `{arg1}` is not an available error name",
                "error": "NameError",
                "catchable": True
            },
            25: {
                "response": "SyntaxError: Invalid catch syntax, no attempt statement was found before catch was parsed",
                "error": "SyntaxError",
                "catchable": False
            },
            26: {
                "response": 'SyntaxError: Invalid name for error `{arg1}`, given must end with a "Error" suffix',
                "error": "SyntaxError",
                "catchable": False
            },
            27: {
                "response": "SyntaxError: Invalid given arguments for `throw` keyword",
                "error": "SyntaxError",
                "catchable": False
            },
            28: {
                "response": "ModuleError: Cannot access directory `{arg1}`, it's not an available directory, perhaps try a different directory",
                "error": "ModuleError",
                "catchable": True
            },
            29: {
                "response": "ModuleError: Module `{arg1}` is not found",
                "error": "ModuleError",
                "catchable": True
            },
            30: {
                "response": "SyntaxError: Keyword `rename` requires `as` to split both library and renamed library name, but got `{arg1}`",
                "error": "SyntaxError",
                "catchable": False
            },
            31: {
                "response": "SyntaxError: Cannot convert `{arg1}` to `{arg2}` due to containing a special character",
                "error": "SyntaxError",
                "catchable": False
            },
            32: {
                "response": "NameError: Given host `{arg1}` is not a variable",
                "error": "NameError",
                "catchable": True
            },
            33: {
                "response": "NameError: Name `{arg1}` is not a defined host variable",
                "error": "NameError",
                "catchable": True
            },
            34: {
                "response": "NameError: Name `{arg1}` is not defined with in `{arg2}` syncronization group",
                "error": "NameError",
                "catchable": True
            },
            35: {
                "response": "TypeError: No such file type named `{arg1}`",
                "error": "TypeError",
                "catchable": True
            },
            36: {
                "response": "ValueError: Name `{arg1}` contains a special character the function couldn't support",
                "error": "ValueError",
                "catchable": True
            },
            # Built In Functions
            37: {
                "response": "ValueError: Value `{arg1}` cannot be evaluated",
                "error": "ValueError",
                "catchable": True
            },
            38: {
                "response": "TypeError: Second given argument to sort() is not a boolean value",
                "error": "TypeError",
                "catchable": True
            },
            39: {
                "response": "TypeError: sort() expected 2 arguments, but got `{arg1}` arguments instead",
                "error": "TypeError",
                "catchable": True
            },
            40: {
                "response": "TypeError: sort() 1st given argument is not a list",
                "error": "TypeError",
                "catchable": True
            },
            41: {
                "response": "ValueError: Given value `{arg1}` is not a list",
                "error": "ValueError",
                "catchable": True
            },
            42: {
                "response": "TypeError: Expected arguments for dict() are `2` but got `{arg1}`",
                "error": "TypeError",
                "catchable": True
            },
            43: {
                "response": "TypeError: Both arguments must be at the same length",
                "error": "TypeError",
                "catchable": True
            },
            44: {
                "response": "ValueError: `{arg1}` is an invalid number system type",
                "error": "ValueError",
                "catchable": True
            },
            45: {
                "response": "SyntaxError: Invalid parameter for num() function",
                "error": "SyntaxError",
                "catchable": False
            },
            46: {
                "response": "ValueError: Cannot print out content `{arg1}`",
                "error": "ValueError",
                "catchable": True
            },
            47: {
                "response": "TypeError: range() 1st argument is not a interger",
                "error": "TypeError",
                "catchable": True
            },
            48: {
                "response": "TypeError: range() 2nd argument `{arg1}` is not an interger",
                "error": "TypeError",
                "catchable": True
            },
            49: {
                "response": "TypeError: range() 3rd argument `{arg1}` is not an interger",
                "error": "TypeError",
                "catchable": True
            },
            # Methods
            50: {
                "response": "ValueError: Can't push variable as it is not a list",
                "error": "ValueError",
                "catchable": True
            },
            51: {
                "response": "TypeError: Cannot evaluate expression `{arg1}`",
                "error": "TypeError",
                "catchable": True
            },
            52: {
                "response": "TypeError: Given variable or value type is not a set",
                "error": "TypeError",
                "catchable": True
            },
            53: {
                "response": "ValueError: The data type given of the variable `{arg1}` -> `{arg2}` is not a set",
                "error": "ValueError",
                "catchable": True
            },
            54: {
                "response": "SyntaxError: cap() method doesn't support any arguments",
                "error": "SyntaxError",
                "catchable": False
            },
            55: {
                "response": "TypeError: Given value `{arg1}` is not a string",
                "error": "TypeError",
                "catchable": True
            },
            56: {
                "response": "TypeError: low() method doesn't expext an argument, but `{arg1}` is given",
                "error": "TypeError",
                "catchable": True
            },
            57: {
                "response": "TypeError: as() method expected a string argument, not `{arg1}`",
                "error": "TypeError",
                "catchable": True
            },
            58: {
                "response": "ValueError: `{arg1}` can't be converted into `{arg2}`",
                "error": "ValueError",
                "catchable": True
            },
            59: {
                "response": "SyntaxError: Invalid expression of pop() method !-> `{arg1}`",
                "error": "SyntaxError",
                "catchable": False
            },
            60: {
                "response": "IndexError: pop() method index is out of range",
                "error": "IndexError",
                "catchable": True
            },
            61: {
                "response": "TypeError: `{arg1}` is not a list" ,
                "error": "TypeError",
                "catchable": True
            },
            # Calling Errors
            62: {
                "response": "NameError: Name `{arg1}` is not a defined class",
                "error": "NameError",
                "catchable": True
            },
            63: {
                "response": "NameError: Name `{arg1}` is not a defined function",
                "error": "NameError",
                "catchable": True
            },
            64: {
                "response": "NameError: Name `{arg1}` is not a defined class method for `{arg2}`",
                "error": "NameError",
                "catchable": True
            },
            65: {
                "response": "LocalBoundError: Function `{arg1}` cannot be access within the local function scope",
                "error": "LocalBoundError",
                "catchable": True
            },
            66: {
                "response": "TypeError: Given argument `{arg1}` can't be passed through to `{arg2}`",
                "error": "TypeError",
                "catchable": True
            },
            # Others
            67: {
                "response": "TypeError: `{arg1}` cannot be created without an ending `{arg2}` bracket/parenthesis",
                "error": "TypeError",
                "catchable": True
            },
            68: {
                "response": "SyntaxError: {arg1}",
                "error": "SyntaxError",
                "catchable": False
            },
            69: {
                "response": "TypeError: {arg1}",
                "error": "TypeError",
                "catchable": True
            },
            70: {
                "response": "ValueError: {arg1}",
                "error": "ValueError",
                "catchable": True
            },
            # Newly added, 70 and above
            71: {
                "response": "AccessError: Method `{arg1}` in class `{arg2}` is private and cannot be called from outside the class",
                "error": "AccessError",
                "catchable": False
            },
            72: {
                "response": "SyntaxError: Function `{arg1}` has an invalid parameter name `{arg2}`",
                "error": "SyntaxError",
                "catchable": False
            },
            73: {
                "response": "FileNotFoundError: File `{arg1}` does not exist",
                "error": "FileNotFoundError",
                "catchable": True
            },
            74: {
                "response": "SyntaxError: Given index cannot be empty",
                "error": "SyntaxError",
                "catchable": False
            },
            75: {
                "response": "KeyError: Key `{arg1}` is not in dictionary map `{arg2}`",
                "error": "KeyError",
                "catchable": True
            },
            76: {
                "response": "IndexError: Slice index `{arg1}` is out of range",
                "error": "IndexError",
                "catchable": True
            },
            77: {
                "response": "TypeError: Slice index type must be intergers",
                "error": "TypeError",
                "catchable": True
            },
            78: {
                "response": "RecursionError",
                "error": "RecursionError",
                "catchable": True
            },
            79: {
                "response": "AccessError: Attribute `{arg1}` is private",
                "error": "AccessError",
                "catchable": False
            },
            80: {
                "response": "AccessError: Attribute `{arg1}` is protected",
                "error": "AccessError",
                "catchable": False
            },
            81: {
                "response": "TypeError: Can not inherit from a non-class object `{arg1}`",
                "error": "TypeError",
                "catchable": True
            },
            82: {
                "response": "CircularError: Module `{arg1}` and `{arg2}` involves indefinite circular omports with each other",
                "error": "CircularError",
                "catchable": True
            },
            83: {
                "response": "CircularError: Indefinite circular inheritance detected between class `{arg1}` and `{arg2}`",
                "error": "CircularError",
                "catchable": True
            },
            84: {
                "response": "NameError: Parent class `{arg1}` does not have the defined method `{arg2}`",
                "error": "NameError",
                "catchable": True
            },
            85: {
                "response": "SyntaxError: Invalid for loop syntax",
                "error": "SyntaxError",
                "catchable": False
            },
            86: {
                "response": "SyntaxError: Invalid while loop condition syntax",
                "error": "SyntaxError",
                "catchable": False
            },
            87: {
                "response": "TypeError: for-loops requires a iterable value, but got `{arg1}`",
                "error": "TypeError",
                "catchable": True
            },
            88: {
                "response": "ValueError: Conditions must return a boolean, but got `{arg1}`",
                "error": "ValueError",
                "catchable": True
            },
            89: {
                "response": "SyntaxError: Keyword `return` cannot be used outside a function",
                "error": "SyntaxError",
                "catchable": False
            },
            90: {
                "response": "TypeError: Return value `{arg1}` cannot be converted into return-type `{arg2}`",
                "error": "TypeError",
                "catchable": True
            },
            91: {
                "response": "SyntaxError: Invalid return expression",
                "error": "SyntaxError",
                "catchable": False
            },
            92: {
                "response": "NameError: Assignments and variable declaration requires a variable name",
                "error": "NameError",
                "catchable": True
            },
            93: {
                "response": "AccessError: Cannot modify constant variable `{arg1}`",
                "error": "AccessError",
                "catchable": False
            },
            94: {
                "response": "ValueError: Given parameter length is insuffucient for function `{arg1}`",
                "error": "ValueError",
                "catchable": True
            },
            95: {
                "response": "ValueError: Given parameter length is excessive for functuon `{arg1}`",
                "error": "ValueError",
                "catchable": True
            },
            96: {
                "response": "TypeError: split() expects a string literal argument type, but got `{arg1}`",
                "error": "TypeError",
                "catchable": True
            },
            97: {
                "response": "TypeError: replace() expects a string literal type arguments",
                "error": "TypeError",
                "catchable": True
            },
            98: {
                "response": "TypeError: Cannot modify unmutable strings `{arg1}`",
                "error": "TypeError",
                "catchable": True
            },
            99: {
                "response": "ValueError: Expected `type` value for instances 2nd argument, but got `{arg1}`",
                "error": "ValueError",
                "catchable": True
            },
            100: {
                "response": "FileExistsError: Cannot create file `{arg1}`, as file name is already in used",
                "error": "FileExistsError",
                "catchable": True
            },
            101: {
                "response": "TypeError: Function `{arg1}` expects a `{arg2}` argument type, but got `{arg3}`",
                "error": "TypeError",
                "catchable": True
            },
            102: {
                "response": "CPIMError: Custom Module Inject `{arg1}` must have a method named `process` for both the module and the interpreter to communicate and pass through each others instructions and data",
                "error": "CPIMError",
                "catchable": False
            },
            103: {
                "response": "CPIMError: This is not likely an Error by the program, but more likely a bug within the module `{arg1}` trying to handle code line `{arg2}`",
                "error": "CPIMError",
                "catchable": True
            },
            104: {
                "response": "CPIMError: Custom Module Inject `{arg1}` passed `{arg2}` back to The Veyl Library Handler that cannot be parsed",
                "error": "CPIMError",
                "catchable": True
            },
            105: {
                "response": "ValueError: Invalid literal for `{arg1}` with base 10: `{arg2}`",
                "error": "ValueError",
                "catchable": True
            },
            106: {
                "response": "ValueError: Could not convert {arg1} to `{arg2}`",
                "error": "ValueError",
                "catchable": True
            },
            107: {
                "response": "TypeError: Given value type `{arg2}` cannot be converted to `{arg1}`",
                "error": "TypeError",
                "catchable": True
            },
            108: {
                "response": "AttributeError: Attribute `{arg1}` not found in class object `{arg2}`",
                "error": "AttributeError",
                "catchable": True
            },
            109: {
                "response": "SyntaxError: Functions and Method parameters expects a ending `)` parenthesis, but got none.",
                "error": "SyntaxError",
                "catchable": False
            },
            110: {
                "response": "TypeError: Array needs 2nd argument `type` for conversion to be complete",
                "error": "TypeError",
                "catchable": True
            },
            111: {
                "response": "TypeError: Vector needs 2nd argument `type` for conversion to be complete",
                "error": "TypeError",
                "catchable": True
            },
            112: {
                "response": "TypeError: Map needs 2nd and 3rd argument `key_type` and `value_type` for conversion to be complete",
                "error": "TypeError",
                "catchable": True
            },
            113: {
                "response": "TypeError: Map needs 3rd argument `value_type` for conversion to be complete",
                "error": "TypeError",
                "catchable": True
            },
            114: {
                "response": "TypeError: Datatype {arg1} does not exist",
                "error": "TypeError",
                "catchable": True
            },
            115: {
                "response": "SSEError: Cannot create or modify `{arg1}` as a Deep System Accesor or Library Accesor SSE values",
                "error": "SSEError",
                "catchable": False
            },
            116: {
                "response": "NameError: Invalid characters found in the name while declaring a variable",
                "error": "NameError",
                "catchable": True
            },
            # 1.0.9 error refinement for bug fixes, the same version that added catchable type errors
            117: {
                "response": "AccessError: Cannot add or remove items from an constant iterable or an tuple/array",
                "error": "AccessError",
                "catchable": False
            },
            118: {
                "response": "AccessError: Cannot add or remove keys from a immutable Hash Map.",
                "error": "AccessError",
                "catchable": False
            },
            119: {
                "response": "TypeError: zip() expects an iterable argument, but got `{arg1}` type from `{arg2}`",
                "error": "TypeError",
                "catchable": True
            },
            120: {
                "response": "TypeError: cannot reverse value `{arg1}`",
                "error": "TypeError",
                "catchable": True
            },
            121: {
                "response": "TypeError: invalid {arg1} default argument `{arg2}`",
                "error": "TypeError",
                "catchable": True
            },
            122: {
                "response": "TypeError: {arg1}() expects it's iterable to have all valid interger/float value elements, but found none",
                "error": "TypeError",
                "catchable": True
            },
            123: {
                "response": "TypeError: method `{arg1}` expects a dictionary or a hash map type value, but got `{arg2}`",
                "error": "TypeError",
                "catchable": True
            },
            
            
            1000: {
                "response": "InternalError: This error is caused by an Error that was unable to handle by Veyl's current error handler, and was passed through Python exceptions\nThis is not a problem within the users code, but most likely a problem with Veyl's system itself\n\
            Error Type: {arg1}\n\
            Error Message: {arg2}",
                "error": "InternalError",
                "catchable": False
            },
            # library error metadatas goes way beyond, to error code 1001
            1001: {
                "response": "TypeError: `string` library always expects its first arguments to be a string, but got `{arg1}`",
                "error": "TypeError",
                "catchable": True
            },
            1002: {
                "response": "TypeError: `string.decode_ascii` expects a int vector for ascii numbers, not `{arg1}`",
                "error": "TypeError",
                "catchable": True
            },
            1003: {
                "response": "TypeError: `string.mask` expects an interger 2nd argument, but got `{arg1}`",
                "error": "TypeError",
                "catchable": True
            },
            1004: {
                "response": "TypeError: `string.find_encloser` expects all arguments to be string, but got either `{arg1}` or `{arg2}`",
                "error": "TypeError",
                "catchable": True
            },
            1005: {
                "response": "SyntaxError: Invalid syntax for library calls, `{arg1}`",
                "error": "SyntaxError",
                "catchable": False
            },
            1006: {
                "response": "TypeError: sys expects a string value, but got `{arg1}` type",
                "error": "TypeError",
                "catchable": True
            },
        }
        # this is a file that contains each error codes and outputs.
    
    def stderr(self, code, arg1=None, arg2=None, arg3=None):
        # code: error code based on what error type it is
        # arg1: what argument is needed in response
        # arg2: secondary argument (None if not needed based on error)
        
        # all arguments used MUST be arg1 and arg2 aswell, misspelled variables throws out an error aswell
        if not self.attempt or self.attempt and not self.meta[code]["catchable"]:
            if self.cause_raise:
                raise VeylInternalSystemError(f"[Error type: {self.meta[code]['error']}] [Error code: {code}]\nThis is an built in error handling for python, only run by an external API access")
            print("\033[31mTraceback(most_recent_call_back):\033[0m")
            
            for i in self.traceback:
                print(f"    TB - [ File `<{self.path / Path(self.file_name).with_suffix(self.file_extension)}>` line: {self.traceback[i]}, in {i} ],")
            print(f"    TB - [ File `<{self.path / Path(self.file_name).with_suffix(self.file_extension)}>` TB found > line [{self.og_c}]: {self.Instructions[self.cnt]} in {i} ]")
            print()
            if arg1 is None and arg2 is None:
                response = self.meta[code]["response"]
            elif arg2 is None and arg3 is None and "{arg1}" in self.meta[code]["response"]:
                response = self.meta[code]["response"].format(arg1=arg1)
            elif arg3 is None and "{arg1}" in self.meta[code]["response"] and "{arg2}" in self.meta[code]["response"]:
                response = self.meta[code]["response"].format(arg1=arg1, arg2=arg2)
            else:
                response = self.meta[code]["response"].format(arg1=arg1, arg2=arg2, arg3=arg3)
            print(response)
            print("EC", code)
        self.Errors[self.meta[code]["error"]] = True

        return self.Errors