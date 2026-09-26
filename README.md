# Veyl-Lang

## About
Veyl-Programming Language (or Veyl) is a expiremental language in 15th November of 2024. It was a educational project when I first started to learn python, and helped me learn debugging and diagnostic skills, and software development.

It is a interpreter language with each line read by a program counter. And has its own unique syntax, while the structure are still recognizable, simple, and familiar.
It is inspired by python and C/C++ syntax, all programs in this repository are coded on python.

## Setup
After installation (either git clone, or downloading the zip file), immidietly rename the folder to "VeylPL" as all program expects the main project directory to be VeylPL.
It is required to have Python version 3.9 and above and the third party libraries, autocorrect and tqdm.
Main Setup from top (first) to bottom (last)

Download one of the releases, or clone it using "git clone"
```shell
git clone https://github.com/AlternateNicko/Veyl-Programming-Language.git
```
- Change Directory:
```shell
cd Veyl-Programming-Language
```
or path to the project directory

- Directory name change:
    "Veyl-Programming-Language" -> "VeylPL"
- Veyl CLI entry point setup:
```shell
pip install -e .
```

## How to run my own programs
To create your own program, you need to create a small python program that will act as the API with the code you have written for veyl in python.
example (you can use):
```python
from VeylPL.veyl import VEY

code = r"""
output("Hello, World!")
"""

vey = VEY(code)
vey.execute()
```

it is recommended to use raw multi lined strings, raw strings for unicode escape character support, and multi lined for simplicity and readability.
For other example, this is the recommended sample code for running programs
Advanved example:
```python
from VeylPL.veyl import VEY
from VeylPL.vdebug import debug

code = r"""
a = 25
b = 50

output(a + b)
"""

vey = VEY(code)
vey.execute()

vdb = debug(1)
vdb.print_init(vey)
vdb.print_functions(vey)
vdb.print_classes(vey)
vdb.print_libraries(vey)
```

## API for custom user made modules
This is a feature where you can pass a python module (mostly required a python object like a function or class) inside veyl as a third party library.
The set up itself is hard as it has to follow a strict class structure as a simple API entry.
Sample code:
```python
# add other library imports here
...

class mylib:
    def __init__(self, data):
        self.__dict__ = data.__dict__
        self.veyl = data
    
    def process(self, instr, variant="ol"):
        # name "process" is required because veyl expects a method named process,
        # a 2nd argument named "variant" with 2 different mode, ol (one line), av (variable assignment)
        if variant == "ol":
            self.oneline_dispatch(...)
        else:
            self.assign_variable_dispatch(...)
    # dispatch methods are added here
```
in the main program where veyl codes are executed in python, add this code
```python
import MyLibrary
module = {
    "mylib": MyLibrary.mylib
}

vey = VEY(code, module)
vey.execute
```
inside the veyl program, you can do this now.
```
import mylib

mylib.methods(...)
var = mylib.methods(...)

output(mylib.methods(...))
```

check out library/Test.py for example class structure.

## Core syntax elements
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
usage of public and private are immidietly different whenever the program is inside a class.

If you want to know more about veyl syntax and more examples.
In veyl:
```
import help

help.init()
```
In veyl CLI:
```
veyl --helps
```
or if you want a more clearer explanation without commands or codes, check out "veyl-encyclopedia.md", it includes keywords, built ins (functions, method, standard libraries), and custom unique features. All with descriptions, example use, error statements/conditions, and more.
The encyclopedia includes unique veyl features that you are unfamiliar with other language, and offers you a clear explanation.

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
## Things to Note
___
- This code was first developed around November of 2024, Where I only had been learning python for about 3 months.
- This transpiled language is a hobby language and project, This project was develop with the purpose of teaching me more about python, programming, debugging, and more
- There are parts of the Veyl source code that were written a year ago, where codes weren't structured properly, and some were written a few months ago, when I finally came back to work on to this language, which are structured neatly while still following the design of the program when i first written it.

___
## What to expect
___
- you should expect tons of bugs, errors, and parsing problems. This language is still not bug free
- The language is getting bug fixes and development everyday, updates frequently every week, but sometimes it won't be quick, as I (main contributor) am also busy with other things.
- Most updates are bug fixes, and major updates only drops whenever there are minimal bugs left that doesn't occur majorly in most programs
- Veyl version 2.0.0 might take months or years, as I have plans to rewrite everything all with my current knowledge in programming.
- Testing takes long, as most tests works while some tests doesn't. Each tests are Veyl test programs, most of the time, I always test after debugging, some of these programs works, while others doesn't. So some bug fixes makes little difference

___
## Updates
___
"veyl.py" is where the main source code is located.
Veyl gets updates every 1-2 weeks for bug fixes, monthly for features

• Minor updates - Veyl will get small features and bug fixes with this updates, Minor updates also includes updates outside of Veyl.py, built in libraries, or others will also get updates.
• Major updates - Veyl gets updates that includes huge features, additions, bug fixes, and even reworks. These updates are mostly rare, sometimes just every few months or a year if I have the time. This type of update is important as it could majorly improve speed, optimizations, future development, or syntaxes.

___
## Extra's
___
[VeylBinder](https://github.com/AlternateNicko/VeylBinder-Veyl2Python)