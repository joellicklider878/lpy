from ir.builder import build_ir_from_lines

def parse(tokens):
    """
    Groups a flat token stream into discrete statement lists 
    and passes them to the IR compiler.
    """
    statements = []
    current_statement = []
    
    i = 0
    while i < len(tokens):
        t = tokens[i]
        
        # Check if a fresh declaration statement boundary is starting
        is_new_statement = False
        if t.type in ["DEFINE", "CALL", "IF", "OTHERWISE", "LOOP"]:
            is_new_statement = True
        elif t.type == "IDENTIFIER" and t.value in ["if", "otherwise", "from", "loop"]:
            is_new_statement = True
        elif t.type == "IDENTIFIER" and t.value == "for" and i + 1 < len(tokens) and tokens[i+1].value == "each":
            is_new_statement = True
            
        # Flush the gathered tokens if a new statement keyword is reached
        if is_new_statement and current_statement:
            statements.append(current_statement)
            current_statement = []
            
        current_statement.append(t)
        i += 1
        
    if current_statement:
        statements.append(current_statement)

    # Temporary fallback step: Convert token groups back to a format 
    # that your current build_ir_from_lines expects until it is refactored.
    # It ensures strings with spaces retain internal values cleanly.
    formatted_lines = []
    for stmt in statements:
        line_parts = []
        for tok in stmt:
            if tok.type == "STRING":
                # Re-wrap in quotes so your IR builder text processing logic sees it as a string
                line_parts.append(f'"{tok.value}"')
            else:
                line_parts.append(tok.value)
        formatted_lines.append(" ".join(line_parts))
        
    return build_ir_from_lines(formatted_lines)
