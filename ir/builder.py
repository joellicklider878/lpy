import re
from ir.nodes import *

def build_ir_from_lines(lines):
    clauses = []  # Holds compiled clauses/nodes
    last_plural = None  # Tracked variable contextual scope
    i = 0  # Initialized index iterator loop control

    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        # Handle Conditional syntax: if <var> is <status> then
        if line.startswith("if ") and " is " in line:
            if line.endswith("then"):
                match = re.match(r"if\s+(\w+)\s+is\s+(\w+)\s+then", line)
                if match:
                    var_name = match.group(1)
                    status_val = match.group(2)

                    # Create the node
                    node = IfStatusNode(var_name, status_val)
                    node.then_body = []
                    node.otherwise_body = []
                    
                    i += 1
                    current_body = node.then_body
                    nesting_depth = 1
                    
                    while i < len(lines) and nesting_depth > 0:
                        next_line = lines[i].strip()
                        if not next_line:
                            i += 1
                            continue
                        
                        # Monitor block depth changes
                        if next_line.startswith("if ") and next_line.endswith("then"):
                            nesting_depth += 1
                        elif next_line == "end":
                            nesting_depth -= 1
                            if nesting_depth == 0:
                                i += 1
                                break
                                
                        # Handle routing to the alternative branch at top nesting layer
                        if nesting_depth == 1 and next_line == "otherwise":
                            current_body = node.otherwise_body
                            i += 1
                            continue
                            
                        # FIXED: Skip passing block-level control keywords to line validator
                        if next_line != "otherwise" and next_line != "end":
                            sub_prog = build_ir_from_lines([next_line])
                            current_body.extend(sub_prog.clauses)
                        i += 1
                        
                    clauses.append(node)
                    continue
            else:
                match = re.match(r"if\s+(\w+)\s+is\s+(\w+)\s+then\s+(.*)", line)
                if match:
                    var_name = match.group(1)
                    status_val = match.group(2)
                    clauses.append(IfStatusNode(var_name, status_val))
                    i += 1
                continue

        if line.startswith("define"):
            parts = line.split(maxsplit=3)
            name = parts[1]
            expr = parts[3]
            
            target_np = NounPhrase(name)
            
            if (expr.startswith('"') and expr.endswith('"')) or (expr.startswith("'") and expr.endswith("'")):
                expr_value = expr[1:-1]
                expr_np = StringExpr(expr_value) if 'StringExpr' in globals() else IdentifierExpr(expr)
                expr_np.is_string = True
                expr_np.raw_value = expr
            else:
                expr_np = IdentifierExpr(expr)
                expr_np.is_string = False

            clauses.append(DefinitionClause(target_np, expr_np))
            last_plural = target_np
            i += 1
            continue

        if line.startswith("from"):
            parts = line.split()
            source = parts[1]
            target = parts[3]
            source_np = NounPhrase(source)
            target_np = NounPhrase(target, is_pronoun=True)

            if "where" in parts:
                w = parts.index("where")
                field = parts[w+1]
                relation = parts[w+2]
                value = parts[w+3]
                cond = Condition(NounPhrase(field), relation, IdentifierExpr(value))
            else:
                cond = None

            clauses.append(SelectionClause(source_np, target_np, cond))
            target_np.resolves_to = source_np
            i += 1
            continue

        if line.startswith("for each"):
            parts = line.split()
            iter_np = NounPhrase(parts[2])
            call_np = NounPhrase(parts[4], is_pronoun=True)
            call_np.resolves_to = last_plural

            i += 1  
            body = []
            
            if i < len(lines):
                next_line = lines[i].strip()
                if next_line.startswith("call"):
                    body.append(parse_call(next_line))
                    i += 1  

            clauses.append(LoopClause(iter_np, call_np, body))
            continue

        if line.startswith("call"):
            clauses.append(parse_call(line))
            i += 1
            continue

        raise SyntaxError(f"Unrecognized LPY line: {line}")

    return Program(clauses)

def parse_call(line):
    parts = line.split()
    verb = parts[1]
    
    if verb == "checkpassword_strength":
        verb = "check_password_strength"
        
    if "with" in parts:
        arg = parts[3]
        arg_np = NounPhrase(arg)
    else:
        arg_np = None
    
    vp = VerbPhrase(verb)
    return CallClause(vp, arg_np)
