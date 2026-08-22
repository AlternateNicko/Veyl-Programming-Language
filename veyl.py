import re # for spliting characters or strings without striping it completly
import ast
import operator
from typing import Any, Dict, Union, List, Tuple, Set
import os
import copy
import sys as system
import time
from pathlib import Path

# this fix circular imports
if "VeylPL" not in system.path:
    system.path.append("VeylPL")
    from built_in_libraries import libraries
    from error import handle
    import syntax_encloser

r = None
m = None
t = None
sys = None
json = None
_ASSIGN_FASTPATH_EXCLUDE = (
    '/<', 'output', 'ignore', 'quit()', 'inherit ', '<debug>',
    'load', 'break', 'continue', 'while', 'return', 'global', 'if', 'else',
    'for', 'call ', 'public', 'private', 'try', 'catch', 'throw', 'import',
    'rename', 'delete', 'sync', 'desync', 'class', 'open',
)

_UNSAFE = (
    # execution
    "eval(",
    "exec(",
    "compile(",
    "__import__(",
    "breakpoint(",

    # filesystem
    "open(",
    "'os'",
    '"os"'
    "pathlib.",
    "shutil.",

    # subprocess / external processes
    "subprocess",
    "system(",
    "popen(",

    # dynamic attribute / reflection
    "getattr(",
    "setattr(",
    "delattr(",
    "vars(",
    "globals(",
    "locals(",
    "dir(",

    # Python internals
    "__builtins__",
    "__globals__",
    "__locals__",
    "__dict__",
    "__class__",
    "__bases__",
    "__subclasses__",
    "print("
)

# Define the safe operators you want to allow
allowed_operators: Dict[type, Any] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.BitAnd: operator.and_,
    ast.BitOr: operator.or_,
    ast.BitXor: operator.xor,
    ast.LShift: operator.lshift,
    ast.RShift: operator.rshift,
    ast.Invert: operator.inv,
    ast.And: all,
    ast.Or: any,
}

