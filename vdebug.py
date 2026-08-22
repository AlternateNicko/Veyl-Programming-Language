from pathlib import Path

class debug():
    def __init__(self, bool_debug):
        self.debug = bool_debug
    
    def print_functions(self, code):
        if not self.debug:
            return
        
        self.eps = code
        print(f"\nDEB: [ functions: ")
        if self.eps.functions:
            for name in self.eps.functions:
                print()
                print(name)
                for f in self.eps.functions[name]:
                    if "block" in f:
                        print("code")
                        tabs = 0
                        for i, c in enumerate(self.eps.functions[name][f]):
                            if c.endswith("}") or c.startswith("}"):
                                tabs -= 1
                            c = ("    " * tabs) + c
                            print(f"{i:<3}", ">>>", c)
                            if c.endswith("{") or c.startswith("{"):
                                tabs += 1
                              
                    else: print(f + ":", self.eps.functions[name][f])
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
        self.eps = code
        print("\nDEB: [ classes")
        if self.eps.classes:
            for name in self.eps.classes:
                print(name)
                for f in self.eps.classes[name]:
                    print(self.eps.classes[name][f])
        
        if self.eps.objects:
            for name in self.eps.objects:
                print(name)
                for f in self.eps.objects[name]:
                    print(self.eps.objects[name][f])
        print("]")
        
    def print_init(self, code):
        if not self.debug:
            return
        self.eps = code
        print(f"\n\n—Debug—————————————————————————————————————————————————————————\
        \n DEB: [ File path: {self.eps.path / Path(self.eps.file_name).with_suffix(self.eps.file_extension)} ]\
        \nDEB: [ Variables:")
        for i in self.eps.variables:
            print(f"{'constant ' if self.eps.variable_info[i]['constant'] else 'variable '} {str(self.eps.constants[i][0]):<5} {str(self.types(self.eps.variables[i])):<5} {str(i)+':':<10}{str(self.eps.variables[i])}")
    
    def print_libraries(self, code):
        if not self.debug:
            return
        self.eps = code
        print("_______________________________________________________________")
        print("DEB: [ Libraries:\
        \nName       |Root library| module")
        for imported, name in zip(self.eps.library, list(self.eps.library_name.values())):
            print(f"{name:<10} | {imported:<10} | {None if imported not in list(self.eps.nplibs.keys()) else self.eps.nplibs[imported]}")