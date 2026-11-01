import ast

def generate_code(py_ast, filename="<lpy>"):
    
    return compile(py_ast, filename=filename, mode="exec")
