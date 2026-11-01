# LPy Compiler & Execution Environment

A robust command-line interface (CLI) and sandboxed execution driver for the **LPy** programming language. This script serves as the orchestrator for the compiler pipeline—handling lexical analysis, parsing, Python AST lowering, and safe code execution.

## Features

- **End-to-End Pipeline:** Lexes, parses, and lowers custom LPy source code into clean, unparsed standard Python AST.
- **Sandboxed Execution:** Executes the generated Python code in an isolated memory buffer using `exec()`, safely redirecting and capturing `stdout` streams.
- **Pre-baked Runtime Helpers:** Exposes a native domain layer directly to the execution sandbox (including mock data streams like `get_user`, `load_roster`, `data`, and system macros like `open_directory`).
- **Dual Execution Models:** Supports both compiling directly to a standalone `.py` script and executing source code on-the-fly directly in-memory.
- **Detailed Diagnostics:** Comprehensive exception tracking capturing exact compiler backend tracebacks or sandboxed execution errors.

## Prerequisites

Before running the driver script, make sure your project has the required companion modules available in your Python path:
- `lexer` (containing the `Token` layout)
- `parser` (containing the `parse` evaluation engine)
- `lowering.ir_to_python_ast` (containing the `lower_program` routine)

## Usage

You can interface with the environment directly through your terminal terminal.

### 1. Verification & Test Mode
Run the built-in sanity test to verify your compiler context and sandbox components work out-of-the-box:
```bash
python main.py -t
```
*(This triggers an internal code snippet passing mock user data to automated folder allocation targets).*

### 2. Live In-Memory Execution
Execute an `.lpy` file directly in memory and stream the console outputs without producing any artifact files:
```bash
python main.py path/to/script.lpy
```

### 3. Compilation to a Python File
Lower your custom source code into a portable, standard `.py` script asset:
```bash
python main.py path/to/script.lpy -o output_compiled.py
```

## CLI Reference

```text
usage: main.py [-h] [-o OUTPUT] [-t] [source_file]

LPy Compiler CLI & Test Runner

positional arguments:
  source_file           Path to the .lpy source file

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Path for the compiled output script.py
  -t, --test            Run a quick internal execution test
```

## Architecture Notes

- **Recursion Safety:** The engine aggressively overrides Python's default stack boundaries (`sys.setrecursionlimit(50000)`) to comfortably parse deeply nested code trees.
- **Global Sandbox Context:** The isolated runtime maps local definitions into a structured global state map to handle context evaluation during live execution blocks.
