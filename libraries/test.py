class Test:
    def __init__(self, veyl):
        self.__dict__ = veyl.__dict__
        self.veyl = veyl
    
    def process(self, inst, variant="ol"):
        if variant == "ol":
            self.one_line(inst)
        else:
            self.assign(inst)
    
    def one_line(self, inst):
        inst = self.veyl.special_split(inst, ".", ("'", '"'), ("'", '"'), limit=1)[1].strip()
        
        if inst.startswith("test_print(") and inst.endswith(")"):
            arg = inst[11:-1].strip()
            val = self.veyl.eval(arg, {}, self.variables)
            print(val)
        return []
            
    def assign(self, inst):
        inst = inst.split("=", 1)
        left = inst[0].strip()
        right = inst[1].strip()
        main = self.veyl.special_split(right, ".", ("'", '"'), ("'", '"'), limit=1)[1].strip()
        if main.startswith("test_add(") and main.endswith(")"):
            params = main[9:-1].strip().split(",", 1)
            a = self.veyl.eval(params[0], {}, self.variables)
            b = self.veyl.eval(params[1], {}, self.variables)
            self.variables[left] = a + b
        return tuple([self.variables])