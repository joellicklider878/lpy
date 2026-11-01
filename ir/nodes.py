class Program:
    def __init__(self, clauses):
        self.clauses = clauses

class Clause: pass

class NounPhrase:
    def __init__(self, name, determiner=None, is_pronoun=False):
        self.name = name
        self.determiner = determiner
        self.is_pronoun = is_pronoun
        self.resolves_to = None

class VerbPhrase:
    def __init__(self, name, adverb=None):
        self.name = name
        self.adverb = adverb

class Expression: pass

class IdentifierExpr(Expression):
    def __init__(self, name):
        self.name = name

class LiteralExpr(Expression):
    def __init__(self, value):
        self.value = value

class FunctionCallExpr(Expression):
    def __init__(self, func_name, args):
        self.func_name = func_name
        self.args = args

class Condition:
    def __init__(self, subject_np, relation, expr):
        self.subject = subject_np
        self.relation = relation 
        self.expr = expr

class DefinitionClause(Clause):
    def __init__(self, target_np ,expr):
        self.target = target_np
        self.expr = expr

class SelectionClause(Clause):
    def __init__(self, source_np, target_np, condition=None):
        self.source = source_np
        self.target = target_np
        self.condition = condition

class LoopClause(Clause):
    def __init__(self, iter_np, collection_np, body_clauses):
        self.iter = iter_np
        self.collection = collection_np
        self.body = body_clauses

class CallClause(Clause):
    def __init__(self, verb_phrase, arg_np=None):
        self.verb = verb_phrase
        self.arg = arg_np

#added clause
class IfStatusNode(Clause):
    def __init__(self, variable, status, then_body=None, otherwise_body=None):
        self.variable = variable
        self.status = status
        self.then_body = then_body if then_body is not None else []
        self.otherwise_body = otherwise_body if otherwise_body is not None else []
