import ast
from ir.nodes import *

def lower_program(program):
    body = []
    for clause in program.clauses:
        body.extend(lower_clause(clause))
    #create module structure        
    module = ast.Module(body=body, type_ignores=[])
    #fix 
    ast.fix_missing_locations(module)
    return module

def lower_clause(root_cl):
    # This acts as our accumulator for the top-level nodes
    final_output = []
    
    # Each entry in our stack tracks: [node, step, contextual data dict]
    # step 0: Initial processing of the node
    # step 1: Post-processing after children are evaluated
    stack = [[root_cl, 0, {}]]
    result_stack = []
    
    while stack:
        current_frame = stack[-1]
        cl, step, context = current_frame[0], current_frame[1], current_frame[2]
        
        if step == 0:
            if isinstance(cl, DefinitionClause):
                result_stack.append([lower_definition(cl)])
                stack.pop()
            elif isinstance(cl, SelectionClause):
                result_stack.append([lower_selection(cl)])
                stack.pop()
            elif isinstance(cl, CallClause):
                result_stack.append([lower_call(cl)])
                stack.pop()
            #added
            elif isinstance(cl, LoopClause):
                loop_body = getattr(cl, 'body', [])
                context['body_len'] = len(loop_body)
                current_frame[1] = 1

                for c in reversed(loop_body):
                    stack.append([c, 0, {}])
                    
            elif isinstance(cl, IfStatusNode):
                # Retrieve sub-clauses safely
                then_body = getattr(cl, 'then_body', [])
                otherwise_body = getattr(cl, 'otherwise_body', [])
                
                # Store structural lengths so we know how many results belong to this node
                context['then_len'] = len(then_body)
                context['otherwise_len'] = len(otherwise_body)
                
                # Move this IfStatusNode to step 1
                current_frame[1] = 1
                
                # Push elements onto stack in reverse 
                for c in reversed(otherwise_body):
                    stack.append([c, 0, {}])
                for c in reversed(then_body):
                    stack.append([c, 0, {}])
            else:
                raise TypeError(f"Unhandled clause type: {type(cl)}")
                
        elif step == 1:
            stack.pop()
            
            if isinstance(cl, LoopClause):
                body_len = context['body_len']
                loop_nodes = []
                for _ in range(body_len):
                    loop_nodes.insert(0, result_stack.pop())
                
                # FIXED: This list comprehension must live safely INSIDE the LoopClause block
                flat_loop_nodes = [node for sublist in loop_nodes for node in sublist]
                if not flat_loop_nodes:
                    flat_loop_nodes = [ast.Pass()]
                
                py_loop = lower_loop_ast_structure(cl, flat_loop_nodes)
                result_stack.append([py_loop])

            elif isinstance(cl, IfStatusNode):
                then_len = context['then_len']
                otherwise_len = context['otherwise_len']
                
                all_children_results = []
                for _ in range(then_len + otherwise_len):
                    all_children_results.insert(0, result_stack.pop())
                    
                then_py_nodes = []
                for res in all_children_results[:then_len]:
                    then_py_nodes.extend(res)
                    
                otherwise_py_nodes = []
                for res in all_children_results[then_len:]:
                    otherwise_py_nodes.extend(res)

                if not then_py_nodes:
                    then_py_nodes = [ast.Pass()]
                if not otherwise_py_nodes:
                    otherwise_py_nodes = [ast.Pass()]
                #clean python 3.13 context implementation
                py_if = ast.If(
                    test=ast.Compare(
                        left=ast.Attribute(
                            value=ast.Name(id=cl.variable),
                            attr='status'
                        ),
                        ops=[ast.Eq()],
                        comparators=[ast.Constant(value=cl.status)]
                    ),
                    body=then_py_nodes,
                    orelse=otherwise_py_nodes
                )
                result_stack.append([py_if])

    # Flatten the final accumulated block results
    for res in result_stack:
        final_output.extend(res)
        
    return final_output

def lower_definition(cl):
    return ast.Assign(
        targets=[ast.Name(id=cl.target.name, ctx=ast.Store())],
        value=lower_expression(cl.expr)
    )