class SafeEval(ast.NodeVisitor):
    """
    Made my own eval, due to problems with pythons eval() function, since the language may run python code while evaluating normal expressions
    so this is a remake of python's eval without arbitrary python code executed, all of the things eval does are in here, just without arbitrary
    """
    def __init__(self, globals: Dict[str, Any] = None, locals: Dict[str, Any] = None) -> None:
        self.globals: Dict[str, Any] = globals or {}
        self.locals: Dict[str, Any] = locals or {}

    def visit(self, node: ast.AST, line = None) -> Any:
        if isinstance(node, ast.Expression):
            return self.visit(node.body)
        elif isinstance(node, ast.BinOp):
            left = self.visit(node.left)
            right = self.visit(node.right)
            return allowed_operators[type(node.op)](left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = self.visit(node.operand)
            if isinstance(node.op, ast.UAdd):  # Unary positive
                return +operand
            elif isinstance(node.op, ast.USub):  # Unary negative
                return -operand
            return allowed_operators[type(node.op)](operand)
        elif isinstance(node, ast.Constant):  # For Python 3.8 and above
            return node.value
        elif isinstance(node, ast.Name):
            if node.id in self.locals:
                return self.locals[node.id]
            elif node.id in self.globals:
                return self.globals[node.id]
            raise NameError(f"Name `{node.id}` is not defined")
        elif isinstance(node, ast.BoolOp):
            values = [self.visit(value) for value in node.values]
            return allowed_operators[type(node.op)](values)
        elif isinstance(node, ast.Compare):
            left = self.visit(node.left)
            for operation, right in zip(node.ops, node.comparators):
                right = self.visit(right)
                if isinstance(operation, ast.Eq):
                    if left != right:
                        return False
                elif isinstance(operation, ast.NotEq):
                    if left == right:
                        return False
                elif isinstance(operation, ast.Lt):
                    if not left < right:
                        return False
                elif isinstance(operation, ast.LtE):
                    if not left <= right:
                        return False
                elif isinstance(operation, ast.Gt):
                    if not left > right:
                        return False
                elif isinstance(operation, ast.GtE):
                    if not left >= right:
                        return False
                elif isinstance(operation, ast.In):
                    if left not in right:
                        return False
                elif isinstance(operation, ast.NotIn):
                    if left in right:
                        return False
            return True
        elif isinstance(node, ast.List):
            return [self.visit(elt) for elt in node.elts]
        elif isinstance(node, ast.Tuple):
            return tuple(self.visit(elt) for elt in node.elts)
        elif isinstance(node, ast.Set):
            return {self.visit(elt) for elt in node.elts}
        elif isinstance(node, ast.Dict):
            return {self.visit(key): self.visit(value) for key, value in zip(node.keys, node.values)}
        elif isinstance(node, ast.Subscript):  # Handling list/tuple indexing
            container = self.visit(node.value)
            index = self.visit(node.slice)
            if isinstance(container, (list, tuple)) and isinstance(index, int) or isinstance(container, (dict)) and isinstance(index, (int, str)):
                return container[index]
            raise ValueError(f"INDEX `{index}` `{container}` Invalid indexing: {ast.dump(node)} line `{line}`")
        elif isinstance(node, ast.Index):  # For subscript index
            return self.visit(node.value)
        else:
            raise ValueError(f"Unsupported operation: {ast.dump(node)} line {line}")

class VEY:
    def __init__(self, instructions, special_library={}, path=None, file="vey", extension=".vey"):
        # nplibs holds dictionaries like this
        # "lib_name": module_class,
        # where module_class is the class object of that library
        
        # CONFIGURATIONS
        self.version = "1.0.6-pr" # current version
        
        self.path = Path.cwd() if path is None else path # current program directory
        self.file_name = file # name of file
        self.file_extension = extension # file extension of the file
        self.run = True # Runtime flag
        
        # LIBRARIES
        self.nplibs = special_library
        self.libraries = ["math", "time", "random", "smart", "sys", "files", "os", "debug"] # libraries, these are built ins
        self.libraries.extend(list(special_library.keys()))
        self.library = [] # library names will be appended here once they are imported
        self.nplibs_acc = {key: False for key in self.nplibs.keys()}
        
        # FOR LIBRARIES
        self.debug = False
        self.adv_debug = False
        self.debug_wait = 0
        self.adv_debug_wait = 0
        
        # IMPORTANTS
        self.Instructions = self.build_instructions(instructions) # main instruction line gets split line by line
        self.full_instructions = self.Instructions # Original constant instructions of self.Instructions
        self.raw_instructions = instructions # Untouched raw instruction line
        self.variables = {} # all the variables are stored here
        self.cnt = 0 # the main pointer to the line of code
        self.traceback = {"<module>": self.cnt} # the traceback, tracing back to where errors originate
        self.classes = {} # name: {methods: {method name: same as funcs}, variables: {name: value}, inheritence: [class name]
        self.og_c = 0 # the count, but the count where the pointer is pointingj at, and not changed by any parsing actions
        self.return_val = None # return value
        self.return_type = None # return type
        
        # EVALUATIONS / CONSTANTS
        self.bif = ["num", "input", "eval", "exec", "length", "sort", "min", "mean", "max", "median", "mode", "sum", "range", "call", "reverse", "type", "format",
            "zip", "dict", "map"
        ] # for eval to: know if the expression they are evaluating has the languages codes
        self.bim = ["cap", "low", "as", "rem", "strip", "split", "hasprefix", "hassuffix", "replace", "slice", "pop", "push", "read", "keys", "values", "items", "const",
            "unconst",
        ] # this one is for methods
        self.forbiden_chars = [" ", "'", '"', "(", ")", "[", "]", "{", "}", "~", "`", "@", "*", "+", "<", ">", "%", "#", "!", "?", ",", ":", ";", "/"] # characters forbiden to non string names
        self.datatypes = ["int", "str", "float", "bool", "vector", "array", "map", "set", "void"] # use for keywords
        
        # IDENTIFIERS
        self.current_func = "" # current function
        self.og_fname = "" # contains original function scope name or past name
        self.func_name = "" # name of current function it's inside
        
        # FLAGS
        self.in_if = False # inside an if statement
        self.if_executed = False # if an if statement is executed with the conditions being true, turns True
        self.condition = False # for the if, else if statement, turns true once their condition is also true
        self.attempt = False # for try-except, but in this language is attempt-catch, once attempting to execute a code, all errors wont print out a trace back, instead it gets catch if it matches with the error name of the catch block
        self.in_class = [None, False, None] # if the program is currently in a code, first index stores the name of the class, the second shows True if they are in a class, third is what class objecf it is (None if it's inside a class) else False
        self.breaking = False # force break out loops
        self.continuing = False # continues
        self.evals = False # if it's currently evaluating something
        self.is_return = False # for return
        self.eval_deb = False # for debug
        self.is_priv = False # private func
        self.is_pub = False # public func, both will be false if they are not inside one
        
        # COUNTERS
        self.in_smth = 0 # i forgot what this does
        self.in_block = 0 # while exiting or skipping some if and else if statement, this turns true if it's inside a code block (code blocks startimg with { and ends with })
        self.exec_fl = 0 # if it's currently executing a loop (for loop or while loops)
        self.in_func = 0 # if it's currently inside a function
        
        # METADATA'S
        self.functions = {} # where all the functions get stored, their entire code blocks, starting line, ending line, local variables, and arguments
        self.class_callers = {} # variable to object access
        self.global_var = {} # Every variables
        self.library_name = {} # where renamed library or current library names are stored
        self.name_library = {} # Vice versa
        self.sync_variables = {} # supports multiple syncronized variables instead of one
        self.func_scope = {} # contains the variables and other user defined values like functions and classes
        self.special = {} # for OOP, protected/static variables or attributes
        self.public = {} # public variables, this is permanentaly stored unless "private" intercepts it
        self.private_classes = {} # For future uses
        self.variable_info = {} # variable datatype, constant, and protected infos
        self.original_var = [] # original variable once calling a new function, the self.variables are replace with a new dictionary, and original_var stores the global variables
        self.cache = {
            "eval": {}, # for evaluation (v1.0.3)
            "func": {}, # function cache (v1.0.5)
            "class": {}, # class method cache (v1.0.5)
            "cond": {}, # for conditions (v1.0.5)
        } # the cache, mostly use for memoization, func and classes still has no use for now
        self.objects = {} # for defined variables using class objects
        self.constants = {} # assign variable names if they are constant or not, becomes False if they are assigned
        self.return_cache = {} # return cache
        self._token_lookup_cache = {}  # caches ultimate_split's first-char buckets, keyed by the token list used
        self.Errors = { # all of the errors that will show up, if one of this is True, the whole code is stop and prints a trace back where the error originated,
            'SyntaxError': False,
            'IndexError': False,
            'RecursionError': False,
            'NameError': False,
            'ZeroDivisionError': False,
            'TypeError': False,
            'KeyError': False,
            'MemoryError': False,
            'ValueError': False,
            'ModuleError': False,
            "AccessError": False,
            "LocalBoundError": False,
            'FileNoFoundError': False,
            "FileExisrsError": False,
            
            'QuitError': False # Use for quit(), doesn't throw an error message, but does stop the program without directly ending the main python program'
        }
    def build_instructions(self, source):
        instructions = []
        lines = source.split("\n")
        i = 0
        in_docstring = False
        while i < len(lines):
            raw_line = lines[i]
            if not in_docstring:
                start = self._find_docstring_marker(raw_line, '<"', respect_quotes=True)
                if start == -1:
                    new_inst = self.split_comment(raw_line)
                    if new_inst:
                        instructions.extend(new_inst)
                    i += 1
                    continue
                before = raw_line[:start]
                after = raw_line[start + 2:]
                end = self._find_docstring_marker(after, '">')
                if before.strip():
                    new_inst = self.split_comment(before)
                    if new_inst:
                        instructions.extend(new_inst)
                if end == -1:
                    # docstring isn't closed on this line, keep consuming lines
                    in_docstring = True
                    i += 1
                else:
                    # opened and closed on the same line - reprocess whatever follows
                    lines[i] = after[end + 2:]
                    continue
            else:
                end = self._find_docstring_marker(raw_line, '">')
                if end == -1:
                    # still inside the docstring, whole line is discarded
                    i += 1
                else:
                    in_docstring = False
                    lines[i] = raw_line[end + 2:]
                    continue
        return instructions

    def _find_docstring_marker(self, line, marker, respect_quotes=False):
        """
        Finds the index of a 2-char marker ('<"' or '">') in line, or -1.
        respect_quotes=True skips matches that fall inside a real ' or "
        string literal - used when scanning ordinary code for the opening
        marker. Once inside a docstring body, matches are found literally
        (respect_quotes=False), since that text is discarded, not parsed.
        """
        in_string = None
        i = 0
        while i < len(line):
            ch = line[i]
            if respect_quotes:
                if in_string:
                    if ch == in_string:
                        in_string = None
                    i += 1
                    continue
                elif ch in ("'", '"'):
                    in_string = ch
                    i += 1
                    continue
            if line[i:i + len(marker)] == marker:
                return i
            i += 1
        return -1
    
    def split_comment(self, line):
        """
        Splits one line into [code] or [code, comment], where the comment
        keeps its leading '/<'. Ignores '/<' found inside string literals
        (same behavior as the rest of the parser).
        """
        parts = self.special_split(line, "/<", ("'", '"'), ("'", '"'), limit=1)
        if len(parts) == 1:
            return [line.strip()] if line.strip() else []
        code = parts[0].strip()
        return [code] if code else None
        
    def single_eval(self, expression, globals=None, locals=None):
        # evaluates one expression
        tree = ast.parse(expression.strip(), mode='eval')
        evaluator = SafeEval(globals, locals)
        self.evals = False
        return evaluator.visit(tree.body)
                        
    
    def eval(self, expression, globals={}, locals=None, arb=True, from_lib=False, from_exp=False, from_isinstance=False):
        self.evals = True # a flag to tell the parser that is just evaluating
        # this eval has the ability to not just evaluate 1 expression, but multiple expressions, the language arbitrary codes, and more
        """Process of how eval handles an expression like
        variable = sum(var1) / length(var1) + var2 + mean(var3)
        first -> assign_variable first process the line, splits variable as "left" and the expression as "right"
        which then gets converted to "main" line after a few process
        after finding no simple matching expression, it feeds it to self.eval
        which the expression is now just sum(var1) / length(var1) + var2 + mean(var3)
        
        self.eval checks if it is a singular method (a function with a method without being too complex)
        self.eval splits the expression by "+" "-" "/" and "*", spliting each function as one
        breaking down the expression to "sum(var1)" "/" "length(var1)" "+" "var2" "+" "mean(var3)"
        then for the functions, it gets looped back to self.assigned variable, but this time as one function
        instead of multiple functions
        """
        
        # gets expression form
        if expression in self.variables.keys():
            return self.variables[expression]
        if not from_exp:
            expr = self.expression(expression)
            if expr["iseval"]:
                self.evals = False
                return self._eval_expr_result(expr, globals, locals) # This only evaluates veyl expression despite using python eval(),
                # self.expression() uses veyl approve and only syntax, doesn't include python codes'
            else:
                expression = expr["expr"]
        if from_lib:
            past_vars = copy.deepcopy(self.variables)
            self.variables = locals
        # this part processes dictionary key and values for the self.eval item processing (yes, eval uses itself)
        is_dict = self.special_find(expression, ":", ('"', "'", "(", "[", "{"), ('"', "'", ")", "]", "}"))
        if len(expression) == 2 and self.expect(expression, (("(", ")"), ("[", "]"), ("{", "}"))):
            self.evals = False
            return self.single_eval(expression, globals, locals)
        if is_dict:
            exp = self.special_split(expression, ":", ('"', "'", "(", "[", "{"), ('"', "'", ")", "]", "}"), limit=1)
            key = exp[0].strip()
            value = str(self.eval(exp[1].strip(), {}, self.variables))
            self.evals = False
            return (key, value)
        if arb:
            execution = False
            methods = False
            if self.in_class[1] and self.in_class[2] and expression in self.objects[self.in_class[2]]["variables"].keys():
                execution = True
            if "." in expression:
                istrue = self.special_find(expression, ".", ('"', "'", "(", "[", "{"), ('"', "'", ")", "]", "}"))
                pattern = r'(?<!\w)[+-]?(?:\d+\.\d+|\d+\.|\.\d+)(?!\w)'
                if bool(re.search(pattern, expression)) and istrue:
                    execution = True
                elif not bool(re.search(pattern, expression)) and istrue:
                    split_arg = expression.split(".", 1)
                    if True in [i in split_arg[1] for i in self.bim]: # double checks methods
                        execution = True
                        methods = True
            for i in self.bif: #
                if i in expression:
                    if "." + i in expression:
                        continue
                    execution = True
            if execution:
                v = False
                things = ["+", "-", "**", "*", "%", "/", "<=", ">=", "<", ">", "==", "!="]
                v = self.special_find(expression, things, ('"', "'", "(", "[", "{"), ('"', "'", ")", "]", "}"))
                # processes item expressions
                if expression.strip().startswith(("(", "[", "{")):
                    expr = expression[:1]
                    expression, cnt, eogc = self.get_items(expr, expression)
                    new = ""
                    for ex in expression:
                        new += ex
                    expression = new
                    if_item = self.special_find(expression, ",", ('"', "'", "(", "[", "{"), ('"', "'", ")", "]", "}"))
                    if expression.startswith("(") and expression.endswith(")") and not if_item:
                        expression = expression[1:-1]
                    else:
                        item_types = {
                            "[": "list",
                            "(": "tuple",
                            "{": "dictionary"
                        }
                        ending = {
                            "[": "]",
                            "(": ")",
                            "{": "}" 
                        }
                        line = expression[:1]
                        end_line = ending[line]
                        i_type = item_types[line]
                        expression = self.special_split(expression[1:-1], ",", ('"', "'", "(", "[", "{"), ('"', "'", ")", "]", "}"))
                        vals = []
                        txt = ""
                        for ex in expression:
                            if i_type == "dictionary":
                                dicts = self.eval(ex, {}, self.variables)
                                vals.append(dicts[0] + ": " + dicts[1])
                            else:
                                vals.append(str(self.eval(ex, {}, self.variables)))
                        # reconstruct
                        new = line
                        for v in vals:
                            new += v + ", "
                        new += end_line
                        expression = new
                if v:
                    org = expression
                    expression = self.ultimate_split(expression, things)
                    chars = []
                    cnt = 0
                    while cnt != len(expression):
                        if expression[cnt] in things:
                            v = expression[cnt]
                            del expression[cnt]
                            chars.append(v)
                            cnt -= 1
                        cnt += 1
                    vals = []
                    for ex in expression:
                        # please don't tell me why it is like this
                        self.assign_variable("<<temporary_variable>> = " + ex, methods) # this class method includes handling variable assignments and the functions for arbitrary
                        expression = self.variables["<<temporary_variable>>"] # the name of the variable is like this because this may delete a existing variable that may have this name
                        vals.append(str(expression))
                    del self.variables["<<temporary_variable>>"] # it deletes it
                    final = ""
                    for v, c in zip(vals, chars):
                        final += v + " " + c + " " # puts all of the evaluated expressions, arithmetic characters back to one string to be executed one last time
                    final += vals[-1]
                    expression = final
                else:
                    try:
                        if self.in_class[1] and expression in self.special[self.in_class[0]]["variables"].keys() and self.special[self.in_class[0]]["variables"][expression]:
                            name_var = expression
                            
                            if name_var in self.classes[self.in_class[0]]["variables"].keys():
                                
                                v = self.classes[self.in_class[0]]["variables"][name_var]
                                return v
                        return self.eval(expression.strip(), {}, self.variables, arb=False)
                    except Exception as e:
                        if self.in_class[1] and expression in self.special[self.in_class[0]]["variables"].keys() and self.special[self.in_class[0]]["variables"][expression]:
                            name_var = expression
                            return self.classes[self.in_class[0]]["variables"][name_var]
                        
                        self.assign_variable("<<temporary_variable>> = " + expression.strip(), methods) # if the expression doesn't contain any arithmetic characters (+ * - /), it runs this
                        expression = self.variables["<<temporary_variable>>"]
                        expression = str(expression)
                        del self.variables["<<temporary_variable>>"]
        expression = str(expression)
        try:
            tree = ast.parse(expression.strip(), mode="eval")
        except Exception as e:
            if "[]" in expression:
                self.error(74, expression)
                return
        self.evals = False
        evaluator = SafeEval(globals, locals)
        if from_lib: self.variables = past_vars
        return evaluator.visit(tree.body, expression) # final evaluator

    def _eval_expr_result(self, expr_dict, globals=None, locals=None):
        """
        Runs the "expr" field of an expression()/run_condition() result dict.
        If it's already a concrete Python value (produced by single_eval/eval
        during expression() construction), it's returned as-is - no need to
        stringify and re-parse it through eval() at all.
        If it's still source text (e.g. "5 + non_const_var"), it's run through
        a cached compile()'d code object instead of eval()'ing the raw string,
        so repeated hits (very common in loop conditions/bodies) skip Python's
        own parse+compile step and only pay for bytecode execution.
        """
        value = expr_dict["expr"]
        if not isinstance(value, str):
            return value
        elif any(c in value for c in _UNSAFE):
            self.error(37, value)
            return None
        code = expr_dict.get("compiled")
        if code is None:
            try:
                code = compile(value, "<veyl_expr>", "eval")
            except Exception:
                self.error(36)
            expr_dict["compiled"] = code
        return eval(code, globals, locals)
        
    def expression(self, exp):
        # self.eval() was written and implemented a year ago, this function was just added now for optimization and speed
        """
        Converts expressions written in veyl into a AST readable form that can be run in self.eval or instantly to evaluation
        Why did i write this?
        - because repitition of if, else if statements, while loops are slow due to recursion calls of self.eval -> self.assign_variable...

        important variables:
            self.cache
            self.constants
            self.variables
        
        can be run with either self.eval() or eval()
        this function returns a dictionary, this contains
        {
            "expr": exp, "iseval": bool, "variables": {"name": True, "name2": False}
        }
        which is then saved in self.cache
        booleans in variables means if its constant or not during it's first evaluation'
        """
        # cache loading
        if exp in self.cache["eval"].keys():
            change = True
            for v in self.cache["eval"][exp]["variables"].keys():
                if self.cache["eval"][exp]["const"][v][0] != self.constants[v][0]:
                    change = False
                    break
            if change:
                return self.cache["eval"][exp]
        
        # main parser converter
        """
        goal: Finds variables inside the expression and checks if that variable is constant or not
        constant variables: constant variables gets its values fetched immidietly into the expression,
        since it stays constant, values are never changed
        non-constants: non-constant variables never gets its values fetched since the variable is changed after evaluation
        
        if it's a simple expression after converting (like just 60 + 20, or 10 == 20) it immidietly evaluates
        only returns expression forms if only there is
        - unfetched non constant variables
        - arbitrary veyl expressions (like built ins)
        """
        iseval = False
        expression = {"expr": None, "iseval": iseval, "variables": {}, "const": copy.deepcopy(self.constants), "compiled": None}
        variables = {}
        # example: cnt == length(list), should return cnt == 60 (cnt is non constant, list is)
        identifiers = self._extract_identifiers(exp)
        if any(v in identifiers for v in self.variables.keys()):
            # uses the same technique as eval, split the expressions
            operators = ["+", "-", "**", "*", "%", "/", "<=", ">=", "<", ">", "==", "!="]
            final_exp = []
            has_built_ins = self.special_find(exp, operators, ("'", '"', "(", "{", "["), ("'", '"', ")", "}", "]"))
            if not has_built_ins:
                expression["expr"] = self.eval(exp, {}, self.variables, from_exp=True)
                expression["iseval"] = True
                var = exp
                if self.special_find(exp, ".", ("'", '"', "(", "[", "{"), ("'", '"', ")", "]", "}")):
                    var = exp.split(".", 1)[0].strip()
                    
                expression["variables"][var] = True if var in self.constants.keys() and self.constants[var][0] else False
                
            else:
                lines = self.ultimate_split(exp, operators)
                # goes through each one to check each variables
                operator = []
                cnt = 0
                # splits expressions away from operators
                while cnt != len(lines):
                    if lines[cnt] in operators:
                        operand = lines[cnt]
                        del lines[cnt]
                        operator.append(operand)
                        cnt -= 1
                    cnt += 1
                for line in lines:
                    if any(i + "(" in line for i in self.bif):
                        # tricky, since it needs to check if variable is actually constant or not while that variable is inside a parenthesis
                        # while that, there is also nested functions like median(sort(list))
                        main_line = line
                        while True:
                            line = line.split("(", 1)[1].removesuffix(")").strip() # removes function
                            if not any(i in line for i in self.bif):
                                break
                        # now checks that line if it's constant or not, if it is then evaluate main line
                        if line.strip() in self.constants.keys() and line in self.variables.keys() and self.constants[line][0]:
                            final_exp.append(str(self.eval(main_line, {}, self.variables)))
                            variables[line] = True
                        # else it loads main line
                        else:
                            final_exp.append(main_line)
                            variables[line] = False
                    elif line in self.constants.keys() and line in self.variables.keys() and self.constants[line][0]:
                        # means constant, constant = load it in
                        value = self.variables[line]
                        if isinstance(value, str) and not value.startswith(("'", '"')) and not value.endswith(("'", '"')):
                            value = "'" + value + "'"
                        final_exp.append(value)
                        variables[line] = True
                    else:
                        final_exp.append(line)
                        if line in self.variables.keys():
                            variables[line] = False
                expr = ""
                for v, c in zip(final_exp, operator):
                    
                    expr += str(v) + " " + c + " "
                expr += str(final_exp[-1])
                expression["expr"] = expr
                expression["iseval"] = has_built_ins
                expression["variables"] = variables
                
        else: # means it's instantly evaluated
            if self.expect(exp, [("'", "'"), ('"', '"')]):
                expression["expr"] = exp
            else:
                expression["expr"] = self.eval(exp, {}, self.variables, from_exp=True)
            expression["iseval"] = True
            expression["variables"] = {}
        # save to cache
        self.cache["eval"][exp] = expression
        return expression
        
    def execute(self):
        # main executer of the code, the start up
        while True:
            # Check for error
            if True in self.Errors.values() and not self.attempt:
                return
            if self.cnt >= len(self.Instructions):
                break # ends the program once the cnt reaches over the programs amount of line of code
            instruction = self.Instructions[self.cnt].strip()
            self.traceback["<module>"] = self.cnt
            if self.debug or self.adv_debug:
                self.run_injected_method("clear_debug_screen")
            if instruction is None or instruction == "ignore":
                pass
            else:
                result = self.execute_functions(instruction)
            
            if result != None:
                print(result)
                result = None
            if self.debug or self.adv_debug:
                self.run_injected_method("render_debug_interface", instruction=instruction)
            self.cnt += 1
            self.og_c += 1
        return
        
    def exec_block(self, code, count):
        # executes a code block, separate uses from the execute method
        self.cnt = 0
        ogc = self.og_c
        original = self.Instructions
        was_in = True if self.in_func else False
        ogif = self.in_if
        self.Instructions = code.split("\n")
        og_type = self.return_type
        while self.cnt < len(self.Instructions):
            # Check for errors
            if True in self.Errors.values() and not self.attempt:
                return
            instruction = self.Instructions[self.cnt].strip()
            if self.debug or self.adv_debug:
                print("\033c", end="")
            if (instruction is None
                or instruction == "pass"
                or instruction == "{"
                or instruction == "}"
            ):
                pass
            else:
                result = self.execute_functions(instruction)
                if result != None:
                    print(result)
            if self.debug or self.adv_debug:
                print("_" *27)
                print("\n" * 5)
                self.render_debug_interface(instruction)
            self.cnt += 1
            self.og_c += 1
            if self.breaking or self.continuing:
                break
            if self.in_func == 0 and was_in or self.is_return:
                break
        self.cnt = count
        self.return_type = og_type
        self.in_if = ogif
        self.og_c = ogc
        self.Instructions = original
        return
    
    def prep_exec(self, code): # prepares to execute a code block
        final = ""
        for i in code:
            final += i + "\n"
        return final
        
    # get code block helper function
    # also supports getting nested blocks, and dont need indent because of the braces (and the rest)
    def get_block(self, intent=False):
        cnt = self.cnt
        ogc = self.og_c
        if '{' in self.Instructions[cnt].strip() or "{" in self.Instructions[cnt + 1].strip():
            if '{' not in self.Instructions[cnt]:
                cnt += 1
                ogc += 1 # for brackets starting at the same line as the function definition
            if "{" in self.Instructions[cnt]:
                nested = 1
                cnt += 1
                ogc += 1
            else:
                nested = 0
            block = [] # to be returned
            while cnt < len(self.Instructions):
                line = self.Instructions[cnt].strip()
                block.append(line)
                cnt += 1
                ogc += 1
                if self.special_find(line, "{", ("'", '"', "(", "["), ('"', "'", ")", "]")):
                    nested += 1
                if self.special_find(line, "}", ("'", '"', "(", "["), ('"', "'", ")", "]")):
                    nested -= 1
                    if nested == 0: # if nested is 1 (meaning is the main code block), it will break out of the loop snd return the block
                        break
                # else, the cnt is in the code block
            # pre process the codes for ending brackets
            line = block[-1]
            if line.strip().endswith("}") and not line.strip().startswith("}"):
                block[-1] = line.strip()[:-1].strip()
            elif line.strip() == "}":
                del block[-1]
            return block, cnt, ogc
        else:    
            self.error(9)
            return [], 0
   
    def process_vars(self):
        """
        runs each loop, this updates a class variable by the current scope variable (self.variables)
        and with the new feature "sync", it is now responsible for syncing the variables with the host or group variables
        based on the sync mode, and values of the synced variables.
        There would be more uses in the near future
        """
        # multiple variable checks
        for v in self.variables.keys():
            if self.in_class[1] and v in self.special[self.in_class[0]]["variables"].keys() and self.special[self.in_class[0]]["variables"][v]:
                self.classes[self.in_class[0]]["variables"][v] = self.variables[v]
                if v not in self.classes[self.in_class[0]]["variables"]["<attr>"]:
                    self.classes[self.in_class[0]]["variables"]["<attr>"].append(v)
            if self.in_class[2] is not None and self.in_class[2] in self.objects.keys() and v in self.objects[self.in_class[2]]["variables"].keys():
                self.objects[self.in_class[2]]['variables'][v] = self.variables[v]
            if v not in self.constants.keys():
                self.constants[v] = [True, self.variables[v]]
            if v != "<dict>" and self.variables[v] != self.constants[v][1]:
                self.constants[v][0] = False
            if v not in self.variable_info.keys():
                self.variable_info[v] = {
                    "datatype": "<any>",
                    "constant": False,
                    "isprotected": False,
                    "Immutable": False
                }
            self.constants[v][1] = self.variables[v]
        # one time class variables
        if self.in_class[1] and self.in_class[2] is not None and self.in_class[2] in self.objects.keys():
            self.objects[self.in_class[2]]["variables"]["<dict>"].update(self.objects[self.in_class[2]]["variables"])
        elif self.in_class[1]:
            self.classes[self.in_class[0]]["variables"]["<dict>"].update(self.classes[self.in_class[0]]["variables"])
        
        # public variables
        self.variables.update(self.public)
        self.global_var.update(self.variables)
        
        # for sync variables
        if self.sync_variables == {}:
            return
        sync_groups = list(self.sync_variables.keys())
        for gr in sync_groups:
            group = self.sync_variables[gr].copy()
            for name in group["all"].keys():
                if name in self.variables.keys():
                    variables = {name: self.variables[name]}
                    self.sync_variables[gr]["past group value"] = self.sync_variables[gr]["group value"].copy()
                    self.sync_variables[gr]["group value"].update(variables)
                    self.sync_variables[gr]["all"].update(variables)
            if group["host"] in group["group value"].keys():
                del self.sync_variables[gr]["group value"][group["host"]]
            if group["host"] in group["past group value"].keys():
                del self.sync_variables[gr]["past group value"][group["host"]]
            if group["mode"] == "hva":
                # checks if host variables changed value
                host = group["host"]
                vars = group["group value"]
                self.sync_variables[gr]["past group value"] = vars.copy()
                host_val = self.variables[host]
                if host_val != group["past value"]:
                    new_var = {}
                    for vars in group["group"]:
                        self.variables[vars] = host_val
                        new_var[vars] = host_val
                    self.sync_variables[gr]["group value"] = new_var
                    self.sync_variables[gr]["past value"] = host_val
            elif group["mode"] == "avs":
                def sync_dict_values(d):
                    values = list(d.values())
                    first = values[0]
                
                    # Find a value that's different
                    different = None
                    for value in values[1:]:
                        if value != first:
                            different = value
                            break
                
                    if different is None:
                        return
                
                    # Copy the different value to every key
                    for key in d:
                        d[key] = different
                
                    return d
                vars = group["all"]
                self.sync_variables[gr]["past group value"] = vars.copy()
                new_dict = sync_dict_values(vars)
                self.sync_variables[gr]["group value"] = new_dict
                self.sync_variables[gr]["all"] = new_dict
                self.variables.update(new_dict)
            elif group["mode"] == "gva":
                # host changes values by their group value
                host = group["host"]
                vars = group["group value"]
                past = group["past group value"]
                host_val = self.variables[host]
                all_dict = group["all"]
                # checks if even one value matches
                value = None
                for key in vars.keys():
                    if vars[key] == past[key]:
                        continue
                    value = vars[key]
                    break
                if value is None:
                    pass
                else:
                    host_val = value
                    all_dict.update({host: host_val})
                    self.sync_variables[gr]["all"] = all_dict
                    self.variables.update(all_dict)
                    self.sync_variables[gr]["past group value"] = vars.copy()
            
    
    def get_items(self, types, line=None):
        """
        uses the same codes of self.get_block()
        except it handles lists, tuples, and dictionaries instead of code blocks
        """
        item_types = {
            "[": "list",
            "(": "tuple",
            "{": "dictionary"
        }
        ending = {
            "[": "]",
            "(": ")",
            "{": "}" 
        }
        
        item_type = item_types[types]
        item_end = ending[types]
        if line is not None and line.endswith(item_end):
            return [line], self.cnt
        cnt = self.cnt
        ogc = self.og_c
        if types in self.Instructions[cnt]:
            nested = 1
            block = [] # to be returned as items
            line = self.Instructions[cnt].strip().split("=")[1].strip()
            block.append(line)
            cnt += 1
            ogc += 1
            while cnt < len(self.Instructions) and nested > 0:
                line = self.Instructions[cnt].strip()
                if line.startswith(types):
                    nested += 1
                if line.endswith(item_end):
                    nested -= 1
                    if nested == 0:
                        block.append(line)
                        cnt += 1
                        break
                block.append(line)
                cnt += 1
                ogc += 1
            if nested != 0:
                self.error(67, item_type, item_end)
                return [], 0
            return block, cnt, ogc
        else:
            self.error()
            return None
        
    def num(self, value, numsys):
        """
        converts an interger to any type of number system,
        and a number system to any number system (and back to int)
        like
        int 10 -> bin 1010
        int 69 -> hex 45
        int 420 -> oct 644
        """
        if numsys == 'bin':
            return bin(value)[2:]
        elif numsys == 'hex':
            return hex(value)[2:]
        elif numsys == 'oct':
            return oct(value)[2:]
        else:
            self.error(45)
            return
    
    def convert_arg(self, args):
        """
        converts user defined function and method args
        by their types
        """
        if args.startswith('"') and args.endswith('"') or args.startswith("'") and args.endswith("'"):
            return args[1:-1]
        if args == "":
            return ""
        try:
            return self.eval(args, {}, self.variables)
        except NameError:
            # a genuinely undefined variable should surface loudly, not get
            # silently substituted as if the raw text were valid data
            self.error(18, args)
            return None
        except Exception as e:
            return args
            
    def global_vars(self):
        globals = []
        for g, l in zip(self.variables.keys(), self.original_var[-1].keys()):
            if g == l:
                globals.append(g)
        for i in globals:
            self.original_var[-1][i] = self.variables[i]
    
    def datatype_convert(self, value, types, fromwho=""):
        try:
            if types == "int":
                return int(value)
            elif types == "str":
                return str(value)
            elif types == "float":
                return float(value)
            elif types == "array":
                return tuple(value)
            elif types == "vector":
                return list(value)
            elif types == "map":
                return dict(value)
            elif types == "set":
                return set(value)
            elif types == "void":
                return None
        except ValueError:
            if types == "int":
                self.error(105, types, value)
                return None
            self.error(106, types, value)
        except TypeError:
            self.error(107, types, value)
        return None
            
    def types(self, value, mode="p"):
        if mode == "p":
            return type(value)
        if mode == "c" or mode == "clear" or mode == "clean":
            if isinstance(value, str):
                return "string"
            elif isinstance(value, int):
                return "int"
            elif isinstance(value, float):
                return "float"
            elif isinstance(value, list):
                return "vector"
            elif isinstance(value, tuple):
                return "array"
            elif isinstance(value, dict):
                return "map"
            elif isinstance(value, set):
                return "set"
            else:
                # supports any type
                new_type = str(type(value)).split(" ", 1)[1][1:-2]
                return new_type
        
    def run_condition(self, cond):
        """
        This function runs condition expressions used in while, if, and else if statements
        there are also logical operators with uses for the conditions, like
        && as "and", || as "or", ^^ as "xor", and "!" before parenthesis as "not"
        """
        # cache load here
        if cond in self.cache["cond"].keys():
            change = True
            for v in self.cache["cond"][cond]["variables"].keys():
                if self.cache["cond"][cond]["const"][v][0] != self.constants[v][0]:
                    change = False
                    break
            if change:
                return eval(self.cache["cond"][cond]["result"], {}, self.variables)
        
        arguments = self.ultimate_split(cond, ["&&", "||", "^^"]) # splits the condition by operators
        text = ""
        expr_text = ""
        ops = {
            "&&": "and",
            "||": "or",
            "^^": "^",
        }
        isfalse = False
        variables = {}
        constants = {}
        for args in arguments:
            
            if args.startswith(("(", "!(")):
                isnot = False
                if args.startswith("!"):
                    isnot = True
                    expr_text += "not "
                expr = args[2:-1].strip() if isnot else args[1:-1].strip()
                expression = self.expression(expr)
                variables.update(expression["variables"])
                constants.update(expression["const"])
                expr_text += f'({str(expression["expr"])}) '
                if isfalse:
                    continue
                if expression["iseval"]: # instant evaluation, use eval() since there is no more arb code
                    boolean = self._eval_expr_result(expression, {}, self.variables)
                else:
                    boolean = self.eval(expression["expr"], {}, self.variables, from_exp=True)
                if not isinstance(boolean, bool):
                    self.error(11, type(boolean))
                    return False
                if isnot:
                    if boolean:
                        boolean = False
                    else:
                        boolean = True
                if not boolean and "&&" in args:
                    isfalse = True
                text += str(boolean) + " "
            elif args in ["&&", "||", "^^"]:
                
                text += args[1:] + " "
                expr_text += ops[args] + " "
        self.cache["cond"][cond] = {"result": expr_text, "const": constants, "variables": variables} # cache the condition for even faster condition parsing
        if isfalse:
            return False
        new_cond = self.eval(text, {}, self.variables)
        return new_cond
    
    def expect(self, line, parts=[]):
        i = 0
        condition = 0
        while i < len(parts):
            if not line.startswith(parts[i][0]) and line.endswith(parts[i][1]):
                condition += 1
            i += 1
        if condition == 0:
            return True
        return False
    
    def error(self, code, arg1=None, arg2=None, arg3=None):
        errors = handle(**self.__dict__)
        self.Errors = errors.stderr(code, arg1, arg2, arg3)
        return
    
    def _extract_identifiers(self, exp):
        """
        Returns the set of real identifier tokens in exp, ignoring anything
        inside string literals. Used to correctly detect whether an expression
        actually references a variable, rather than naive substring matching
        (which would wrongly match a variable named "e" against the letter "e"
        sitting inside an unrelated string literal like "hello world").
        """
        without_strings = re.sub(r'"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'', '', exp)
        return set(re.findall(r'\b[A-Za-z_][A-Za-z0-9_]*\b', without_strings))
        
    def _build_token_lookup(self, split_tokens):
        """
        Buckets split_tokens by their first character, sorted longest-first
        within each bucket so multi-char operators (**, <=, ==) get checked
        before their single-char prefixes (*, <, =). Cached per unique token
        list since eval()/run_condition() call ultimate_split() repeatedly
        with the same fixed operator lists.
        """
        key = tuple(split_tokens)
        if key in self._token_lookup_cache:
            return self._token_lookup_cache[key]
        lookup = {}
        for token in split_tokens:
            lookup.setdefault(token[0], []).append(token)
        for first_char in lookup:
            lookup[first_char].sort(key=len, reverse=True)
        self._token_lookup_cache[key] = lookup
        return lookup
    
    def ultimate_split(self, line, split_tokens, group_pairs=(("'", '"'), ('"', "'")), nest_pairs=(("(", ")"), ("[", "]"), ("{", "}")), join_capture=True):
        """
        Splits 'line' by any of the split_tokens, ignoring tokens inside strings or nested groups.
    
        - split_tokens: list of strings to split by (can be multi-char)
        - group_pairs: string quote pairs
        - nest_pairs: parentheses/brackets/braces pairs
    
        Uses a first-character lookup (see _build_token_lookup) so each
        character only gets checked against tokens that could possibly match
        it, instead of looping through every token at every position.
        """
        token_lookup = self._build_token_lookup(split_tokens)
        result = []
        current = ""
        stack = []
        in_string = None
        i = 0
        while i < len(line):
            char = line[i]
    
            if in_string:
                current += char
                if char == in_string:
                    in_string = None
                i += 1
                continue
            elif any(char == start for start, end in group_pairs):
                in_string = char
                current += char
                i += 1
                continue
            elif any(char == start for start, end in nest_pairs):
                stack.append(next(end for start, end in nest_pairs if start == char))
                current += char
                i += 1
                continue
            elif stack and char == stack[-1]:
                stack.pop()
                current += char
                i += 1
                continue
    
            split_matched = False
            if not stack and not in_string and char in token_lookup:
                for token in token_lookup[char]:
                    if line[i:i+len(token)] == token:
                        if current:
                            result.append(current.strip())
                        if join_capture:
                            result.append(token)
                        current = ""
                        i += len(token)
                        split_matched = True
                        break
            if split_matched:
                continue
    
            current += char
            i += 1
    
        if current:
            result.append(current.strip())
        return result
        
    def special_split(self, line, split_str, in_char1, in_char2, ret_capture_group=False, limit=None, ranges=[0, -1]):
        """
    splits a string into a list by using split()
    and only splits the characters that's outside of a specific character
    like if it is outside ( and )
    
    why i add this? because problems like this
    
    output(range(10, 20, 2), sort(list1, True), len(range(0, 30, 3)))
    and i wanna split it by comma's
    but there is so many coma's
    it just ruins the function's arguments
    and supposed to output as ["range(10, 20, 2)", " sort(list1, True)", " len(range(0, 30, 3))"]
    but... normal .split() can't do that
    so i did this
        """
        start, end = ranges
        end = len(line) if end == -1 else end + 1
        line = line[start:end]
        new_line = ""
        inside_char = False
        i = 0
        splits = 0
    
        while i < len(line):
            # Check if we're inside quotes
            if line[i] in in_char1 and not inside_char:
                inside_char = line[i]
                new_line += line[i]
                i += 1
                continue
            elif line[i] in in_char2 and inside_char:
                inside_char = False
                new_line += line[i]
                i += 1
                continue
    
            # Check for the multi-character split
            if (
                not inside_char
                and (limit is None or splits < limit)
                and line[i:i + len(split_str)] == split_str
            ):
                new_line += (
                    "¤"
                    if not ret_capture_group
                    else f"¤{split_str}¤"
                )
                splits += 1
                i += len(split_str)
                continue
    
            # Otherwise, just copy character
            new_line += line[i]
            i += 1
    
        if "¤" in new_line:
            return new_line.split("¤")
        return [new_line]
    
    def special_find(self, line, target, in_char1, in_char2, ranges=[0, -1]):
        """
        This function works like special_split, but it returns True or False if target_str is in the string
        only if it exist, and is not inside the chosen characters (in_chars1 for the start and in_chars2 for the end)
        it has the same method as special_split, just a different purpose
    
        this function fixes the bug in self.eval() about running a built in method inside as an argument of an built in function (or even user defined)
        """
        start, end = ranges
        if not (start == 0 and end == -1):
            end = len(line) if end == -1 else end + 1
            line = line[start:end]
        inside_char = False
        i = 0
        if not isinstance(target, list):
            target = [target]
        target_lookup = self._build_token_lookup(target)
    
        while i < len(line):
            char = line[i]
    
            # Enter quoted section
            if char in in_char1 and not inside_char:
                inside_char = char
                i += 1
                continue
    
            # Exit quoted section
            elif char in in_char2 and inside_char:
                inside_char = False
                i += 1
                continue
    
            # Only check tokens that could possibly start with this character
            if not inside_char and char in target_lookup:
                for t in target_lookup[char]:
                    if line[i:i+len(t)] == t:
                        return True
    
            i += 1
    
        return False
        
    def run_functions(self, name, provided_args, infunc):
        """
        runs a user defined function and process its arguments as variables,
        it also has a scope system where variables are refreshed but you can still access global variables
        the original variables in the main program are untouched
        """
        self.in_func += 1 # for nested function calls
        og_cond = self.is_priv
        og_cond1 = self.is_pub
        
        if not infunc:
            block = self.functions[name]['block']
            count = self.functions[name]['end']
            argument = provided_args
            arg = self.functions[name]['args']
            ogc = self.functions[name]['ogc']
            count_ogc = self.functions[name]['end ogc']
            self.return_type = self.functions[name]["datatype"]
            self.is_pub = True
            self.is_priv = False
        else:
            if self.func_name in self.func_scope.keys():
                block = self.func_scope[self.func_name]["functions"][name]['block']
                count = self.func_scope[self.func_name]["functions"][name]['end']
                arg = self.func_scope[self.func_name]["functions"][name]['args']
                ogc = self.func_scope[self.func_name]["functions"][name]['ogc']
                count_ogc = self.func_scope[self.func_name]["functions"][name]['end ogc']
                self.return_type = self.func_scope[self.og_fname]["functions"][name]["datatype"]
            else:
                block = self.func_scope[self.og_fname]["functions"][name]['block']
                count = self.func_scope[self.og_fname]["functions"][name]['end']
                arg = self.func_scope[self.og_fname]["functions"][name]['args']
                ogc = self.func_scope[self.og_fname]["functions"][name]['ogc']
                count_ogc = self.func_scope[self.og_fname]["functions"][name]['end ogc']
                self.return_type = self.func_scope[self.og_fname]["functions"][name]["datatype"]
            argument = provided_args
            self.is_priv = True
            self.is_pub = False
        self.cnt = 0
        self.og_c = ogc + 1
        point = self.cnt
        if len(argument) > len(arg):
            self.error(12, name, len(argument))
        if '' in arg:
            del arg[0]
        self.traceback[name] = self.og_c
        self.original_var.append(self.variables.copy())
        self.variables = {}
        
        og_cache = self.cache
        self.cache = {
            "eval": {},
            "func": {},
            "class": {},
            "cond": {}
        }
        
        past_name = self.og_fname
        og_name = self.func_name
        self.og_fname = self.func_name
        self.func_name = name
        original_inst = self.Instructions
        for value, n in zip(argument, arg):
            if n.startswith("<"):
                types = n.split(">", 1)
                n = types[1]
                value = self.datatype_convert(value, types[0][1:].strip())
                
            self.variables[n.strip()] = value
            self.constants[n.strip()] = [True, value]
        self.process_vars()
        code = self.prep_exec(block)
        self.exec_block(code, count)
        self.global_vars()
        self.variables = self.original_var.pop()
        self.variables.update(self.public)
        self.in_func -= 1
        if infunc:
            if self.func_name in self.func_scope.keys():
                self.func_scope[self.func_name]["variables"] = self.variables.copy()
            else:
                self.func_scope[self.og_fname]["variables"] = self.variables.copy()
        self.func_name = og_name
        self.og_fname = past_name
        self.Instructions = original_inst
        self.cache = og_cache
        self.cnt = count
        self.og_c = count_ogc
        self.is_priv = og_cond
        self.is_pub = og_cond1
        del self.traceback[name]
        return
        
    def run_methods(self, name, m_name, object, object_name, provided_args, infunc):
        """
        almost the same code as run_function (because it is)
        but with a different responsibility... (which is just running user defined functions but cooler)
        """
        block = self.classes[name]["methods"][m_name]['block']
        count = self.classes[name]["methods"][m_name]['end']
        arg = self.classes[name]["methods"][m_name]['args'].copy()
        ogc = self.classes[name]["methods"][m_name]['ogc']
        count_ogc = self.classes[name]["methods"][m_name]['end ogc']
        self.return_type = self.classes[name]["methods"][m_name]["datatype"]
        argument = provided_args
        self.special[name]["access"] = True
        self.cnt = 0
        self.og_c = ogc + 1
        self.func_name = name
        point = self.cnt
        if len(argument) > len(arg):
            self.error(13, m_name, len(arg), len(argument))
        self.traceback[m_name] = self.og_c
        self.original_var.append(self.variables.copy())
        og_var = self.variables.copy()
        self.variables = {}
        if object:
            self.variables = self.objects[object_name]["variables"].copy()
        else:
            self.variables = self.classes[name]["variables"].copy()
        past_name = self.og_fname
        og_name = self.func_name
        self.og_fname = self.func_name
        self.func_name = name
        self.in_class[2] = object_name
        self.in_class[1] = True
        self.in_class[0] = name
        
        og_cache = self.cache
        self.cache = {
            "eval": {}, # for evaluation
            "func": {},
            "class": {},
            "cond": {}, # for conditions
        }
        
        self.in_func += 1
        original_inst = self.Instructions
        for value, n in zip(argument, arg):
            self.variables[n.strip()] = value
            if object:
                self.objects[object_name]["variables"][n.strip()] = value
            self.constants[n.strip()] = [True, value]
        for k in self.variables.keys():
            if k in self.special[name]["variables"].keys():
                if object:
                    self.objects[object_name]["variables"][k] = self.variables[k]
                else:
                    self.classes[name]["variables"][k] = self.variables[k]
        self.process_vars()
        
        code = self.prep_exec(block)
        self.exec_block(code, count)
        if self.in_func == 0:
            self.variables = self.original_var.pop()
            self.variables.update(og_var)
            self.Instructions = original_inst
            self.cnt = count
            return self.return_val
        self.func_name = og_name
        self.og_fname = past_name
        self.global_vars()
        
        self.variables = self.original_var.pop()
        self.variables.update(og_var)
        self.in_func -= 1
        if self.in_func <= 0:
            self.in_class = [None, False, None]
        self.Instructions = original_inst
        self.cache = og_cache
        self.cnt = count
        self.og_c = count_ogc
        if name in self.traceback:
            del self.traceback[m_name]
        return
    
    def load(self, name, addr, value):
        """
        handles list assignments in the past, but now it both handles
        list assignments and dictionary assigmments
        """
        var = self.variables[name]
        addr = self.eval(addr, {}, self.variables)
        value = self.eval(value, {}, self.variables)
        if isinstance(var, (list, dict)):
            if isinstance(var, dict):
                self.variables[name][addr] = value
            elif int(addr) > len(var) or int(addr) is None:
                self.error(14, name, len(var), len(addr))
                return
            else:
                self.variables[name][int(addr)] = value
                return
        else:
            if not self.attempt:
                self.error(15, name, type(value))
            return
    
    def datatype_keyword(self, instruction, acc="pub"):
        # this is apart of self.execute_functions() for data type syntaxes
        type = None
        line = instruction.split(" ", 1)
        data_type = line[0].strip()
        instruction = line[1].strip()
        if self.special_find(instruction, "=", ('"', "'", "(", "[", "{"), ('"', "'", ")", "]", "}")):
            self.assign_variable(instruction, dt=data_type)
            return
        elif instruction.startswith("func "):
            self.function_creation(instruction, acc, data_type)
        # there are more to come
    
    def function_creation(self, instruction, acc_type, dt="<any>"):
        types = acc_type
        start = self.cnt
        ogc = self.og_c
        arg = instruction[5:-1] if instruction.endswith('{') else instruction[5:]
        arg = arg.rstrip("{").strip()
        arg = arg[:-1].split('(', 1)
        name = arg[0]
        func_arg = [a.strip() for a in arg[1].split(',')]
        for c, a in enumerate(func_arg):
            if " " in a and a.startswith(tuple(self.datatypes)):
                arg_type = a.split(" ", 1)
                dtype = "<" + arg_type[0].strip() + ">"
                func_arg[c] = dtype + arg_type[1].strip() # argument type
                continue
            if a and any(ch in a for ch in self.forbiden_chars):
                self.error(72, a, name)  # new error code, see below
                return
        block, count, eogc = self.get_block()
        if types == "pub":
            self.functions[name] = {'block': block, 'args': func_arg, 'end': count, 'start': start, 'ogc': ogc, 'end ogc': eogc, 'datatype': dt}
        else:
            self.functions[name] = {'block': block, 'args': func_arg, 'end': count, 'start': start, 'ogc': ogc, 'end ogc': eogc, 'datatype': dt}
            if self.func_name not in self.func_scope.keys():
                self.func_scope[self.func_name] = {"variables": {}, "functions": {}, "classes": {}}
            self.func_scope[self.func_name]["functions"][name] =  {'block': block, 'args': func_arg, 'end': count, 'start': start, 'ogc': ogc, 'end ogc': eogc}
            self.func_scope[self.func_name]['functions'].update(self.functions)
            self.func_scope[self.func_name]['functions'][name]['datatype'] = dt
        self.cnt = count - 1
        self.og_c = eogc
            
    def execute_functions(self, instruction):
        """where lines are processed through
        but further down the code, the lines breaks up into smaller and smaller peices
        where the code understands it with the help of other functions like
        self.assign_variable(), self.methods(), and self.evals()
        
        so that means there is a layer of parsing the program does instead of doing it by once
        this is the first layer, where lines are checked to where they should execute,
        this is where keywords are executed aswell, if keywords weren't checked, it checks if it's a variable assignment
        if not, it checks if it's using a built in method (without variable assignment)
        then checks if it's using a library function
        then only says SyntaxError
        
        Layer 1 of parsing
        """
        global m, r, t, json, sys
        if isinstance(instruction, list):
            instruction = instruction[0].strip()
        else:
            instruction = instruction.strip()

        if not instruction:
            return
            
        elif instruction.startswith('/<'): pass # programming language's comment syntax
        
        elif instruction.startswith('output'):
            stdout = self.handle_output(instruction)
            
            if "\\" in str(stdout): # processes backslashes
                stdout = stdout.encode().decode("unicode_escape")
            return stdout
            
        elif instruction.startswith(('{', '}')): pass # because it may be a peice of a code block
                    
        elif instruction.startswith('pass'):
            return # passes instructions, usefull for placeholders
            
        elif instruction.startswith('quit()'):
            self.Errors["QuitError"] = True # a hidden error just to stop the program without affecting the main python program
            return
        
        elif instruction.startswith('inherit ') and self.in_class[1]:
            arg = instruction[8:].strip().split(" from ", 1)
            method = arg[0].strip() # like <const>
            classes = arg[1].strip() # like Parent()
            arg = method[:-1].split('(', 1)
            method = arg[0].strip()
            argument = self.special_split(arg[1].strip(), ",", ('"', "'", "(", "[", "{"), ('"', "'", ")", "]", "}"))
            c_class = copy.deepcopy(self.classes[self.in_class[0]])
            if classes not in c_class["inherits"]:
                self.error(16, classes, self.in_class[0])
                return
            p_class = c_class["inherits"][c_class["inherits"].index(classes)]
            p_info = copy.deepcopy(self.classes[p_class])
            if method in p_info["methods"].keys():
                args = [self.convert_arg(arg.strip()) for arg in argument]
                self.classes[p_class]["methods"]["<const>"]["end"] = self.cnt + 1
                c_name = self.in_class[0]
                self.run_methods(p_class, method, False, p_class, argument, False)
                # gets variables
                inherits = copy.deepcopy(self.classes[p_class])
                self.classes[c_name]["variables"].update(inherits["variables"])
                for name in inherits["methods"].keys():
                    if name not in self.classes[c_name]["methods"].keys():
                        self.classes[c_name]["methods"][name] = inherits["methods"][name]
                self.in_class[0] = c_name
                self.in_class[1] = True
                self.cnt -= 1
                self.og_c -= 1
            else:
                self.error(17, method, classes)
            return
            
        elif instruction.startswith("<debug>"):
            # VEYL SOURCE CODE DEVELOPER DEBUGGING
            inst = instruction[8:].strip()
            if inst.startswith("var") and "_" not in inst:
                print(self.variables)
            elif inst.startswith("var_") and inst.endswith("class"):
                print(self.classes[self.in_class[0]]["variables"])
            elif inst.startswith("objects"):
                print(self.objects)
            elif inst.startswith("var_value "):
                arg = inst[10:].strip()
                print(self.variables[arg])
            elif inst.startswith("function"):
                print(self.func_name)
            
        elif instruction.startswith('load'):
            # load name[addr] = value
            # this keyword handles list loading and dictionaries aswell
            instruction = instruction[5:]
            part = instruction.split("=", 1)
            value = part[1].strip()
            parts = part[0].split("[", 1)
            
            addr = parts[1].strip().split("]")[0]
            name = parts[0].strip()
            if name not in self.variables:
                self.error(18, name)
                return None
            else:
                self.load(name, addr, value)
        
        elif instruction.startswith("break"):
            # breaks out of a loop
            if self.exec_fl <= 0:
                self.error(19)
                return None
            self.breaking = True
            return
            
        elif instruction.startswith('continue'):
            if self.exec_fl <= 0:
                self.error(20)
                return None
            self.continuing = True
            return
            
        elif instruction.startswith('while'):
            # like a while loop
            point = 0
            ogc = self.og_c
            block, count, eogc = self.get_block()
            condition = instruction[6:-1] if instruction.endswith('{') else instruction[6:]
            self.exec_fl += 1
            try:
                error_testing = self.run_condition(condition)
            except Exception:
                self.error(86)
                return
            while self.run_condition(condition):
                self.og_c = ogc
                code = self.prep_exec(block)
                self.exec_block(code, count)
                if self.breaking:
                    self.breaking = False
                    break
                    
            self.exec_fl -= 1
            self.cnt = count
            self.og_c = eogc
        
        elif instruction.startswith('return') and self.in_func > 0 or instruction.startswith('return') and self.in_class[1] and self.in_func > 0:
            # returns a value in a function
            self.return_val = {}
            arg = instruction[7:].strip()
            arg = self.special_split(arg, ",", ('"', "'", "(", "[", "{"), ('"', "'", ")", "]", "}"))
            v = []
            for var in arg:
                value = self.eval(var, {}, self.variables)
                if self.return_type is None:
                    v.append(value)
                    continue
                rt = self.return_type
                if rt != "<any>":
                    value = self.datatype_convert(value, rt)
                v.append(value)
            self.return_val = v
            self.return_cache = v
            self.is_return = True
            return
        
        elif instruction.startswith('return') and self.in_func == 0:
            self.error(89)
            
        elif instruction.startswith('global') and self.in_func:
            # makes variables global
            arg = instruction[7:].strip()
            if arg not in self.original_var[-1]:
                self.error(21, arg)
                return None
            self.variables[arg] = self.original_var[-1][arg]
            
        elif instruction.startswith('if'):
            # an if statement
            self.condition = False
            self.if_executed = False
            self.in_if = True
            condition = instruction[2:-1].strip() if instruction.endswith('{') else instruction[2:].strip()
            block, count, eogc = self.get_block()
            cond = self.run_condition(condition)
            if cond:
                self.condition = True
                self.if_executed = True
                code = self.prep_exec(block)
                self.exec_block(code, count)
                self.in_if = True
                # iterates over the code till it reaches a line starting with else or a non in code block line
                count -= 1
                eogc -= 1
                while True:
                    count += 1
                    eogc += 1
                    if count >= len(self.Instructions): break
                    if self.Instructions[count].strip().startswith('{') or self.Instructions[count].strip().endswith('{'):
                        self.in_block += 1
                    if self.Instructions[count].strip().startswith('}') and self.in_block > 0 or self.Instructions[count].strip().endswith('}') and self.in_block > 0:
                        self.in_block -= 1
                    if self.Instructions[count].strip() == "":
                        continue
                    if self.Instructions[count].strip().startswith("else"):
                        continue
                    if not self.Instructions[count].strip().startswith(('{', '}', 'else')) and self.in_block == 0:
                        self.in_block, self.condition = 0, False
                        self.in_if = False
                        self.if_executed = False
                        break
                self.cnt = count - 1
                self.og_c = eogc - 1
                
            else:
                self.condition = False 
                # iterates over the code till it reaches a line starting with else or a non in code block line
                count -= 1
                eogc -= 1
                while True:
                    count += 1
                    eogc += 1
                    if count >= len(self.Instructions): break
                    if self.Instructions[count].strip().startswith('else') and self.in_block == 0:
                        break
                    if self.Instructions[count].strip().startswith('{') or self.Instructions[count].strip().endswith('{'):
                        self.in_block += 1
                    if self.Instructions[count].strip().startswith('}') and self.in_block > 0 or self.Instructions[count].strip().endswith('}') and self.in_block > 0:
                        self.in_block -= 1
                        if self.in_block == 0:
                            self.in_block = False
                    if self.Instructions[count].strip() == "":
                        continue
                    if not self.Instructions[count].strip().startswith(('{', '}', 'else')) and not self.in_block:
                        self.in_block, self.condition = False, False
                        self.in_if = False
                        break
                
                self.cnt = count - 1
                self.og_c = eogc - 1
                return
        elif instruction.startswith('else'):
            arg = instruction[4:].strip()
            arg = arg[:-1] if arg.endswith('{') else arg
            # else if statement
            if arg.startswith('if') and not self.condition:
                condition = arg[2:]
                if not self.in_if:
                    self.error(22)
                    return None
                else:
                    block, count, eogc = self.get_block()
                    cond = self.run_condition(condition)
                    self.in_if = True
                    if cond and not self.if_executed:
                        self.condition = True
                        code = self.prep_exec(block)
                        self.exec_block(code, count)
                        self.in_if = True
                        self.cnt = count - 1
                        count -= 1
                        eogc -= 1
                        while True:
                            count += 1
                            eogc += 1
                            if count >= len(self.Instructions): break
                            if self.Instructions[count].strip().startswith('{') or self.Instructions[count].strip().endswith('{'):
                                self.in_block += 1
                            elif self.Instructions[count].strip().startswith('}') and self.in_block > 0 or self.Instructions[count].strip().endswith('}') and self.in_block > 0:
                                self.in_block -= 1
                            elif self.Instructions[count].strip() == "":
                                continue
                            elif not self.Instructions[count].strip().startswith(('{', '}', 'else')) and self.in_block == 0:
                                self.in_block = 0
                                self.in_if = False
                                break
                        self.cnt = count - 1
                        self.og_c = eogc - 1
                    else:
                        self.condition = False
                        count -= 1
                        eogc -= 1
                        while True:
                            count += 1
                            eogc += 1
                            if count >= len(self.Instructions): break
                            if self.Instructions[count].strip().startswith(('else', "else if")) and self.in_block == 0:
                                break
                            elif self.Instructions[count].strip().startswith('{') or self.Instructions[count].strip().endswith('{'):
                                self.in_block += 1
                            elif self.Instructions[count].strip().startswith('}') and self.in_block > 0 or self.Instructions[count].strip().endswith('}') and self.in_block > 0:
                                self.in_block -= 1
                            elif self.Instructions[count].strip() == "":
                                continue
                            elif not self.Instructions[count].strip().startswith(('{', '}', 'else')) and self.in_block == 0:
                                self.in_block = 0
                                self.in_if = False
                                break
                        self.cnt = count - 1
                        self.og_c = eogc - 1
                        return
            else:
                # else statement
                block, count, eogc = self.get_block()
                if not self.in_if:
                    self.error(23)
                    return None
                elif self.condition:
                    self.cnt = count - 1
                    self.og_c = eogc - 1
                else:
                    self.in_if = False
                    code = self.prep_exec(block)
                    self.exec_block(code, count)
                    self.cnt = count - 1
                    self.og_c = eogc - 1
            
        
        # for loops (for each and loops)
        elif instruction.startswith('for'):
            arg = self.special_split(instruction[4:], " in ", ('"', "'", "(", "[", "{"), ('"', "'", ")", "]", "}"), False, 1)
            if len(arg) < 2 or not arg[0].strip() or not arg[1].strip():
                self.error(85)
                return None
            iter, arg = arg[1].strip(), arg[0].strip()
            if iter.endswith('{'):
                iter = iter[:-1].strip()
            if iter.startswith("range(") and iter.endswith(")"):
                iterable = list(self.ran(iter))
            else:
                iterable = self.eval(iter, {}, self.variables)
            if isinstance(iterable, str):
                iterable = list(iterable)
            if not isinstance(iterable, (list, tuple, dict, set, range, frozenset, str)):
                self.error(87, self.types(iterable, "c"))
                self.cnt = count - 1
                self.og_c = eogc - 1
                return None
            ogc = self.og_c
            block, count, eogc = self.get_block()
            self.exec_fl += 1
            for cnt, val in enumerate(iterable):
                self.variables[arg] = val
                self.process_vars()
                self.og_c = ogc
                code = self.prep_exec(block)
                self.exec_block(code, count)
                if self.breaking:
                    self.breaking = False
                    break
            self.exec_fl -= 1 
            self.cnt = count - 1
            self.og_c = eogc - 1
        
        elif instruction.startswith('call '):
            # calls a user defined function (also supports class methods, both inside a class and outside)
            
            arg = self.special_split(instruction[5:-1], "(", ("'", '"'), ("'", '"'), False, 1)
            name = arg[0]
            polymorph = False
            isclass = False
            object_name = None
            called = False
            if any(name.startswith(aa+".") for aa in list(self.variables.keys())):
                try:
                    polymorph = True
                    name = name.split(".")
                    object_name = name[0].strip()
                    name = self.eval(name[0], {}, self.variables) + "." + name[1]
                except Exception:
                    name = arg[0]
            if any(name == a for a in list(self.class_callers.keys())) or any(name.startswith(a) for a in list(self.classes.keys())):
                name = name.strip().split(".")
                m_name = name[1]
                if any(name[0].startswith(a) for a in list(self.class_callers.values())):
                    if polymorph:
                        for i in list(self.class_callers.keys()):
                            if self.class_callers[i] == name[0]:
                                name = self.class_callers[i]
                    else: name = self.class_callers[name[0]]
                else: name = name[0]
                if m_name not in self.classes[name]["methods"].keys():
                    self.error(64, m_name, name)
                    return
                if self.classes[name]["methods"][m_name].get("type") == "priv":
                    self.error(71, m_name, name)
                    return
                args = self.special_split(arg[1], ",", ('"', "'", "(", "[", "{"), ('"', "'", ")", "]", "}"))
                args = [self.convert_arg(arg.strip()) for arg in args]
                og = self.variables
                self.variables = self.classes[name]["variables"]
                self.classes[name]["methods"][m_name]["end"] = self.cnt
                isclass = True
                called = True
                self.run_methods(name, m_name, True, object_name, args, False)
                self.variables = og
            
            elif self.in_class[1] and name in self.special[self.in_class[0]]["methods"].keys() and self.special[self.in_class[0]]["methods"][name]:
                # runs class methods within the class itself
                m_name = name.strip()
                class_n = self.in_class[0]
                classes = self.classes[class_n]
                args = self.special_split(arg[1], ",", ('"', "'", "(", "[", "{"), ('"', "'", ")", "]", "}"))
                args = [self.convert_arg(arg.strip()) for arg in args]
                classes["methods"][m_name]["end"] = self.cnt
                called = True
                self.run_methods(class_n, m_name, False, class_n, args, False)
                
            elif name in list(self.functions.keys()):
                a = self.special_split(arg[1], ",", ("'", '"', "(", "[", "{"), ("'", '"', ")", "]", "}"))
                a = [self.convert_arg(ar.strip()) for ar in a]
                self.functions[name]['end'] = self.cnt
                self.functions[name]['end ogc'] = self.og_c
                called = True
                self.run_functions(name, a, False)
                
            elif self.in_func:
                if self.is_priv and name in list(self.func_scope.keys()) or self.is_pub and self.func_name in list(self.func_scope.keys()):
                    a = self.special_split(arg[1], ",", ("'", '"', "(", "[", "{"), ("'", '"', ")", "]", "}"))
                    a = [self.convert_arg(ar.strip()) for ar in a]
                    ending = self.cnt
                    end_ogc = self.og_c
                    if self.is_priv:
                        self.func_scope[self.og_fname]["functions"][name]['end'] = self.cnt
                        self.func_scope[self.og_fname]["functions"][name]['end ogc'] = self.og_c
                    elif self.is_pub:
                        self.func_scope[self.func_name]["functions"][name]['end'] = self.cnt
                        self.functions[self.func_name]["functions"][name]['end ogc'] = self.og_c
                    called = True
                    self.run_functions(name, a, True)
                    self.cnt = ending
                    self.og_c = end_ogc
            if not called:
                # nothing matched this name as a class, class-method, or function
                name_str = name if isinstance(name, str) else ".".join(name)
                if "." in name_str:
                    cls_part, m_part = name_str.rsplit(".", 1)
                    if cls_part in self.classes or cls_part in self.class_callers:
                        self.error(64, m_part, cls_part)
                    else:
                        self.error(62, cls_part)
                else:
                    self.error(63, name_str)
                return None
            if not self.in_class[1] and isclass:
                self.special[name]["access"] = False
                
        elif instruction.startswith("public") or instruction.startswith("private"):
            types = ""
            if instruction.startswith("public"):
                instruction = instruction[7:].strip()
                types = "pub"
            if instruction.startswith("private"):
                instruction = instruction[8:].strip()
                types = "priv"
            # Function or variables
            if not instruction.startswith("func ") and "=" in instruction: # meaning it's a variable assignment
                arg = instruction.split("=", 1)
                name = arg[0].strip()
                value = self.eval(arg[1].strip(), {}, self.variables)
                self.variables[name] = value
                if type == "pub" and self.in_class[1]:
                    self.special[self.in_class[0]]["variables"][name] = True
                elif types == "priv" and self.in_class[1]:
                    self.special[self.in_class[0]]["variables"][name] = False
                elif types == "pub":
                    self.public[name] = value # stored into public
                elif types == "priv" and name in self.public.keys():
                    del self.public[name]
                self.process_vars()
            
            elif not instruction.startswith("func ") and instruction in self.variables.keys(): # not assignments
                name = instruction
                if types == "pub" and self.in_class[1]:
                    self.special[self.in_class[0]]["variables"][name] = True
                elif types == "priv" and self.in_class[1]:
                    self.special[self.in_class[0]]["variables"][name] = False
                elif types == "pub":
                    self.public[name] = self.variables[name]
                elif types == "priv" and name in self.public.keys():
                    del self.public[name]
                self.process_vars()
            
            elif instruction.startswith('func '):
                # user define function
                # example: `func main(arg1, arg2):`
                self.function_creation(instruction, types)
            elif instruction.startswith(tuple(self.datatypes)):
                self.datatype_keyword(instruction, types)
            elif instruction.startswith("class "):
                name = self.handle_class(instruction, types=types)
                if types == "priv":
                    self.private_classes[name] = self.classes[name]
        # error handling keywords
        elif instruction.startswith("try"):
            # error handling by catching errors, with throw and catch and finally
            block, count, eogc = self.get_block()
            self.attempt = True
            code = self.prep_exec(block)
            self.exec_block(code, count)
            self.cnt = count - 1
            self.og_c = eogc - 1
            return
        
        elif instruction.startswith('catch'): # Catching Errors
            if self.attempt:
                new_name = []
                error_name = instruction[5:-1].strip() if instruction.endswith('{') else instruction[5:]
                # strips out spaces because strip() doesnt strip out 1 letter space
                for letter in error_name:
                    if letter != " ":
                        new_name.append(letter)
                self.attempt = False # so the errors and messages out of attempt block will work
                error_name = "".join(new_name)
                block, count, eogc = self.get_block()
                if error_name in self.Errors.keys():
                    if self.Errors[error_name]:
                        for i in self.Errors:
                            self.Errors[i] = False
                        code = self.prep_exec(block)
                        self.exec_block(code, count)
                    self.cnt = count - 1
                    self.og_c = eogc - 1
                elif error_name == "<any>":
                    if any(i for i in self.Errors.values()):
                        for i in self.Errors:
                            self.Errors[i] = False
                        code = self.prep_exec(block)
                        self.exec_block(code, count)
                    self.cnt = count - 1
                    self.og_c = eogc - 1
                else:
                    self.error(24, error_name)
                    return None
                self.attempt = False
            else:
                self.error(25)
                return None
                
        elif instruction.startswith("throw"):
            args = instruction[6:].strip().split("(", 1)
            name = args[0].strip()
            output = "output(" + args[1].strip()
            output = self.handle_output(output)
            if not name.endswith("Error"):
                self.error(26, name)
                return None
            try:
                # This is the only raw output std error message
                print("\033[31mTraceback(most_recent_call_back):\033[0m")
                for i in self.traceback:
                    print(f"    TB - [ File `<{self.path / Path(self.file_name).with_suffix(self.file_extension)}>` line: {self.traceback[i]}, in {i} ],")
                print(f"    TB - [ File `<{self.path / Path(self.file_name).with_suffix(self.file_extension)}>` TB found > line [{self.og_c}]: {self.Instructions[self.cnt]} in {i} ]")
                print(f"\n{name}: {output}")
                self.Errors[name] = True
                return None
            except Exception as e:
                self.error(27)
                return None
                
        elif instruction.startswith("import"):
            args = instruction[6:].strip().split(",")
            for lib in args:
                has_get = True if " get " in lib else False
                get_val = None
                if has_get:
                    lib = lib.split(" get ")
                    get_val = lib[1].strip()
                    lib = lib[0].strip()
                if lib in self.libraries:
                    self.library.append(lib)
                    self.library_name[lib] = lib
                    self.name_library[lib] = lib
                    # import individually if the program says so, so startup doesn't take too long
                    if lib == "time":
                        import time
                        t = time
                    elif lib == "random":
                        import random
                        r = random
                    elif lib == "math":
                        import math
                        m = math
                    elif lib == "files":
                        import json as j
                        json = j
                    elif lib == "sys":
                        import sys as s
                        sys = s
                    elif lib in self.nplibs.keys():
                        self.nplibs_acc[lib] = True # access allowed
                    else:
                        pass # some built in libraries have its own functions and methods
                    continue
                if Path(self.path / Path(lib.replace(".", "/")).with_suffix(".vey")).exists():
                    # execute .vey and get variables, functions, and methods
                    # types of imports -
                    # import file_vey <- imports full code
                    # import directory.file_vey <- imports code
                    # import file_vey get func_or_class <- imports a function or class instead of the whole code
                    types = "dir" if "." in lib else "cwd"
                    path = str(self.path)
                    if types == "dir":
                        # get directory
                        pathp = path / Path(lib.replace(".", "/")).with_suffix(".vey")
                        pathx = path / Path(lib.replace(".", "/")).with_suffix(".vyl")
                    else:
                        pathp = path / Path(lib).with_suffix(".vey")
                        pathx = path / Path(lib).with_suffix(".vyl")
                    # get name
                    split_varsp = str(pathp).rsplit("/", 1)
                    split_varsx = str(pathx).rsplit("/", 1)
                    namep = split_varsp[1]
                    namex = split_varsx[1]
                    absolute_pathp = split_varsp[0]
                    absolute_pathx = split_varsx[0]
                    if pathp.exists():
                        with open(pathp, "r") as file:
                            code = str(file.read())
                        path = pathp
                        name = namep
                        absolute_path = absolute_pathp
                    elif pathx.exists():
                        with open(pathx, "r") as file:
                            code = str(file.read())
                        name = namex
                        absolute_path = absolute_pathx
                        path = pathx
                        
                    else:
                        self.error(28, lib)
                        return
                        
                    # execute code
                    vey = VEY(code, {}, absolute_path, name)
                    result = vey.execute()
                    variables = {}
                    functions = {}
                    func_scope = {}
                    classes = {}
                    
                    private_c = {}
                    public = {}
                    class_callers = {}
                    variable_info = {}
                    objects = {}
                    constant = {}
                    name = name.removesuffix(".vey")
                    # get variables, functions, classes, and libraries
                    if has_get and get_val is not None:
                        value = get_val.split(",")
                        for get_val in value:
                            get_val = get_val.strip()
                            if get_val in vey.variables.keys():
                                variables[get_val] = vey.variables[get_val]
                            if get_val in vey.functions.keys():
                                functions[get_val] = vey.functions[get_val]
                            if get_val in vey.classes.keys():
                                classes[get_val] = vey.classes[get_val]
                            if get_val in vey.objects.keys():
                                objects[get_val] = vey.objects[get_val]
                                class_callers[get_val] = vey.class_callers[get_val]
                                variables[get_val] = vey.variables[get_val]
                                variables["<" + get_val + ">"]
                    else:
                        for v in vey.variables.keys():
                            variables[name + "." + v] = vey.variables[v]
                        for f in vey.functions.keys():
                            functions[name + "." + f] = vey.functions[f]
                        for fs in vey.func_scope.keys():
                            func_scope[name + "." + f] = vey.func_scope[f]
                        for c in vey.classes.keys():
                            classes[name + "." + c] = vey.classes[c]
                        for pc in vey.private_classes.keys():
                            private_c[name + "." + pc] = vey.classes[pc]
                        for p in vey.public.keys():
                            public[name + "." + p] = vey.public[p]
                        for cc in vey.class_callers.keys():
                            class_callers[name + "." + cc] = vey.class_callers[cc]
                        for vi in vey.variable_info.keys():
                            variable_info[name + "." + vi] = vey.variable_info[vi]
                        for obj in vey.objects.keys():
                            objects[name + "." + obj] = vey.objects[obj]
                        for con in vey.constants.keys():
                            constants[name + "." + con] = vey.constants[con]
                        
                    if vey.libraries:
                        self.library.extend(vey.library)
                        self.library_name.update(vey.library_name)
                        self.name_library.update(vey.name_library)
                    if vey.nplibs != {}:
                        self.nplibs.update(vey.nplibs)
                        self.nplibs_acc.update(vey.nplibs_acc)
                    self.variables.update(variables)
                    self.functions.update(functions)
                    self.classes.update(classes)
                    self.func_scope.update(func_scope)
                    self.library.append(name)
                    self.process_vars()
                else:
                    self.error(29, lib)
                    return
                    
        elif instruction.startswith("rename"):
            # rename variables and libraries
            if " as " not in instruction:
                self.error(30, instruction.strip())
                return None
                
            args = instruction[7:].strip().split(" as ")
            name = args[0].strip()
            rename = args[1].strip()
            if rename in self.forbiden_chars:
                self.error(31, name, rename)
                return None
            if name in self.library_name.keys():
                self.library_name[name] = rename
                self.name_library[rename] = name
            elif name in self.variables.keys():
                self.variables[rename] = self.variables[name]
                if name != rename:
                    del self.variables[name] # so it doesn't delete the variable
        
        elif instruction.startswith("delete"):
            arg = instruction[7:].strip()
            targets = self.special_split(arg, ",", ('"', "'", "(", "[", "{"), ('"', "'", ")", "]", "}"))
            for target in targets:
                self.delete_target(target.strip())
                
        elif instruction.startswith("sync"):
            # syncronizes variables
            # sync mode host_var with *group_varA and group_varB
            args = instruction[4:].strip()
            parts = args.split(" with ", 1)
            args = parts[0].strip().split(" ")
            mode = args[0].strip()
            host = args[1].strip()
            if host not in self.variables.keys():
                # host variables must be a real variable
                self.error(32, host)
                return None
                
            groups = parts[1].strip().split(" and ") # stays as a list of variable names
            # group variables can both be existing variables and non existing, if it doesn't exist, it will create a new one
            # immidietly assigning the variable with the hosts, depending what mode async is on, but immidietly as "None"
            variables = {}
            for var in groups: # variable assignments to newly defined vars
                if var not in self.variables.keys():
                    self.variables[var] = None
                variables[var] = self.variables[var]
            all_variables = variables.copy()
            all_variables.update({host: self.variables[host]})
            # sync_var dictionary
            self.sync_variables[host] = {
                "host": host,
                "past value": self.variables[host],
                "mode": mode,
                "group": groups,
                "group value": variables.copy(),
                "all": all_variables.copy(),
                "recent": None,
                "past group value": variables.copy(), # for gva only
            }
            # modes
            if mode in ["hva", "ota", "avs"]:
                # hva assigns every variables to the hosts value (hva means host value assignment)
                # ota assigns every variable to the hosts value, but only once, every variables are independent (ota means one time assignment)
                # avs assigns all variable, any variable changes will affect every group and even host variable (avs mean all variable shared)
                for var in groups:
                    variables[var] = self.variables[host]
                self.variables.update(variables)
                self.sync_variables[host]["group value"].update(variables)
                self.sync_variables[host]["past group value"].update(variables)
                self.sync_variables[host]["all"].update(variables)

            # the rest of the modes is processed through self.process_vars()
            self.process_vars()
        
        elif instruction.startswith('desync'):
            args = instruction[7:].strip()
            values = args.split(" from ")
            host = values[1].strip()
            if host not in self.sync_variables.keys():
                self.error(33, host)
                return None
            args = values[0].strip().split(" and ")
            for vars in args:
                if vars not in self.sync_variables[host]["group"]:
                    self.error(34, vars, host)
                    return None
                lst = self.sync_variables[host]["group"]
                del self.sync_variables[host]["group"][lst.index(vars)]
                del self.sync_variables[host]["group value"][vars]
                del self.sync_variables[host]["all"][vars]
            
        elif instruction.startswith('class'):
            self.handle_class(instruction)
            
        elif instruction.startswith("open"):
            # example: open file.type as read name
            insts = instruction[5:].split(" ", 1)
            file = insts[0].strip()
            args = insts[1].strip().split("as", 1)
            types = args[0].strip()
            name = args[1].strip()
            modes = ["read", "write", "append", "binary", "create", "text"]
            convert = {
                "read": "r",
                "write": "w",
                "append": "a",
                "create": "x",
                "binary": "b",
                "text": "t"
            }
            if types not in modes:
                self.error(35, types)
                return None
            if any(ch in name for ch in self.forbiden_chars):
                self.error(36, name)
                return None
            types = convert[types]
            file = self.eval(file, {}, self.variables)
            if not file.startswith("$/"): # starting
                file = self.path / file
            else:
                file = file[1:].strip()
            try:
                handle = open(file, types)
            except FileNotFoundError:
                self.error(73, file)
                return None
            except FileExistsError:
                self.error(100, file)
                return None
            self.variables[name] = handle
            self.constants[name] = [True, handle]
        
        # LAYER 2 OF PARSING
        elif instruction.startswith("const "):
            inst = instruction[6:].strip()
            self.assign_variable(inst, constant=True)
            self.process_vars()
        
        elif any(instruction.startswith(dtype + " ") for dtype in self.datatypes):
            self.datatype_keyword(instruction)
            self.process_vars()
            
        elif '=' in instruction:
            self.assign_variable(instruction)
            self.process_vars()
            
        elif '.' in instruction:
            func = self.special_split(instruction, ".", ('"', "'", "(", "[", "{"), ('"', "'", ")", "]", "}"))
            name = func[0]
            cnt = 1
            while cnt < len(func):
                if func[cnt].startswith('push(') and func[cnt].endswith(')'):
                    args = func[cnt][5:-1]
                    if not isinstance(self.variables[name], list):
                        self.error(50)
                        return None
                    else:
                        if args:
                            try:
                                self.variables[name].append(self.eval(args, {}, self.variables))
                            except Exception as e:
                                self.error(51, args)
                                return None
                elif func[cnt].startswith('freeze(') and func[cnt].endswith(')'):
                    if not isinstance(self.variables[name], set):
                        self.error(52)
                        return None
                    self.variables[name] = frozenset(self.variables[name])
                elif func[cnt].startswith('set(') and func[cnt].endswith(')'):
                    if not isinstance(self.variables[name], set):
                        self.error(53, name, self.variables[name])
                        return None
                    self.variables[name] = set(self.variables[name])
                elif func[cnt].startswith("close(") and func[cnt].endswith(")"):
                    if not isinstance(self.variables[name], _io.TextIOWrapper):
                        self.error(101, "[file].close()", "_io.TextIOWrapper", self.types(self.variables[name], "c"))
                        return None
                    self.variables[name].close()
                    
                elif func[cnt].startswith("write(") and func[cnt].endswith(")"):
                    if not isinstance(self.variables[name], _io.TextIOWrapper):
                        self.error(101, "[file].write()", "_io.TextIOWrapper", self.types(self.variables[name], "c"))
                        return None
                    arg = func[cnt][6:-1].strip()
                    value = self.eval(arg, {}, self.variables)
                    self.variables[name].write(value)
                elif func[cnt].startswith("extend(") and func[cnt].endswith(")"):
                    if not isinstance(self.variables[name], list):
                        self.error(61, self.variables[name])
                        return
                    arg = func[cnt][7:-1].strip()
                    value = self.eval(arg, {}, self.variables)
                    self.variables[name].extend(value)
                elif func[cnt].startswith("update(") and func[cnt].endswith(")"):
                    if not isinstance(self.variables[name], dict):
                        self.error(101, "[dict].update()", "dict", self.types(self.variables[name], "c"))
                    arg = func[cnt][7:-1].strip()
                    value = self.eval(arg, {}, self.variables)
                    self.variables[name].update(value)
                cnt += 1
            if self.libraries:
                if any(instruction.strip().startswith(self.library_name[l] + ".") and l in self.library for l in self.nplibs.keys()):
                    struct = instruction.split(".", 1)
                    key = self.name_library[struct[0]]
                    module = self.nplibs[key]
                    lib = module(**self.__dict__)
                    if not hasattr(lib, "process"):
                        self.error(102, key)
                        return
                    try:
                        result = lib.process(instruction, self.variables, variant="ol")
                    except Exception as e:
                        self.error(103, key, instruction)
                    if result == [] or result is None:
                        return
                    if len(result) > 0:
                        if not isinstance(result[0], str):
                            self.variables = result[0]
                        elif result[0].startswith("$<<"):
                            self.process_sse(result[0], types="library")
                        if len(result) > 1:
                            self.cnt = result[0]
                        else:
                            pass
                    if len(result) > 1 and result[0] != "$<<DEBUGGED>>" and result[0] != "$<<ADV_DEBUGGED>>":
                        self.cnt = result[1]
                    return
                lib = libraries(self.__dict__)
                result = lib.process(instruction, self.variables, t, m, r, json, sys, variant="ol")
                if result == [] or result is None:
                    return
                
                if len(result) > 0:
                    if isinstance(result[0], str) and not result[0].startswith("$<<"):
                        self.variables = result[0]
                        if len(result) > 1:
                            self.cnt = result[1]          # only jumps for real (non-sentinel) results
                    else:
                        if result[0] == "$<<SELF EVAL>>":
                            self.eval_deb = not self.eval_deb
                        elif result[0] == "$<<DEBUGGED>>":
                            wait_time = result[1] if len(result) > 1 else 0
                            if self.debug:
                                self.debug = False
                            else:
                                self.adv_debug = False
                                self.debug = True
                                self.debug_wait = wait_time
                        elif result[0] == "$<<ADV_DEBUGGED>>":
                            wait_time = result[1] if len(result) > 1 else 0
                            if self.adv_debug:
                                self.adv_debug = False
                            else:
                                self.debug = False
                                self.adv_debug = True
                                self.adv_debug_wait = wait_time
                if "$<<new_path>>" in self.variables.keys():
                    self.path = self.variables["$<<new_path>>"]
                    del self.variables["$<<new_path>>"]
                            
                # libraries already access whatever is inside veyl, result is a dict
                
        else:
            self.error(1, instruction)
            return None
            
    def assign_variable(self, instruction, run_method=False, dt="<any>", constant=False):
        """
        Main Level 2 of parsing
        where variable assignments are handled
        but also can be the 4th layer of parsing by self.eval()
        """
        stuff = instruction.split('=', 1)
        libs = False
        left = stuff[0].strip()
        if not left or left == "":
            self.error(92)
            return
        right = stuff[1].strip()
        
        # Handle values of string literals, so method doesnt get involved in strings
        ismethod = self.special_find(right, ".", ('"', "'", "(", "[", "{"), ('"', "'", ")", "]", "}"))
        pattern = r'(?<!\w)[+-]?(?:\d+\.\d+|\d+\.|\.\d+)(?!\w)'
        if not right.startswith("call") and not bool(re.search(pattern, right)):
            main = self.special_split(right, ".", ("'", '"', "("), ("'", '"', ")"))
        else: main = right.strip()
        if isinstance(main, list):
            main = main[0].strip()
        else: main = main.strip()
        # for imports
        if main in self.library:
            main = right
        # handles multiple variable names (like val1, val2 = stuff)
        l = self.special_split(left, ",", ('"', "'", "(", "[", "{"), ('"', "'", ")", "]", "}"))
        # if single name
        if len(l) == 1:
            left = l[0]
        else:
            left = l # full list instead
        
        if left not in self.variables.keys():
            self.constants[left] = [True, None]
        if left not in self.variable_info.keys():
            self.variable_info[left] = {
                "datatype": dt,
                "constant": constant,
                "isprotected": False,
                "Immutable": False
            }
        else:
            if self.variable_info[left]["constant"]:
                if not self.attempt:
                    self.error(93, left)
                    return
        pre_run = False
        # runs self.eval if it includes arithmetics
        if not self.evals and any(operator in main for operator in ["+", "-", "/", "*", "%"]):
            if self.special_find(main, ["+", "-", "*", "/", "%"], ('"', "'", "(", "[", "{"), ('"', "'", ")", "]", "}")):
                self.variables[left] = self.eval(main, {}, self.variables)
                pre_run = True
        def built_in_functions(left, main, right, method):
            global m, r, t, json, sys
            libs = False
            try:
                if main.startswith('num(') and main.endswith(')'):
                    self.handle_num_function(left, main)
                    return
                elif main in list(self.variables.keys()):
                    self.variables[left] = self.variables[main]
                    return
                    
                elif main.startswith('input(') and main.endswith(')'):
                    output = main.split('(', 1)
                    content = str(output[1][:-1])
                    if content.startswith('"') and content.endswith('"') or content.endswith("'") and content.startswith("'"):
                        out = content[1:-1]
                    else:
                        try:
                            out = str(self.eval(content, {}, self.variables))
                        except Exception:
                            out = content
                    value = input(out)
                    self.variables[left] = str(value)
                    return
                    
                elif main.startswith('length(') and main.endswith(')'):
                    arg = main[7:-1]
                    try:
                        value = self.eval(arg.strip(), {}, self.variables)
                    except Exception as e:
                        
                        return None
                    if value:
                        self.variables[left] = len(value)
                    return
                elif main.startswith('range(') and main.endswith(')'):
                    self.variables[left] = self.ran(main)
                    return    
                elif main.startswith('format(') and main.endswith(")"):
                    content = main[7:-1].strip()
                    if content.startswith('"') and content.endswith('"') or content.startswith("'") and content.endswith("'"):
                        content = content[1:-1]
                    # Extract expressions inside the curly braces and evaluate
                    new_content = ""
                    parts = re.split(r'({[^}]*})', content)  # Split by expressions in curly braces
                    for part in parts:
                        if part.startswith("{") and part.endswith("}"):
                            expression = part[1:-1]  # Remove curly braces
                            evaluated = self.eval(expression, {}, self.variables)
                            new_content += str(evaluated)  # Append the evaluated result
                        else:
                            new_content += part  # Append the literal text
                    self.variables[left] = new_content
                    return
                elif main.startswith('eval(') and main.endswith(')'):
                    arg = self.special_split(main[5:-1], ",", ("'", '"', "(", "{", "["), ('"', "'", ")", "]", "}"))
                    try:
                        if len(arg) > 1:
                            a1 = arg[1].strip()
                            globald = self.eval(a1, {}, self.variables)
                            if len(arg) > 2:
                                a2 = arg[2].strip()
                                locald= self.eval(a2, {}, self.variables)
                                if len(arg) > 3:
                                    arb = self.eval(arg[3].strip(), {}, self.variables)
                                else: 
                                    arb = False
                            else:
                                locald = {}
                        else:
                            globald = {}
                            locald = {}
                        argument = self.eval(arg[0].strip(), {}, self.variables, arb)
                        locald.update(self.variables)
                        self.variables[left] = self.eval(argument, globald, locald, arb)
                        return
                    except Exception as e:
                        self.error(37, arg[0])
                        return None
                    
                elif main.startswith('call'):
                    arg = main[5:-1].split('(', 1)
                    name = arg[0]
                    polymorph = False
                    isclass = False
                    object_name = None
                    called = False
                    if any(name.startswith(aa+".") for aa in list(self.variables.keys())):
                        
                        try:
                            polymorph = True
                            name = name.rsplit(".")
                            object_name = name[0]
                            name = self.eval(name[0], {}, self.variables) + "." + name[1]
                        except Exception:
                            name = arg[0]
                    if any(name == a for a in list(self.class_callers.keys())) or any(name.startswith(a) for a in list(self.classes.keys())) or self.in_class[1] and main in self.special[self.in_class[0]]["variables"].keys():
                        name = name.strip().rsplit(".", 1)
                        m_name = name[1]
                        self.traceback[m_name] = self.og_c
                        if any(name[0].startswith(a) for a in list(self.class_callers.values())):
                            if polymorph:
                                for i in list(self.class_callers.keys()):
                                    if self.class_callers[i] == name[0]:
                                        name = self.class_callers[i]
                            else: name = self.class_callers[name[0]]
                        else: name = self.in_class[0]
                        if m_name not in self.classes[name]["methods"].keys():
                            self.error(64, m_name, name)
                        if self.classes[name]["methods"][m_name].get("type") == "priv":
                            self.error(71, m_name, name)
                            return
                        args = self.special_split(arg[1], ",", ("'", '"', "(", "[", "{"), ("'", '"', ")", "]", "}"))
                        args = [self.convert_arg(arg.strip()) for arg in args]
                        self.classes[name]["methods"][m_name]["end"] = self.cnt 
                        t = False if self.classes[name]["methods"][m_name]["type"] == "pub" else True
                        isclass = True
                        called = True
                        self.run_methods(name, m_name, True, object_name, args, t)
                        if self.is_return:
                            if isinstance(left, str):
                                left = [left]
                            for v, n in zip(self.return_val, left):
                                self.variables[n] = v
                            self.is_return = False
                    elif name in list(self.functions.keys()):
                        a = self.special_split(arg[1], ",", ("'", '"', "(", "[", "{"), ("'", '"', ")", "]", "}"))
                        a = [self.convert_arg(ar.strip()) for ar in a]
                        self.functions[name]['end'] = self.cnt
                        self.traceback[name] = self.og_c
                        called = True
                        
                        self.run_functions(name, a, False)
                        if self.is_return:
                            if isinstance(left, str):
                                left = [left]
                            for v, n in zip(self.return_val, left):
                                self.variables[n] = v
                            self.is_return = False
                    elif self.in_func:
                        if self.is_priv and name in list(self.func_scope.keys()) or self.is_pub and self.func_name in list(self.func_scope.keys()):
                            a = self.special_split(arg[1], ",", ("'", '"', "(", "[", "{"), ("'", '"', ")", "]", "}"))
                            a = [self.convert_arg(ar.strip()) for ar in a]
                            ending = self.cnt
                            end_ogc = self.og_c
                            if self.is_priv:
                                self.func_scope[self.og_fname]["functions"][name]['end'] = self.cnt
                            elif self.is_pub:
                                self.func_scope[self.func_name]["functions"][name]['end'] = self.cnt
                            self.traceback[name] = self.og_c
                            called = True
                            self.run_functions(name, a, True)
                            if self.is_return:
                                if isinstance(left, str):
                                    left = [left]
                                for v, n in zip(self.return_val, left):
                                    self.variables[n] = v
                                self.is_return = False
                            self.cnt = ending
                            self.og_c = end_ogc
                    if not called:
                        name_str = name if isinstance(name, str) else ".".join(name)
                        if "." in name_str:
                            cls_part, m_part = name_str.rsplit(".", 1)
                            if cls_part in self.classes or cls_part in self.class_callers:
                                self.error(64, m_part, cls_part)
                            else:
                                self.error(62, cls_part)
                        else:
                            self.error(63, name_str)
                        return None
                    if not self.in_class[1] and isclass:
                        self.special[name]["access"] = False
                    
                    return
                elif main.startswith('sort(') and main.endswith(')'):
                    arg = main[5:-1].split(',')
                    reverse = self.eval(arg[1].strip(), {}, self.variables) if len(arg) == 2 else False
                    if not isinstance(reverse, bool):
                        self.error(38)
                        return
                    name = self.eval(arg[0], {}, self.variables)
                    # sort(list, reverse=False) reverse being boolean, and list as variable name that is a list
                    if len(arg) > 2:
                        self.error(39, len(arg))
                        return
                    elif isinstance(arg, list):
                        if isinstance(name, list) and len(arg) == 2 or reverse or not reverse:
                            if not reverse:
                                self.variables[left] = sorted(name)
                            elif reverse:
                                sort_val = sorted(name)
                                self.variables[left] = list(reversed(sort_val))
                            return
                        if not isinstance(name, list):
                            self.error(40)
                            return
                    return
                elif main.startswith("mean(") and main.endswith(")"):
                    arg = self.eval(main[5:-1].strip(), {}, self.variables)
                    if not isinstance(arg, list):
                        self.error(41, arg)
                        return None
                    val = sum(arg)
                    self.variables[left] = val / len(arg)
                    return
                elif main.startswith("median(") and main.endswith(")"):
                    arg = self.eval(main[7:-1].strip(), {}, self.variables)
                    if not isinstance(arg, list):
                        self.error(41, arg)
                        return None
                    lists = sorted(arg)
                    length = len(lists) / 2
                    if not str(length).endswith(".5"):
                        mid1 = int(length) - 1
                        mid2 = mid1 + 1
                        stuffs = lists[mid1] + lists[mid2]
                        self.variables[left] = stuffs / 2
                    else:
                        mid = int(length)
                        self.variables[left] = float(lists[mid])
                    return
                elif main.startswith("mode(") and main.endswith(")"):
                    arg = self.eval(main[5:-1].strip(), {}, self.variables)
                    if not isinstance(arg, list):
                        self.error(41, arg)
                        return None
                    counts = {}
                    for i in arg:
                        counts[str(i)] = 0
                    for i in arg:
                        counts[str(i)] += 1
                    highest = 0
                    for i in counts:
                        if int(counts[str(i)]) >= int(highest):
                            highest = i
                            
                    self.variables[left] = highest
                    return
                elif main.startswith("sum(") and main.endswith(")"):
                    arg = self.eval(main[4:-1].strip(), {}, self.variables)
                    if not isinstance(arg, list):
                        self.error(41, arg)
                        return None
                    self.variables[left] = sum(arg)
                    return
                elif main.startswith("max(") and main.endswith(")"):
                    arg = main[4:-1].strip().split(",", 1)
                    value = self.eval(arg[0], {}, self.variables)
                    if len(arg) == 2:
                        self.variables[left] = max(value, default=arg[1])
                    else:
                        self.variables[left] = max(value)
                    return
                elif main.startswith("min(") and main.endswith(")"):
                    arg = main[4:-1].strip().split(",", 1)
                    value = self.eval(arg[0], {}, self.variables)
                    if len(arg) == 2:
                        self.variables[left] = min(value, default=arg[1])
                    else:
                        self.variables[left] = min(value)
                    return
                
                elif main.startswith("reverse(") and main.endswith(")"):
                    arg = main[8:-1].strip()
                    value = self.eval(arg, {}, self.variables)
                    self.variables[left] = value[::-1]
                    return
                
                elif main.startswith("type(") and main.endswith(")"):
                    arg = main[5:-1].strip().split(",", 1)
                    value = self.eval(arg[0].strip(), {}, self.variables)
                    if len(arg) == 2:
                        mode = arg[1].strip()
                    else:
                        self.variables[left] = type(value)
                        return
                    self.variables[left] = self.types(value, mode)
                    return
                elif main.startswith("zip(") and main.endswith(")"):
                    arg = self.special_split(main[4:-1].strip(), ",", ('"', "'", "(", "[", "{"), ('"', "'", ")", "]", "}"))
                    new_list = []
                    for value in arg:
                        new_list.append(self.eval(value.strip(), {}, self.variables))
                    self.variables[left] = list(zip(*new_list))
                    return
                elif main.startswith("dict(") and main.endswith(")"):
                    arg = self.special_split(main[5:-1].strip(), ",", ('"', "'", "(", "[", "{"), ('"', "'", ")", "]", "}"))
                    if len(arg) < 2:
                        self.error(42, len(arg))
                        return None
                    arg[0] = self.eval(arg[0], {}, self.variables)
                    arg[1] = self.eval(arg[1], {}, self.variables)
                    if len(arg[0]) != len(arg[1]):
                        self.error(43)
                        return None
                    dicts = {}
                    for v in range(len(arg[1])):
                        dicts[arg[0][v]] = arg[1][v]
                    self.variables[left] = dicts
                    return
                elif main.startswith("isinstance(") and main.endswith(")"):
                    arg = self.special_split(main[11:-1].strip(), ",", ("'", '"', "(", "[", "{"), ("'", '"', ")", "]", "}"))
                    value = self.eval(arg[0].strip(), {}, self.variables)
                    value2 = arg[0].strip() # for classes
                    given_type = arg[1].strip()
                    if given_type in self.classes.keys():
                        datatype = "<class_name> " + given_type
                    else:
                        try:
                            datatype = self.eval(given_type, {}, self.variables)
                        except Exception:
                            self.error(99, given_type)
                    
                    if not isinstance(datatype, type) and datatype.startswith("<class_name>"):
                        dt = given_type
                        if not value2 in self.objects.keys():
                            self.variables[left] = False
                            return
                        c_obj = self.objects[value2]
                        self.variables[left] = True if c_obj["instance"] == dt == value or dt in c_obj["inherits"] else False # both tracks norma class instance and inherits
                    else:
                        self.variables[left] = isinstance(value, datatype)
                    return
                        
                    
                elif main in self.functions.keys():
                    arg = self.functions[main.strip()]
                    # just copies it as variable left name
                    self.functions[left] = arg
                    self.variables[left] = main
                    return
                # handles classes
                elif main.startswith(tuple(self.classes.keys())):
                    name = None
                    for i in self.classes.keys():
                        if i in main:
                            name = i
                    if "(" in main and ")" in main and "<const>" in list(self.classes[name]["methods"].keys()):
                        args = main[:-1].split("(", 1)
                        name = args[0]
                        
                        m_name = "<const>"
                        args = args[1].split(',')
                        args = [self.convert_arg(arg.strip()) for arg in args]
                        self.classes[name]["methods"]["<const>"]["end"] = self.cnt
                        self.run_methods(name, m_name, None, None, args, False)
                    self.class_callers[left] = name
                    self.objects[left] = {"variables": {}, "instance": name, "inherits": self.classes[name]["inherits"]}
                    self.objects[left]["variables"] = copy.deepcopy(self.classes[name]["variables"])
                    self.variables[left] = name
                    ogl = left
                    left = "<" + left + ">"
                    self.variables[left] = ogl
                    return
                # handles list, tuples, dictionaries
                elif main.startswith(("[", "(", "{")):
                    # this code handles item values where not only it supports normally loading items, but also items that stretches with the end further down on the code
                    # normal assignment
                    if main.startswith("[") and main.endswith("]") or main.startswith("(") and main.endswith(")") or main.startswith("{") and main.endswith("}"):
                        self.variables[left] = self.eval(main, {}, self.variables)
                        return
                    else:
                        # handles complex long assignments (like multi lined)
                        args = main.strip()
                        structure, count, c_ogc = self.get_items(args)
                        self.cnt = count - 1
                        self.og_c = c_ogc - 1
                        item_now = ""
                        for i in structure:
                            item_now += str(i)
                        self.variables[left] = self.eval(item_now, {}, self.variables)
                    return
                elif self.library and "." in right:
                    # checks if it's floating point number
                    flt_check = right.split(".", 1)
                    d1 = flt_check[0]
                    d2 = flt_check[1]
                    if d1.strip().isdigit() and d2.strip().isdigit():
                        self.variables[left] = self.eval(main, {}, self.variables)
                        return
                    
                    if any(instruction.strip().startswith(self.library_name[l] + ".") and l in self.library for l in self.nplibs.keys()):
                        struct = instruction.split(".", 1)
                        key = self.name_library[struct[0]]
                        module = self.nplibs[key]
                        lib = module(**self.__dict__)
                        result = lib.process(instruction, self.variables, variant="ol")
                        if result == [] or result is None:
                            return
                            
                        if len(result) >= 1:
                            self.variables = result[0]
                            return
                    lib = libraries(self.__dict__)
                    result = lib.process((left, right), self.variables, t, m, r, json, sys, variant="av")
                    if result[0] is None or isinstance(result[0], dict) and result[0] == {}:
                        pass
                    else:
                        self.variables = result[0]
                        return
                if not libs:
                    """
                    3rd Layer of parsing, which is evaluation, all assignments are
                    """
                    self.variables[left] = self.eval(main, {}, self.variables)
            except Exception as e:
                # If this error handler get commented out, it is a mistake, as it is for debugging purposes
                if isinstance(e, ZeroDivisionError):
                    self.error(4)
                    return None
                if isinstance(e, MemoryError):
                    self.error(7)
                    return
                self.error(6, right)
                print(e)
                return None
        if not run_method and not pre_run:
            built_in_functions(left, main, right, ismethod)
        else:
            if ismethod:
                self.methods(left, right)
                return
        # AFTER VARIABLE MANIPULATIONS
        if any(left in self.classes[vs]["variables"].keys() for vs in self.classes.keys()) and self.in_class[1]:
            self.classes[self.in_class[0]]["variables"][left] = self.variables[left]
        if self.constants[left][0] and self.constants[left][1] == None and left in self.variables.keys():
            self.constants[left][1] = self.variables[left]
        elif self.constants[left][0] and self.constants[left][1] != None and left in self.variables.keys():
            self.constants[left][0] = False
        if dt != "<any>":
            self.variables[left] = self.datatype_convert(self.variables[left], dt)
            self.variable_info[left]["datatype"] = "Nonetype" if dt == "void" else dt
        if ismethod:
            self.methods(left, right) # next is methods
        return
    def methods(self, left, right):
        """
        3rd layer of parsing
        this handles built in methods and assigns them to the variable
        this also handles multiple built in methods instead of doing it one by one
        """
        try:
            if '.' in right:
                var_func = self.special_split(right, ".", ("'", '"'), ("'", '"'))
                if var_func[0] not in self.variables:
                    name = left
                else:
                    name = var_func[0]
                cnt = 1
                while cnt < len(var_func):
                    if var_func[cnt].startswith('cap(') and var_func[cnt].endswith(')') :
                        func = var_func[cnt][4:-1]
                        arg_er = list(func.split(',')) # list() because if no comma, it wouldnt be a list
                        if func != '':
                            self.error(54)
                            break
                        self.variables[left] = self.variables[name].upper() if isinstance(self.variables[name], str) else None
                        if self.variables[left] is None:
                            self.error(55, self.variables[left])
                            return
                    if var_func[cnt].startswith('low(') and var_func[cnt].endswith(')') :
                        func = var_func[cnt][4:-1]
                        arg_er = list(func.split(','))
                        if func != '':
                            self.error(56, len(arg))
                            return
                        self.variables[left] = self.variables[name].lower() if isinstance(self.variables[name], str) else None
                        if self.variables[left] is None:
                            self.error(55, self.variables[left])
                            return
                    elif var_func[cnt].startswith('as(') and var_func[cnt].endswith(')'):
                        args = var_func[cnt][3:-1]
                        if name in self.variables:
                            try:
                                if args in self.variables:
                                    arg = self.variables[args]
                                    if arg not in ["int", "interger", "str", "string", "flt", "float", "list", "tuple"]:
                                        pass
                                    else:
                                        args = arg
                                if args in ['int', 'interger']:
                                    self.variables[left] = int(self.variables[name])
                                    return
                                elif args in ['str', 'string']:
                                    self.variables[left] = str(self.variables[name])
                                    return
                                elif args in ['flt', 'float']:
                                    self.variables[left] = float(self.variables[name])
                                    return
                                elif 'bool' in args:
                                    self.variables[left] = bool(self.variables[name])
                                    return
                                elif "vector" in args:
                                    self.variables[left] = list(self.variables[name])
                                    return
                                elif "array" in args:
                                    self.variables[left] = tuple(self.variables[name])
                                    return
                                elif "set" in args:
                                    self.variables[left] = set(self.variables[name])
                                    return
                                else:
                                    self.error(57, type(args))
                                    return

                            except ValueError:
                                self.error(58, self.variables[name], args)
                                return
                    elif var_func[cnt].startswith('rem(') and var_func[cnt].endswith(')'):
                        argu = var_func[cnt][4:-1]
                        if argu != "":
                            func = self.eval(argu, {}, self.variables)
                        else:
                            func = argu
                        self.variables[left] = self.variables[name].replace(func, "")
                        return
                    elif var_func[cnt].startswith("strip(") and var_func[cnt].endswith(")"):
                        argu = var_func[cnt][6:-1]
                        if argu is None:
                            argu = " "
                        self.variables[left] = self.variables[name].strip(argu)
                        return
                    elif var_func[cnt].startswith("split(") and var_func[cnt].endswith(")"):
                        argu = self.special_split(var_func[cnt][6:-1], ",", ("(", "'", '"', "[", "{"), (")", "'", '"', "]", "}"))
                        group = self.eval(argu[0].strip(), {}, self.variables)
                        if len(argu) > 1:
                            limit = self.eval(argu[1].strip(), {}, self.variables)
                            
                            self.variables[left] = self.variables[name].split(group, limit)
                        else:
                            self.variables[left] = self.variables[name].split(group)
                        return
                        
                    # strwith() method as startswith() and endwith() as endswith()
                    elif var_func[cnt].startswith("hasprefix(") and var_func[cnt].endswith(')'):
                        arg = var_func[cnt][10:-1].strip()
                        arg = arg[1:-1] if arg.startswith('"') and arg.endswith('"') or arg.startswith("'") and arg.endswith("'") else arg
                        if self.variables[name].startswith(arg):
                            self.variables[left] = True
                        else:
                            self.variables[left] = False
                            
                    elif var_func[cnt].startswith("hassuffix(") and var_func[cnt].endswith(")"):
                        arg = var_func[cnt][10:-1].strip()
                        arg = arg[1:-1] if arg.startswith('"') and arg.endswith('"') or arg.startswith("'") and arg.endswith("'") else arg
                        if self.variables[name].endswith(arg):
                            self.variables[left] = True
                        else:
                            self.variables[left] = False
                            
                    elif var_func[cnt].startswith("replace(") and var_func[cnt].endswith(")"):
                        arg = self.special_split(var_func[cnt][8:-1].strip(), ",", ("'", '"'), ("'", '"'))
                        arg1 = self.eval(arg[0], {}, self.variables)
                        arg2 = self.eval(arg[1], {}, self.variables)
                        if arg1.startswith("(") and arg1.endswith(")"):
                            arg1 = tuple(arg1)
                        self.variables[left] = self.variables[name].replace(arg1, arg2)
                    
                    elif var_func[cnt].startswith("slice(") and var_func[cnt].endswith(")"):
                        arg = var_func[cnt].strip()[6:-1]
                        arg = self.special_split(arg, ",", ("(", "'", '"'), (")", "'", '"'))
                        if not isinstance(arg, list):
                            arg = [arg]
                        for i, v in enumerate(arg):
                            arg[i] = self.eval(v, {}, self.variables)
                        if len(arg) < 3:
                            if len(arg) < 2:
                                arg.append(len(self.variables[name]))
                            arg.append(1)
                        if arg[0] == ":" and arg[1] != ":":
                            value = self.variables[name][::int(arg[1])]
                        elif arg[0] != ":" and arg[1] == ":":
                            value = self.variables[name][int(arg[0])::int(arg[2])]
                        else:
                            value = self.variables[name][int(arg[0]):int(arg[1]):int(arg[2])]
                        self.variables[left] = value
                        
                    elif var_func[cnt].startswith("pop(") and var_func[cnt].endswith(')'):
                        arg = var_func[cnt][4:-1]
                        try:
                            arg = self.eval(arg, {}, self.variables) if arg else arg
                        except Exception as e:
                            self.error(59, args)
                            return
                        if not arg:
                            self.variables[left] = self.variables[name].pop()
                        elif isinstance(arg, bool) and isinstance(self.variables[name], list):
                            if arg:
                                # pops like an FIFO
                                self.variables[left] = self.variables[name].pop(0)
                            else:
                                # pops like the LIFO
                                self.variables[left] = self.variables[name].pop()
                        else:
                            if isinstance(arg, int) and isinstance(self.variables[name], list):
                                if arg <= len(self.variables[name]):
                                    self.variables[left] = self.variables[name].pop(arg)
                                else:
                                    self.error(60)
                                    return
                            else:
                                self.error(61, name)
                                return
                    elif var_func[cnt].startswith("push(") and var_func[cnt].endswith(")"):
                        arg = var_func[cnt][5:-1].strip()
                        value = self.eval(arg, {}, self.variables) # value to push
                        self.variables[name].append(value)
                        self.variables[left] = self.variables[name]
                        
                    elif var_func[cnt].startswith("read(") and var_func[cnt].endswith(")"):
                        arg = var_func[cnt][5:-1]
                        self.variables[left] = self.variables[name].read()
                    elif var_func[cnt].startswith("keys(") and var_func[cnt].endswith(")"):
                        arg = var_func[cnt][5:-1]
                        self.variables[left] = self.variables[name].keys()
                    elif var_func[cnt].startswith("items(") and var_func[cnt].endswith(")"):
                        arg = var_func[cnt][6:-1]
                        self.variables[left] = self.variables[name].items()
                    elif var_func[cnt].startswith("values(") and var_func[cnt].endswith(")"):
                        arg = var_func[cnt][7:-1]
                        self.variables[left] = self.variables[name].values()
                    elif var_func[cnt].startswith("const(") and var_func[cnt].endswith(")"):
                        arg = var_func[cnt][6:-1].strip()
                        self.constants[left] = [True, self.variables[name]]
                        self.variables[left] = self.variables[name]
                    elif var_func[cnt].startswith("variable(") and var_func[cnt].endswith(")"):
                        # opposite of constant
                        arg = var_func[cnt][8:-1].strip()
                        self.constants[left] = [False, self.variables[name]]
                        self.variables[left] = self.variables[name]
                    elif var_func[cnt].startswith("immutable(") and var_func[cnt].endswith(")"):
                        if not isinstance(self.variables[name], str):
                            self.error(101, ".immutable()", "str", self.types(self.variables[name]))
                            return None
                        self.variable_info[left]["Immutable"] = True # Special key for string literals only
                    elif var_func[cnt].startswith("mutable(") and var_func[cnt].endswith(")"):
                        if not isinstance(self.variables[name], str):
                            self.error(101, ".mutable()", "str", self.types(self.variables[name]))
                            return None
                        self.variable_info[left]["Immutable"] = False
                    cnt += 1
                self.process_vars()
            else:
                return
        except Exception as e:
            self.error(8, right)
            return
    
    def ran(self, main):
        # for the built in range(start, end, set)
        # the range() function, i just ask myself why did i did this?
        arg = main[6:-1].split(',')
        start = self.eval(arg[0], {}, self.variables)
        end = self.eval(arg[1], {}, self.variables) if len(arg) >= 2 else None
        set = self.eval(arg[2], {}, self.variables) if len(arg) == 3 else 1
        if not isinstance(start, int):
            self.error(47)
            return None
        elif not isinstance(end, int) and end is not None:
            self.error(48, end)
            return None
        elif not isinstance(set, int):
            self.error(49, set)
            return None
        if end is None:
            list_ran = range(0, start, set)
        else:
            list_ran = range(start, end, set)
        return list_ran
        
    def handle_num_function(self, left, right):
        """Prepares and process the arguments of num()"""
        try:
            func_params = right[4:-1].split(',')
            if len(func_params) == 2:
                value = self.eval(func_params[0].strip(), {}, self.variables)
                numsys = func_params[1].strip().strip('"')
                self.variables[left] = self.num(value, numsys)
            else:
                self.error(45)
                return
        except Exception as e:
            self.error(68, e)
            return
    
    def handle_output(self, instruction):
        """handles for the output() function
        this not only handles printing variables and values, but also built in functions, expressions,
        user defined functions, class methods (in and out of the class scope), and even formsted strings
        """
        content = instruction[7:-1].strip() if instruction.startswith("output(") else instruction # Extract content within output(...)
        if not content:
            return ""
        # Handle output of string literals, variables, and expressions    
        if content.startswith('call '):
            arg = content[5:-1].split('(', 1)
            name = arg[0]
            polymorph = False
            isclass = False
            v = ""
            object_name = None
            called = False
            if any(name.startswith(aa+".") for aa in list(self.variables.keys())):
                
                try:
                    polymorph = True
                    name = name.rsplit(".")
                    object_name = name[0]
                    name = self.eval(name[0], {}, self.variables) + "." + name[1]
                except Exception:
                    name = arg[0]
            if any(name == a for a in list(self.class_callers.keys())) or any(name.startswith(a) for a in list(self.classes.keys())) or self.in_class[1] and content in self.special[self.in_class[0]]["variables"].keys():
                name = name.strip().rsplit(".", 1)
                m_name = name[1]
                self.traceback[m_name] = self.og_c
                if any(name[0].startswith(a) for a in list(self.class_callers.values())):
                    if polymorph:
                        for i in list(self.class_callers.keys()):
                            if self.class_callers[i] == name[0]:
                                name = self.class_callers[i]
                    else: name = self.class_callers[name[0]]
                else: name = self.in_class[0]
                if m_name not in self.classes[name]["methods"].keys():
                    self.error(64, m_name, name)
                    return
                if self.classes[name]["methods"][m_name].get("type") == "priv":
                    self.error(71, m_name, name)
                    return
                args = arg[1].split(',')
                args = [self.convert_arg(arg.strip()) for arg in args]
                self.classes[name]["methods"][m_name]["end"] = self.cnt 
                t = False if self.classes[name]["methods"][m_name]["type"] == "pub" else True
                isclass = True
                called = True
                self.run_methods(name, m_name, True, object_name, args, t)
                if self.is_return:
                    for val in self.return_val:
                        v += val + " "
                    self.is_return = False
            elif name in list(self.functions.keys()):
                a = self.special_split(arg[1], ",", ("'", '"', "(", "[", "{"), ("'", '"', ")", "]", "}"))
                a = [self.convert_arg(ar.strip()) for ar in a]
                self.functions[name]['end'] = self.cnt
                self.traceback[name] = self.og_c
                called = True
                self.run_functions(name, a, False)
                if self.is_return:
                    
                    for val in self.return_val:
                        v += val + " "
                    self.is_return = False
            elif self.in_func:
                if self.is_priv and name in list(self.func_scope.keys()) or self.is_pub and self.func_name in list(self.func_scope.keys()):
                    a = self.special_split(arg[1], ",", ("'", '"', "(", "[", "{"), ("'", '"', ")", "]", "}"))
                    a = [self.convert_arg(ar.strip()) for ar in a]
                    ending = self.cnt
                    end_ogc = self.og_c
                    if self.is_priv:
                        self.func_scope[self.og_fname]["functions"][name]['end'] = self.cnt
                    elif self.is_pub:
                        self.func_scope[self.func_name]["functions"][name]['end'] = self.cnt
                    self.traceback[name] = self.og_c
                    called = True
                    self.run_functions(name, a, True)
                    if self.is_return:
                        for val in self.return_val:
                            v += val + " "
                        self.is_return = False
                    self.cnt = ending
                    self.og_c = end_ogc
            if not called:
                # nothing matched this name as a class, class-method, or function
                name_str = name if isinstance(name, str) else ".".join(name)
                if "." in name_str:
                    cls_part, m_part = name_str.rsplit(".", 1)
                    if cls_part in self.classes or cls_part in self.class_callers:
                        self.error(64, m_part, cls_part)
                    else:
                        self.error(62, cls_part)
                else:
                    self.error(63, name_str)
                return None
            if not self.in_class[1] and isclass:
                self.special[name]["access"] = False
            return v
        elif content.startswith('"') and content.endswith('"') or content.endswith("'") and content.startswith("'"):
            return content[1:-1]  # Output string literal
        elif self.in_class[1] and content in self.classes[self.in_class[0]]["variables"].keys():
            return self.classes[self.in_class[0]]["variables"][content]
        elif content in self.variables.keys():
            return self.variables[content]  # Output variable value
        elif content.startswith('f(') and content.endswith(')'):  # Format handling
            content = content.strip('f(').strip(')')
            if content.startswith('"') and content.endswith('"') or content.startswith("'") and content.endswith("'"):
                content = content[1:-1]
            # Extract expressions inside the curly braces and evaluate
            new_content = ""
            parts = re.split(r'({[^}]*})', content)  # Split by expressions in curly braces
            for part in parts:
                if part.startswith("{") and part.endswith("}"):
                    expression = part[1:-1]  # Remove curly braces
                    evaluated = self.eval(expression, {}, self.variables)
                    new_content += str(evaluated)  # Append the evaluated result
                else:
                    new_content += part  # Append the literal text
            return new_content
        else:
            try:
                if any(a in content for a in list(self.variables.keys())) and self.in_class[1]:
                    c = content.split(".")
                    if len(c) > 1:
                        content = c[1]
                conts = self.special_split(content, ",", ("(", "'", '"'), (")", "'", '"'))
                if isinstance(conts, list) and len(conts) > 1:
                    outputs = []
                    for i, val in enumerate(conts):
                        if val.startswith('"') and val.endswith('"') or val.endswith("'") and val.startswith("'"):
                            outputs.append(val[1:-1])
                            
                        else: outputs.append(self.handle_output(val))
                    conts = ""
                    for i in outputs:
                        conts += str(i) + " "
                    return conts
                v = self.eval(content, {}, self.variables)
                if isinstance(content, str) and isinstance(v, tuple):
                    t = ""
                    for i in v:
                        t += str(i) + " "
                    v = t
                    
                return v
            except Exception as e:
                self.error(46, content)
                return

    def handle_class(self, line):
        insts = line[5:].strip()
        inherits = False
        if insts.endswith("{"): insts = insts[:-1].strip()
        inheritances = []
        if "(" in insts and ")" in insts:
            insts = insts[:-1].split("(", 1)
            inheritances = insts[1].split(',')
            inherits = True
            insts = insts[0]
            
        self.classes[insts] = {"methods": {}, "variables": {"<dict>": {}, "<attr>": []}, "inherits": inheritances}
        if inherits:
            for i in inheritances:
                parent_const = {}
                if i not in self.classes.keys():
                    continue
                parent_const.update(copy.deepcopy(self.classes[i]))
                if "<const>" in self.classes[i]["methods"].keys():
                    parent_const["methods"]["_" + i + "_" + "<const>"] = self.classes[i]["methods"]["<const>"].copy() # so both constructors don't get over written
                    del parent_const["methods"]["<const>"]
                if i:
                    self.classes[insts]["methods"].update(parent_const["methods"])
                    self.classes[insts]["variables"].update(parent_const["variables"])
                    self.classes[insts]["variables"]["<dict>"].update(parent_const["variables"])
                    self.classes[insts]["variables"]["<attr>"].extend(list(parent_const["methods"].keys()))
                    self.classes[insts]["variables"]["<attr>"].extend(list(parent_const["variables"].keys()))
                        
        # statics
        self.special[insts] = {"variables": {}, "methods": {}, "access": False} # this stores static variable and method names here
            
        ogc = self.og_c
        block, count, eogc = self.get_block()
        og_inst = self.Instructions
        self.Instructions = block
        og_cnt = count
        self.cnt = 0
        #{'block': block, 'args': func_arg, 'end': count, 'start': start, 'ogc': ogc, 'end ogc': eogc}
        while self.cnt < len(block):
            if block[self.cnt].endswith("{") and block[self.cnt].startswith("{"):
                block[self.cnt] = block[self.cnt][:-1]
            # static functions, public is static, where it is defined as a class method, while private is also a class method, but you can't directly call it outside of class'
            if block[self.cnt].startswith("public func") or block[self.cnt].startswith("private func"):
                idks = block[self.cnt][12:].strip() if block[self.cnt].startswith("private") else block[self.cnt][11:].strip()
                start = self.cnt
                if idks.endswith("{"): idks = idks[:-1].strip()
                idks = idks.removesuffix(")")
                arg = idks.split('(') # removes the starting parenthensis and ending
                func_name = arg[0]
                func_arg = [a.strip() for a in arg[1].split(",")]
                ogc2 = self.og_c
                b, count, eogc2 = self.get_block()
                self.classes[insts]["methods"][func_name] = {'block': b, 'args': func_arg, 'end': count, 'start': start, "ogc": ogc2, "end ogc": eogc2, "type": "pub" if block[self.cnt].strip().startswith("public") else "priv"}
                self.classes[insts]["variables"]["<attr>"].append(func_name)
                self.special[insts]["methods"][func_name] = True
                    
                self.cnt = count - 1
                self.og_c = eogc - 1
            self.cnt += 1
            self.og_c += 1
        self.cnt = og_cnt - 1
        self.og_c = eogc - 1
        self.Instructions = og_inst
        return insts
    
    def delete_target(self, arg):
        """
        Deletes a single delete-target. Supports:
        - plain names: variables, functions, classes, object instances, imported libraries
        - bracket access: list/dict elements, e.g. arr[0], mp["key"]
        - dot access: object attributes (obj.attr) and class-level
          attributes/methods (ClassName.attr / ClassName.method)
        Called once per comma-separated target, so
        `delete a, obj.attr, arr[0], math` deletes all four in one line.
        """
        arg = arg.strip()
        if not arg:
            return
    
        base, accessors = self.parse_delete_target(arg)
        if accessors:
            if base not in self.variables:
                self.error(18, base)
                return
            current = self.variables[base]
            try:
                for accessor in accessors[:-1]:
                    key = self.eval(accessor, {}, self.variables)
                    current = current[key]
                final_key = self.eval(accessors[-1], {}, self.variables)
                del current[final_key]
            except (KeyError, IndexError, TypeError):
                self.error(14, base, len(current) if hasattr(current, "__len__") else "?", accessors[-1])
            return
    
        if self.special_find(arg, ".", ('"', "'"), ('"', "'")):
            obj_name, attr = arg.split(".", 1)
            obj_name = obj_name.strip()
            attr = attr.strip()
    
            if obj_name in self.class_callers:
                # live object instance - delete an instance attribute
                deleted = False
                if obj_name in self.objects and attr in self.objects[obj_name]["variables"]:
                    del self.objects[obj_name]["variables"][attr]
                    deleted = True
                if self.in_class[1] and self.in_class[2] == obj_name and attr in self.variables:
                    del self.variables[attr]
                    deleted = True
                if not deleted:
                    self.error(18, attr)
                return
    
            if obj_name in self.classes:
                # class itself - delete a class-level attribute or method
                if attr in self.classes[obj_name]["variables"]:
                    del self.classes[obj_name]["variables"][attr]
                    if attr in self.classes[obj_name]["variables"].get("<attr>", []):
                        self.classes[obj_name]["variables"]["<attr>"].remove(attr)
                elif attr in self.classes[obj_name]["methods"]:
                    del self.classes[obj_name]["methods"][attr]
                    if obj_name in self.special and attr in self.special[obj_name]["methods"]:
                        del self.special[obj_name]["methods"][attr]
                else:
                    self.error(18, attr)
                return
    
            self.error(18, obj_name)
            return
    
        # plain name - object instance, variable, function, class, or library
        base = arg
        if base in self.class_callers:
            self.class_callers.pop(base)
            if base in self.objects:
                del self.objects[base]
            if base in self.variables:
                del self.variables[base]
            internal = "<" + base + ">"
            if internal in self.variables:
                del self.variables[internal]
            if base in self.constants:
                del self.constants[base]
        elif base in self.variables:
            del self.variables[base]
            if base in self.constants:
                del self.constants[base]
        elif base in self.functions:
            del self.functions[base]
        elif base in self.classes:
            del self.classes[base]
            if base in self.special:
                del self.special[base]
        elif base in self.library or base in self.name_library:
            lib_key = self.name_library.get(base, base)
            if lib_key in self.library:
                self.library.remove(lib_key)
            rename = self.library_name.pop(lib_key, None)
            if rename is not None:
                self.name_library.pop(rename, None)
            if lib_key in self.nplibs:
                del self.nplibs[lib_key]
            if lib_key in self.nplibs_acc:
                del self.nplibs_acc[lib_key]
        else:
            self.error(18, base)
            
    def run_injected_method(self, name, **dynamic_args):
        """
        Runs a method a library has registered for injection into veyl's own
        execution lifecycle (e.g. debug's screen clear / interface renderer),
        rather than the normal instruction-triggered dispatch path.
        Builds a fresh library instance so it reflects current live state (same
        pattern as ordinary library calls), looks up the registered method and
        its declared extra argument names, and calls it.
        """
        lib = libraries(**self.__dict__)
        injections = lib.get_injections()
        if name not in injections:
            return None
        entry = injections[name]
        method = entry["method"]
        call_args = {a: dynamic_args[a] for a in entry["args"] if a in dynamic_args}
        return method(**call_args)
    
    def parse_delete_target(self, arg):
        """
        Parses a delete target like arrays[0][1]["key"] into a base variable
        name and an ordered list of raw (unevaluated) accessor expressions,
        e.g. ("arrays", ["0", "1", '"key"']). Returns (base, []) if there are
        no brackets at all (a plain name).
        """
        arg = arg.strip()
        if "[" not in arg:
            return arg, []
        base, rest = arg.split("[", 1)
        rest = "[" + rest
        accessors = []
        depth = 0
        current = ""
        in_string = None
        i = 0
        while i < len(rest):
            ch = rest[i]
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
            if ch == "[":
                depth += 1
                if depth == 1:
                    current = ""  # start fresh, don't include the opening bracket
                    i += 1
                    continue
            if ch == "]":
                depth -= 1
                if depth == 0:
                    accessors.append(current)
                    current = ""
                    i += 1
                    continue
            current += ch
            i += 1
        return base.strip(), accessors
        
    def process_sse(self, code, types="syntax"):
        data = syntax_encloser.Data(self)
        # this is a beta feature, only library has functionality for Custom Module Injections
        if types == "syntax":
            sse = syntax_encloser.SyntaxSSE(data, code)
            
        elif types == "class":
            sse = syntax_encloser.MethodSSE(data, code)
            
        elif types == "value":
            sse = syntax_encloser.ValueSSE(data, code)
            
        elif types == "library":
            sse = syntax_encloser.LibrarySSE(data, code) # for now, only this one has functionality
        
        elif types == "deep":
            sse = syntax_encloser.DeepSA(data, code)
        
        sse.parse()
        
        
        
# This comment right here is only used to copy, i uncomment the lines and copy them to place somewhere in the code later

#if not self.attempt:
#    print("\033[31mTraceback(most_recent_call_back):\033[0m")
#    for i in self.traceback:
#        print(f"    TB - [ File `<{self.path / Path(self.file_name).with_suffix(self.file_extension)}>` line: {self.traceback[i]}, in {i} ],")
#    print(f"    TB - [ File `<{self.path / Path(self.file_name).with_suffix(self.file_extension)}>` TB found > line [{self.og_c}]: {self.Instructions[self.cnt]} in {i} ]")
#    print(f"\nError: ")
#    self.Errors["Error"] = True
#    return None
        