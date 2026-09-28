from pathlib import Path

class debug():
    def __init__(self, bool_debug):
        self.debug = bool_debug
    
    def print_functions(self, code):
        if not self.debug:
            return
        
        self.vey = code
        print(f"\nDEB: [ functions: ")
        if self.vey.functions:
            for name in self.vey.functions:
                print()
                print(name)
                for f in self.vey.functions[name]:
                    if "block" in f:
                        print("code")
                        tabs = 0
                        for i, c in enumerate(self.vey.functions[name][f]):
                            if c.endswith("}") or c.startswith("}"):
                                tabs -= 1
                            c = ("    " * tabs) + c
                            print(f"{i:<3}", ">>>", c)
                            if c.endswith("{") or c.startswith("{"):
                                tabs += 1
                              
                    else: print(f + ":", self.vey.functions[name][f])
        print("]")
    
    
    def types(self, value, mode="c"):
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
                return "list"
            elif isinstance(value, tuple):
                return "tuple"
            elif isinstance(value, dict):
                return "dict"
            elif isinstance(value, set):
                return "set"
            else:
                # supports any type
                new_type = str(type(value)).split(" ", 1)[1][1:-2]
                return new_type
                
    def print_classes(self, code):
        if not self.debug:
            return
        self.vey = code
        print("\nDEB: [ classes")
        if self.vey.classes:
            for name in self.vey.classes:
                print(name)
                for f in self.vey.classes[name]:
                    print(self.vey.classes[name][f])
        
        if self.vey.objects:
            for name in self.vey.objects:
                print(name)
                for f in self.vey.objects[name]:
                    print(self.vey.objects[name][f])
        print("]")
        
    def print_init(self, code):
        if not self.debug:
            return
        self.vey = code
        print(f"\n\n—Debug—————————————————————————————————————————————————————————\
        \n DEB: [ File path: {self.vey.path / Path(self.vey.file_name).with_suffix(self.vey.file_extension)} ]\
        \nDEB: [ Variables:")
        for i in self.vey.variables:
            print(f"{'constant ' if self.vey.variable_info[i]['constant'] else 'variable '} {str(self.vey.constants[i][0]):<5} {str(self.types(self.vey.variables[i])):<5} {str(i)+':':<10}{str(self.vey.variables[i])}")
    
    def print_libraries(self, code):
        if not self.debug:
            return
        self.vey = code
        print("_______________________________________________________________")
        print("DEB: [ Libraries:\
        \nName       |Root library| module")
        for imported, name in zip(self.vey.library, list(self.vey.library_name.values())):
            print(f"{name:<10} | {imported:<10} | {None if imported not in list(self.vey.nplibs.keys()) else self.vey.nplibs[imported]}")