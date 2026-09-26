# VEYL cli entry point, having different functionality in one

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))

import os
import argparse
import time

from veyl import VEY
# main entry function

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("program", nargs="?", type=Path,
    help = "Executes a veyl (.vey) program executable file, must contain veyl approved syntax"
    )
    parser.add_argument("-c", "--command", nargs=1,
    help = "Executes a small snippet of code directly"
    )
    
    # help program
    # either opens up a help terminal
    # or depending on given argument, it gives a description about them
    
    parser.add_argument("-v", "--verbose", action="store_true",
    help = "A flag that gives extra trace and output information for your language"
    )
    parser.add_argument("-V", "--version", action="store_true",
    help = "Returns the language version, info, cli version, and python version"
    )
    parser.add_argument("-H", "--Help", action="store_true",
    help = "The languages helper function"
    ) # THIS ONE IS A BIG ONE SO IT STILL HAS NO USE
    
    # program testing/diagnostic
    # 1st argument is always a .vey program
    parser.add_argument("-ch", "--check", nargs=1, type=Path,
    help = "Runs the program without executing the code, this checks for accuracte syntax"
    )
    parser.add_argument("-d", "--debug", nargs=1, type=Path,
    help = "Debugs your program by flag, or Veyl itself for the development of the language"
    )
    parser.add_argument("-t", "--test", nargs=1, type=Path,
    help = "Tests your program by flag, or Veyl itself for the development of the language"
    )
    parser.add_argument("-cwd", "--cwd", action="store_true",
    help = "Just a quick way of knowing what current working directory is the CLI on"
    )
    parser.add_argument("-tm", "--time", action="store_true",
    help = "Gives an accuracte timer of execution time whenever running a program."
    )
    parser.add_argument("-pr", "--progress", action="store_true",
    help = "Shows a progress bar during Veyl execution, requires third party library, tqdm"
    )
    
    args = parser.parse_args()
    
    # passes it to a argument dispatch
    dispatch_args(args.__dict__)

def dispatch_args(args):
    """
    handles all the argument conditions and executes them depending on functionality and value
    """
    if args["cwd"]:
        print(os.getcwd())
        return
    code = None
    timer = False
    progress = False
    
    cli_config = {
        "verbose": args["verbose"],
        "debug": False if args["debug"] is None else args["debug"],
        "test": False if args["test"] is None else args["test"]
    }
    isexecutable = False
    if all(a is None for a in list(args.values())):
        interpreter()
    if args["program"] is not None:
        # runs a veyl program, any text format aslong as it has veyl's syntax
        isexecutable = True
        code = args["program"].read_text(encoding="utf-8")
    if args["version"]:
        version_check(VEY(""))
    if args["time"]:
        timer = True
    if args["progress"]:
        progress = True
    if args["command"] is not None:
        command(args["command"])
    if args["check"] is not None:
        check_program(args["check"][0].read_text(encoding="utf-8"))
    if isexecutable:
        execute_program(VEY(code, cli_config=cli_config), timer, progress)
        

def execute_program(veyl_program, timer: bool, progress: bool):
    try:
        if timer:
            start = time.perf_counter()
        veyl_program.execute(hastqdm=progress)
        if timer:
            est = time.perf_counter() - start
            print(f"\nEST: {est:.4}s")
    except Exception as e:
        veyl_program.error(1000, type(e).__name__, e)
    return
    
def version_check(veyl):
    print(f"""
Veyl Interpreter version: {veyl.version}
Veyl Version Information: {veyl.version_info}
Veyl CLI version: {veyl.cli_version}
Python Version: {sys.version}
    """)

def command(line):
    line = line[0]
    if (not line.startswith('"') and not line.endswith('"')) or (not line.startswith("'") and not line.endswith("'")):
        return None
    vey = VEY(line[1:-1].strip())
    vey.execute()
    return
    
def check_program(code):
    try:
        print("\nProgramming Checker Interface\n- Passing programm")
        vey = VEY(code, io=False)
        print("- Running program...")
        vey.execute(hastqdm=True)
        print("\nRunned succesfully and exit without any errors.\nReady for execution")
    except Exception as e:
        print("\nRunned and exited with an Error")
        vey.error(1000, type(e).__name__, e)
    return
    
def interpreter():
    reference = VEY("")
    print(f"""
Veyl Interactive Intrepreter
Veyl Interpreter version: {reference.version}
Veyl Version Information: {reference.version_info}
Veyl CLI version: {reference.cli_version}
Python Version: {sys.version}
    """)
    vey = VEY("")
    try:
        code = ""
        tab = 0
        while True:
            line = input(">>> ")
            if line == "-exit":
                break
            if line == "-check":
                print(code)
                continue
            if line == "-clear":
                code = ""
                continue
            if line == "-run":
                vey = VEY(code, {})
                vey.execute()
                continue
            if line == "-save":
                path = input("Save Path Directory >>> ")
                with open(path, "w") as save_file:
                    save_file.write(code)
            elif line == "-load":
                path = input("Load Path Directory >>> ")
                with open(path, "r") as load_file:
                    code = load_file.read()
            
            else:
                if line.startswith("{") and "}" not in line or line.endswith("{") and "}" not in line:
                    tab += 1
                if line.startswith("}") and "{" not in line or line.endswith("}") and "{" not in line:
                    tab -= 1
                code += " " * tab
                code += line + "\n"
                try:
                    print(vey.eval(code, {}, vey.variables))
                except Exception as e:
                    vey.error(1000, type(e).__name__, e)
                try:
                    vey = VEY(code, {})
                    vey.execute()
                    continue
                except Exception:
                    continue
                    
    except Exception as e:
        reference.error(1000)
        getaway = input("Input a emergency save file name: ")
        with open(getaway + ".vey", "w") as file:
            file.write(code)