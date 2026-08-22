# SPECIAL SYSTEM VALUES (SSv)
# SPECIAL SYNTAX ENCLOSER (SSE)
# enclosers - <simple> <<deep_level>> $<<library_level>>
import os

class Data:
    def __init__(self, veyl):
        self.__dict__ = veyl.__dict__ # gets all variable instances in one line due to the sheer amount of variables

# 5 classes that represents 5 differeny special system values
# 1. class method names

class MethodSSE:
    def __init__(self, data, line):
        self.__dict__ = data.__dict__
        self.line = line.strip() # the main method name
        # method names (sse) are defined with a <encloser>
    
    def parse(self):
        line = self.line
        pass # future use in v1.1.0

# 2. special system values

class ValueSSE:
    def __init__(self, data, line):
        self.__dict__ = data.__dict__
        self.line = line.strip()
    
    def parse(self):
        line = self.line
        pass

# 3. special system syntax

class SyntaxSSE:
    def __init__(self, data, line):
        self.__dict__ = data.__dict__
        self.line = line.strip()
    
    def parse(self):
        line = self.line
        pass

# 4. Deep system accessor

class DeepSA:
    def __init__(self, data, line):
        self.__dict__ = data.__dict__
        self.line = line.strip()

    def parse(self):
        line = self.line
        pass
# 5. Library to Interpreter system accessor

class LibrarySSE:
    def __init__(self, data, line):
        self.__dict__ = data.__dict__
        self.line = line.strip()
        self.commands = {} # for custom direct small commands
   
    def parse(self):
        line = self.line[3:]
        pass