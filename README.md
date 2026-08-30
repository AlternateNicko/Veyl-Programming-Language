![Static Badge](https://img.shields.io/badge/Veyl--Programming--Language-text)
![GitHub Release](https://img.shields.io/github/v/release/AlternateNicko/Veyl--Programming--Language)
![GitHub Created At](https://img.shields.io/github/created-at/AlternateNicko/Veyl--Programming--Language)
![GitHub commits since latest release](https://img.shields.io/github/commits-since/AlternateNicko/Veyl--Programming--Language/latest)
![GitHub last commit](https://img.shields.io/github/last-commit/AlternateNicko/Veyl--Programming--Language)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/AlternateNicko/Veyl--Programming--Language/total)
![GitHub top language](https://img.shields.io/github/languages/top/AlternateNicko/Veyl--Programming--Language)
![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/AlternateNicko/Veyl--Programming--Language)
![GitHub Release Date](https://img.shields.io/github/release-date/AlternateNicko/Veyl--Programming--Language)
___
# About
___

Veyl-Lang (or Veyl) is a transpiled interpreter language writen in python.

Veyl includes an easy to read syntax, with all the basic keywords and features.
Simple language features like declarations, instances, keywords, built ins, and OOP (Object Oriented Programming)
And many more features Veyl includes,
The followings are:
- custom library injections
- unique built ins
- robust accessor systems (using `public` `private`)

Veyl's source code is written in Python

___
# Syntax
___

Keywords:
- if
- else if
- else
- while
- for
- private
- public
- func
- call
- attempt
- catch
- import
- class
- inherit
- load
- sync
- desync
- open
- break
- continue
- return
- global
- from
- pass
- const

• Other keywords (mostly used in conditions, loops, etc)
- and
- or
- in
- not
- from
- as

• datatypes
used optionally in function return types, and variable types
- int - intergers
- str - string (mutable and immutable)
- float - floating point numbers
- bool - boolean
- array - fixed size sequence of elements
- tuple - an immutable, fixed size of sequence of elements
- vector - dynamic arrays (not fixed size) with dynamicly typed elements
- map (hash map)
- set (hash set)
- None (usually defined as void in keywords)

• Operators
+ Addition
- Subtraction
* Multiplication
/ Division
% Modular division
/< Integer division
** Exponential
++ Increment
-- Decrement
== Is Equal
!= Is Not Equal
< Less than
> Greater than
<= Less or equal than
>= Greater or equal than

___
# core syntax elements
___
• Code blocks - These are enclosed with curly brackets { }, but curly brackets can also be used in map data types

• /< - this symbol is defined as a comment

• Built in functions - there are built in functions and methods used for easier variable assignments and value manipulations
    - Additionally, function calls are defined using "call" prefix to prevent name collisions
    - But functions can be called without need of "call" by doing "using" keyword

• Case-Sensitive language - uppercase and lowercase characters acts differently

• white spaces are ignored - Tabs, spaces, and lines without any codes are ignored and skipped

• OOP support - There are multiple syntaxes used for Object Oriented Programming
1. "class" - the main keyword to define a object
2. <const> - the "construction" name, used in
    - < > are special syntax enclosers, pre release for 1.0.6 update, and will gain full functionality in 1.1.0 and above
3. public - Accessible outside of class
4. private - Class only access, any external access or calls are not allowed

• additionally, "public" and "private" can change a function or variable scope visibility
with "public" changing visibility to the whole program no matter what scope the program is in.
While "private" changes visibility strictly to the current scope only
```python
private func method()
{
    ...
}
```
or a
```python
public func method()
{
    ...
}
```

constructors must be defined as "public" or else the class main constructor cannot be accessed,
```
public func <const>()
{
    public name = "Bartolomew"
}
```

usage of public and private are immidietly different whenever the program is inside a class.

3. "inherit" - The constructor class is also where "inherit" keyword is mostly used, "inherit" gets the attributes, methods, and other more class object information from a Parent class, which is usually defined as
```python
class Child_class(Parent_class1, Parentclass2, ...)
```
___
# Libraries
___
Veyl supports custom user built libraries that it can add within the code, and treats it as one
This can be either importing .vey codes
or building your own library (in /library directory) which uses python programs or even deeper, any type of program as long as it follows these instructions
```python
#add this code to /library directory
import ... #import any libraries, modules, etc as dependencies

class any_library_name:
    #the class constructor method must follow this arguments and code
    def __init__(self, data):
        self.__dict__
        self.veyl = data # data is an object pointing to the current veyl class object (self)
        ...
    # this method must also be added
    def process(self, line, variant="ol"):
        # all values must be returned
        if variant == "av": # meaning assign variable
            return self.variable_assignment(line)
        else:
            return elf.one_line_instruction(line)
```
Important notices
- self.process() must be always defined as Veyl expects a method named process() with 2 arguments, line and variant.
- variants are 2 types,
- 1. "av" means Assign to Variable, this is defined when there is a code like this
`variable = library.method()`
where "library" is the imported library, "method" is the method of that library (or can be anything like variable assignlents)
and "variable" as the variable name
- name of module cannot overwrite the names of other built in libraries

___
# Setup
___
The setup is simple, you can open up NBIDE.py, a simple notebook like IDE (doesn't execute), then after writing the code, save it as .vey, a file extension for Veyl
then at interactive_shell, type
`veyl your_file.vey`
to setup Veyl, you have to first make a .py python program outside of the directory where Veyl (VEYL) is stored.
then write this code
```python
from VeylPL.veyl import VEYL

instructions = """
/< put your code here
"""
module = {}
veyl = VEYL(instructions, module)
results = veyl.execute()
```
• Key pointers of this code
  1. from VeylPL.veyl import VEYL - if VeylPL in "from VeylPL.veyl..." is a different name, change it immidietly
  2. instructions - must be a doc string
  3. module dictionary - this is where special libraries are stored inside /library directory.
  4. VEYL class - the class always expects 1 or 2 arguments, the most important is the "instructions" argument, module argument is optional if you didn't include any libraries from /library directory
  5. veyl.execute() - doesn't actually need variable assignments.

for simple debugging, write this on top of the code
```python
from VeylPL.vdebug import debug
```
then do
```python
veyl = VEYL(instructions) # or where VEYL() gets defined, the code in the following must be added after veyl
ndb = ndebug(True) # False for debug mode off
ndb.print_init(veyl) # The first print, this prints the variables and values and information
ndb.print_functions(veyl) # prints out the each functions, what their code block is, arguments, and information
ndb.print_classes(veyl) # prints out the classes and its attributes, methods, and inherited class
```

• This is usefull for simply debugging after code execution to check informations about the program and any issues that needed to be fixed

And For special modules in /library, do this
data_lib for example

```python
from VeylPL.veyl import VEYL
from VeylPL.library.data_lib import class_module

instructions = """
/< put your code here
"""
module = {
    "datalib": class_module,
    ...
}
veyl = VEYL(instructions, module)
results = veyl.execute()
```

• key pointers:
- module must have a key with a string, and a name that will be used as the name of the library inside Veyl libraries
- Directory must match (if the downloaded github .zip file has a different name, change the name to VeylPL)
- "from VeylPL.library.data_lib" must be imported, and must be the main class
- the module must have the value as a instance of the class object, and don't run the class initialize method

• Where to find example?
- Check out `built_in_libraries` for example, it uses the same layout, but mostly coded for multiple libraries parsing

___
# Example Veyl Codes
___

• Simple Syntax Examples
```
/< double slash as comments
output("Hello, World!") /< hello world example
user_input = input("Type in anything: ")
output(user_input)
vect = [2, 6, 4, 9, 8, 1, 3, 0, 5, 7] /< Dynamic arrays
tup = (1, 2, 3, 4, 5)
map hash_map = {"a": 10, "b": 20, "c": 30} /< defined hash maps
sets = {1, 2, 3, 4, 5}

/< Adding a datatype at the start of a variable or function is completely optional
/< it is immidietly defined as "<any>", recognizing each datatypes and any datatypes
word = "Hello"
int number = "100"

bif = sort(vect) /< built ins
if (hash_map["a"] == 10) && (tup[4] == 5)
{
    output("This has 10 and 5")
}
/< Curly brackets as code blocks, and functional if statement condition
```
• Calculator code
```
/< Calculator
num_a = input("Enter the first number >>> ").as(int)
num_b = input("Enter the second number >>> ").as(int)
operation = input("Enter an operation (+, -, *, /) >>> ")

result = 0

/< Indentation isn't necessary for code block definition
/< mostly use for code organization, easy readability, and neatness

if (operation == "+") {
    result = num_a + num_b
}
else if (operation == "-") {
    result = num_a - num_b
}
else if (operation == "*") {
    result = num_a * num_b
}
else {
    result = num_a * num_b
}
output("Result is:", result)
```

• Bubble sort
```
public vector func bubble(lst) </ defines a public function named bubble with a vector return type
{
    lens = length(lst)
    for i in range(lens)
    {
        for k in range(lens - 1)
        {
            x = lst[k]
            y = lst[k + 1]
            
            if (x > y)
            {
                load lst[k] = y
                load lst[k + 1] = x
            }
        }
    }
    return lst
}

unsorted = [2, 4, 6, 3, 8, 1, 10, 9, 7, 5]
sorted = call bubble(unsorted_list)
```
• For loop
```
import time
rename time as t

/< Prints from 1 to N
number = input("enter maximum range > ").as(int)

start = t.time()

for cnt in range(1, number)
{
    output(cnt)
}

end = t.time()
est = end - start

output(f("Estimated taken time {est}"))
```
• Guess the number
```
import random
rename random as r

output("Welcome to guess the number game!")
output("guess a number from 1 to 100 > ")

generated = r.randint(1, 100)
while (True) {
    answer = input("You: ").as(int)
    if (answer > generated)
    {
        output("> Too high")
    }
    else if (answer < generated)
    {
        output("> Too low")
    }
    else
    {
        output("You guessed correctly!")
        output("The answer was: ", generated)
        break
    }
}
```

___
# Things to Note
___
- This code was first developed around November of 2024, Where I only had been learning python for about 3 months.
- This transpiled language is a hobby language and project, This project was develop with the purpose of teaching me more about python, programming, debugging, and more
- There are parts of the Veyl source code that were written a year ago, where codes weren't structured properly, and some were written a few months ago, when I finally came back to work on to this language, which are structured neatly while still following the design of the program when i first written it.
___
# What to expect
___
- you should expect tons of bugs, errors, and parsing problems. This language is still not bug free
- The language is getting bug fixes and development everyday, updates frequently every week, but sometimes it won't be quick, as I (main contributor) am also busy with other things.
- Most updates are bug fixes, and major updates only drops whenever there are minimal bugs left that doesn't occur majorly in most programs
- Veyl version 2.0.0 might take months or years, as I have plans to rewrite everything all with my current knowledge in programming.
- Testing takes long, as most tests works while some tests doesn't. Each tests are Veyl test programs, most of the time, I always test after debugging, some of these programs works, while others doesn't. So some bug fixes makes little difference
___
# Updates
___
"veyl.py" is where the main source code is located.
Veyl gets updates every 1-2 weeks for bug fixes, monthly for features

• Minor updates - Veyl will get small features and bug fixes with this updates, Minor updates also includes updates outside of Veyl.py, built in libraries, or others will also get updates.
• Major updates - Veyl gets updates that includes huge features, additions, bug fixes, and even reworks. These updates are mostly rare, sometimes just every few months or a year if I have the time. This type of update is important as it could majorly improve speed, optimizations, future development, or syntaxes.
