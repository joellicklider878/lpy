import sys
import os
import ast
import argparse
import traceback  # FIXED: Added missing import for exception reporting
import io
import contextlib

from lexer import Token 
from parser import parse
from lowering.ir_to_python_ast import lower_program
sys.setrecursionlimit(50000)

# Runtime functions available to the language environment
class User:
    def __init__(self, name, status):
        self.name = name
        self.status = status
    
def get_user():
    return User('Alice', 'active')
    
def get_users():
    return [
        User('Alice', 'active'),
        User('Bob', 'inactive'),
        User('Carol', 'active')
    ]

def load_roster():
    return [
        User('Alice', 'active'),
        User('Bob', 'inactive'),
        User('Carol', 'active')
    ]

# FIXED: Added parameters to prevent a NameError when values/records are passed
def data(values=None, records=None):
    avg = sum(values) / len(values) if values else 0
    csv_data = f"csv_dump_count:{len(records)}" if records else ""
    return avg, csv_data

def open_directory(user):
    name = user.name if hasattr(user, 'name') else user.get('name')
    print(f" opening directory: {name}")

def send_email(user):
    name = user.name if hasattr(user, 'name') else user.get('name')
    print(f"email sent to {name}")

# fully encapsulated run_lpy
def run_lpy(program_text: str) -> dict:
    # initialize the specific dict layout
    response = {
        "python": "",
        "output": "",
        "errors": []
    }

# 1. Compile phase: Translate Lpy source into Python source strings
    try:
        tokens = Token.lex(program_text)
        ir = parse(tokens)
        py_ast = lower_program(ir)

        # Mirroring the AST wrapping/normalization logic from your compile_and_export
        if hasattr(py_ast, 'node'):
            raw_module = py_ast.node
        else:
            raw_module = py_ast

        if not isinstance(raw_module, ast.Module):
            if hasattr(raw_module, 'body') and isinstance(raw_module.body, list):
                raw_module = ast.Module(body=raw_module.body, type_ignores=[])
            else:
                raw_module = ast.Module(body=[raw_module], type_ignores=[])

        ast.fix_missing_locations(raw_module)
        
        # Unparse the final safe module tree structure back into clean Python text
        generated_python = ast.unparse(raw_module)
        response["python"] = generated_python
        
        compiled_code = compile(generated_python, filename="<lpy_sandbox>", mode="exec")
        

    except Exception as compile_err:
        # Capture line numbers and crash logs if your compiler backend fails
        error_buffer = io.StringIO()
        traceback.print_exc(file=error_buffer)
        response["errors"].append(f"Compiler Error: {str(compile_err)}\n{error_buffer.getvalue()}")
        return response

    # 2. Execution phase: Run the generated Python and isolate output stream triggers
    stdout_buffer = io.StringIO()

    # python's exec() functions best when it can reference the active module
    sandbox_globals = globals().copy()
    
    # Expose runtime helpers (like get_user or data) directly into the execution sandbox
    sandbox_globals.update({
        "User": User,
        "get_user": get_user,
        "get_users": get_users,
        "load_roster": load_roster,
        "data": data,
        "open_directory": open_directory,
        "send_email": send_email,
        "__builtins__": __builtins__
    })

    try:
        # Redirect standard printing streams into our memory buffer
        with contextlib.redirect_stdout(stdout_buffer):
            # Compile the raw text blocks explicitly into an executable code object
            exec(compiled_code, sandbox_globals)

        response["output"] = stdout_buffer.getvalue()
        
    except Exception as exec_err:
        # Extract everything printed up until the script crashed
        response["errors"].append(f"Execution Error: {str(exec_err)}")

    return response

if __name__ == '__main__':
    # 1. Initialize the command line argument parser
    parser = argparse.ArgumentParser(description="LPy Compiler CLI & Test Runner")
    parser.add_argument("source_file", nargs="?", help="Path to the .lpy source file")
    parser.add_argument("-o", "--output", help="Path for the compiled output script.py")
    parser.add_argument("-t", "--test", action="store_true", help="Run a quick internal execution test")
    
    args = parser.parse_args()
    
    # 2. Quick Test Mode: Verifies run_lpy works out-of-the-box
    if args.test:
        print("--- Running Internal run_lpy() Test ---")
        test_code = """
user = get_user()
open_directory(user)
print("Hello from Lpy sandbox environment!")
"""
        result = run_lpy(test_code)
        print(f"Generated Python:\n{result['python']}")
        print(f"Captured Output:\n{result['output']}")
        if result['errors']:
            print(f"Errors:\n{result['errors']}")
        sys.exit(0)

    # 3. Guard against missing CLI file inputs
    if not args.source_file:
        parser.print_help()
        sys.exit(1)
        
    # 4. Check if the source code file exists
    if not os.path.exists(args.source_file):
        print(f"Error: Source file '{args.source_file}' not found.")
        sys.exit(1)
        
    # 5. Read the code contents from the source file
    with open(args.source_file, 'r', encoding='utf-8') as f:
        source_code_contents = f.read()
        
    # 6. If an output target is defined, compile and export a standalone file
    if args.output:
        print(f"Compiling {args.source_file} into {args.output}...")
        compile_and_export(source_code_contents, args.output)
        print("Compilation completed successfully!")
    else:
        # Otherwise, run it in-memory right in your terminal console
        print(f"Executing {args.source_file} directly in memory...")
        result = run_lpy(source_code_contents)
        if result['output']:
            print("\n--- Output ---")
            print(result['output'])
        if result['errors']:
            print("\n--- Errors ---")
            print("\n".join(result['errors']))