def lower_selection(cl):
    target = cl.target.name
    
    # 1. Linguistically normalize the source collection identifier 
    source_name = cl.source.name
    normalized_source = source_name.rstrip("s")
    
    # 2. Match the variable scope to whatever form was declared in the environment
    elem_id = ast.Name(id=normalized_source, ctx=ast.Store())
    elem_ref = ast.Name(id=normalized_source, ctx=ast.Load())
    
    src = ast.Name(id=source_name, ctx=ast.Load())

    if cl.condition:
        cond = lower_condition(cl.condition, elem_ref)
        comp = ast.ListComp(elt=elem_ref, generators=[ast.comprehension(target=elem_id, iter=src, ifs=[cond], is_async=0)])
    else:
        comp = ast.ListComp(elt=elem_ref, generators=[ast.comprehension(target=elem_id, iter=src, ifs=[], is_async=0)])
    
    return ast.Assign(
        targets=[ast.Name(id=target, ctx=ast.Store())],
        value=comp
    )

def lower_condition(cond, elem_ref):
    left = ast.Attribute(
        value=elem_ref, attr=cond.subject.name,
        ctx=ast.Load() 
    )
    right = lower_expression(cond.expr)
    return ast.Compare(left=left, ops=[ast.Eq()], comparators=[right])

def lower_loop_ast_structure(cl, flat_loop_nodes=None):
    iter_target = ast.Name(id=cl.iter.name, ctx=ast.Store())
    
    if cl.collection.name == "those":
        call_name = "those"
    elif hasattr(cl.collection, 'resolves_to') and cl.collection.resolves_to:
        call_name = cl.collection.resolves_to.name
    else:
        call_name = cl.collection.name
        
    coll_expr = ast.Name(id=call_name, ctx=ast.Load())

    body = []
    for inner in cl.body:
        body.extend(lower_clause(inner))

    return ast.For(
        target=iter_target,
        iter=coll_expr,
        body=body,
        orelse=[]
    )

def lower_call(cl):
    func_name = cl.verb.name
    # FIXED: Normalize typo call variations to match cyber runtime module directly
    if func_name == "checkpassword_strength":
        func_name = "check_password_strength"
        
    # NEW: Check if this is a namespaced module function call (e.g., "algo.quicksort")
    if "." in func_name:
        namespace, method_name = func_name.split(".", 1)
        
        # Generates the AST equivalent of: namespace['method_name']
        func = ast.Subscript(
            value=ast.Name(id=namespace, ctx=ast.Load()),
            slice=ast.Constant(value=method_name) if hasattr(ast, 'Constant') else ast.Index(value=ast.Str(s=method_name)),
            ctx=ast.Load()
        )
    else:
        # Default behavior for normal global function lookups
        func = ast.Name(id=func_name, ctx=ast.Load())
        
    args = []
    arg_node = getattr(cl, 'arg', None) or getattr(cl, 'target', None) or getattr(cl, 'alias', None)
    if arg_node:
        args.append(ast.Name(id=arg_node.name, ctx=ast.Load()))
        
    return ast.Expr(value=ast.Call(func=func, args=args, keywords=[]))

def lower_expression(expr):
    # 1. Safely resolve raw fallback python strings first
    if isinstance(expr, str):
        if (expr.startswith('"') and expr.endswith('"')) or (expr.startswith("'") and expr.endswith("'")):
            expr = expr[1:-1]
        return ast.Constant(value=expr)

    if isinstance(expr, IdentifierExpr):
        # 2. Extract and sanitize raw text flags 
        is_string_literal = getattr(expr, 'is_string', False)
        raw_name = getattr(expr, 'raw_value', expr.name)

        if isinstance(raw_name, str):
            if (raw_name.startswith('"') and raw_name.endswith('"')) or (raw_name.startswith("'") and raw_name.endswith("'")):
                raw_name = raw_name[1:-1]
                is_string_literal = True  # Enforce text status if it has quotes

        # 3. Explicit Text Rule: Never let text values get caught by keyword mappings
        if is_string_literal:
            return ast.Constant(value=raw_name)
            
        # 4. Keyword Processing: Safely process keyword execution actions
        if expr.name in ["get_user", "get_users"]:
            return ast.Call(
                func=ast.Name(id=expr.name, ctx=ast.Load()),
                args=[],
                keywords=[]
            )
            
        # 5. Domain Status Rule
        if expr.name in ["active", "inactive", "pending"]:
            return ast.Constant(value=expr.name)

        # 6. Fallback Rule: Treat as normal variable declaration
        return ast.Name(id=expr.name, ctx=ast.Load())
        
    # 7. Check for clean wrapper primitives
    if isinstance(expr, LiteralExpr):
        return ast.Constant(value=expr.value)

    # 8. Nested Explicit Functions
    if isinstance(expr, FunctionCallExpr):        
        return ast.Call(
            func=ast.Name(id=expr.func_name, ctx=ast.Load()),
            args=[lower_expression(a) for a in expr.args],
            keywords=[]
        )
        
    raise TypeError(f"Unhandled expression type: {type(expr)}")
