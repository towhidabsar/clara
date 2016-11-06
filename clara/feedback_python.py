'''
Generating textual feedback from repair for Python programs
'''

from model import Op, Var, Const, VAR_COND, VAR_RET, VAR_OUT

PRIMITIVE_FUNC = ['len']

BINARY_OPS = {
    'And': 'and',
    'Or': 'or',
    'Add': '+',
    'Sub': '-',
    'Mult': '*',
    'Div': '/',
    'Mod': '%',
    'Pow': '**',
    'LShift': '<<',
    'RShift': '>>',
    'BitOr': '|',
    'BitAnd': '&',
    'BitXor': '^',
    'FloorDiv': '//',
    'Eq':'==',
    'NotEq':'!=',
    'Lt':'<',
    'LtE':'<=',
    'Gt':'>',
    'GtE':'>=',
    'Is':'is',
    'IsNot':'is not',
    'In':'in',
    'NotIn':'not in'
}
UNARY_OPS = {
    'Invert': '~',
    'Not': 'not ',
    'UAdd': '+',
    'USub': '-'
}


class PythonFeedback(object):

    def __init__(self, impl, spec, result, cleanstrings=None):
        self.impl = impl
        self.spec = spec
        self.result = result
        self.feedback = []

    def add(self, msg, *args):
        if args:
            msg %= args
        self.feedback.append('(python) %s' % (msg,))

    def genfeedback(self):
        # Iterate all functions
        # fname - function name
        # mapping - one-to-one mapping of variables
        # repairs - list of repairs
        # sm - structural matching betweeb locations of programs
        for fname, (mapping, repairs, sm) in self.result.items():

            # Copy mapping with converting '*' into a 'new_' variable
            nmapping = {k: '$new_%s' % (k,)
                        if v == '*' else v for (k, v) in mapping.items()}

            # Go through all repairs
            # loc1 - location from the spec.
            # var1 - variable from the spec.
            # var2 - variable from the impl.
            # cost - cost of the repair
            for (loc1, var1, var2, cost, _) in repairs:

                # Get functions and loc2
                fnc1 = self.spec.getfnc(fname)
                fnc2 = self.impl.getfnc(fname)
                loc2 = sm[loc1]

                # Get exprs (spec. and impl.)
                expr1 = fnc1.getexpr(loc1, var1)
                expr2 = fnc2.getexpr(loc2, var2)

                # Location of the expression
                if expr2.line:
                    # Either line
                    locdesc = 'at %s' % (expr2.line,)
                else:
                    # Or location description
                    locdesc = fnc2.getlocdesc(loc2)

                # Delete feedback
                if var1 == '-':
                    self.add("Delete '%s' at line %s (cost=%s)",
                             str(self.assignmentStatement(var2, expr2)), expr2.line, cost)
                    continue

                # Rewrite expr1 (from spec.) with variables of impl.
                expr1 = expr1.replace_vars(nmapping)

                # '*' means adding a new variable (and also statement)
                if var2 == '*':
                    self.add("Add assignment '%s' %s (cost=%s)",
                             str(self.assignmentStatement('$new_%s' % (var1, expr1))), locdesc, cost)
                    continue

                # Output original and new (rewriten) expression for var2
                self.add(
                    "Change '%s' to '%s' %s (cost=%s)",
                    str(self.assignmentStatement(var2, expr2)), str(self.assignmentStatement(var2, expr1)), locdesc, cost)
                
    def assignmentStatement(self, var, expr):
        if var == VAR_COND:
            return PyCondition(self.pythonExpression(expr))
        elif var == VAR_RET:
            return PyReturn(self.pythonExpression(expr))
        elif var == VAR_OUT:
            return PyPrint(self.pythonExpression(expr))
        else:
            try:
                if expr.name == 'AssignElement':
                    return self.pythonExpression(expr)
            except AttributeError:
                pass
        return PyAssignment(PyVariable(var), self.pythonExpression(expr))
                
    def pythonExpression(self, expr):
        try:
            args = [self.pythonExpression(arg) for arg in expr.args]
            if expr.name == 'ListInit':
                return PyListInit(args)
            elif expr.name == 'SetInit':
                return PySetInit(args)
            elif expr.name == 'DictInit':
                return PyDictInit(args)
            elif expr.name == 'TupleInit':
                return PyTupleInit(args)
            elif expr.name == 'AssignElement':
                return PyAssignment(PyGetElement(args[0], args[1]), args[2])
            elif expr.name in BINARY_OPS:
                return PyBinaryOperation(args[0], expr.name, args[1])
            elif expr.name in UNARY_OPS:
                return PyUnaryOperation(expr.name, args[0])
            elif expr.name == 'StrAppend':
                return PyStrAppend(args[0], args[1])
            elif expr.name == 'ite':
                return PyIfThenElse(args[0], args[1], args[2])
            elif expr.name == 'GetAttr':
                return PyGetAttr(args[0], args[1])
            elif expr.name == 'Slice':
                return PySlice(args[0], args[1], args[2])
            elif expr.name == 'GetElement':
                return PyGetElement(args[0], args[1])
            elif expr.name == 'Delete':
                return PyDelete(args)
            elif expr.name == 'FuncCall':
                return PyFuncCall(args[0], (args[1:]))
            elif expr.name == 'Comp':
                return PyComprehension(args[0], args[1], args[2:])
            elif expr.name == 'ListComp':
                return PyListComp(args[0], args[1:])
            elif expr.name == 'SetComp':
                return PySetComp(args[0], args[1:])
            elif expr.name == 'DictComp':
                return PyDictComp(args[0], args[1], args[2:])
            elif expr.args != None:
                try:
                    if expr.name in PRIMITIVE_FUNC or callable(eval(expr.name)):
                        return PyFuncCall(expr.name, args)
                except NameError:
                    pass
                return PyFuncCall(PyGetAttr(self.pythonExpression(expr.args[0]), expr.name), args[1:])
        except AttributeError:
            try:
                return PyConstant(expr.value)
            except AttributeError:
                return PyVariable(expr.name)
        return PyConstant(None)

class PyStatement(object):
    def __init__(self, value):
        self.value = value
    
    def __repr__(self):
        return self.value

class PyCondition(PyStatement):
    def __init__(self, cond):
        self.cond = cond
        
    def __repr__(self):
        return 'if %s:' % str(self.cond)
    
class PyReturn(PyStatement):
    def __init__(self, arg):
        self.arg = arg
        
    def __repr__(self):
        return 'return %s' % str(self.arg)
    
class PyPrint(PyStatement):
    def __init__(self, arg):
        self.arg = arg
        
    def __repr__(self):
        if(isinstance(self.arg, PyStrAppend)):
            try:
                if self.arg.left.name == VAR_OUT:
                    return 'print %s' % str(self.arg.right)
                elif self.arg.right.name == VAR.OUT:
                    return 'print %s' % str(self.arg.left)
                    
            except AttributeError:
                pass
            return '%s; %s' % (str(PyPrint(self.arg.left)), str(PyPrint(self.arg.right)))
            
        return 'print %s' % str(self.arg)
    
class PyExpression(PyStatement):
    def __init__(self, value):
        self.value = value
    
    def __repr__(self):
        return self.value
    
class PyLValue(PyExpression):
    def __init__(self, value):
        self.value = value
    
    def __repr__(self):
        return self.value
    
class PyAssignment(PyExpression):
    def __init__(self, variable, assigned):
        self.variable = variable
        self.assigned = assigned
        
    def __repr__(self):
        return '%s = %s' % (str(self.variable), str(self.assigned))
    
class PyVariable(PyLValue):
    def __init__(self, name):
        self.name = name
        
    def __repr__(self):
        return self.name

class PyConstant(PyExpression):
    def __init__(self, value):
        self.value = value
        
    def __repr__(self):
        return self.value
    
        
class PyListInit(PyExpression):
    def __init__(self, args):
        self.args = args
    
    def __repr__(self):
        arguments = [str(arg) for arg in self.args]
        return '[%s]' % ','.join(arguments)
        
class PySetInit(PyExpression):
    def __init__(self, args):
        self.args = args
    
    def __repr__(self):
        arguments = [str(arg) for arg in self.args]
        return 'set([%s])' % ', '.join(arguments)
        
class PyDictInit(PyExpression):
    def __init__(self, args):
        self.args = args
    
    def __repr__(self):
        arguments = [str(arg) for arg in self.args]
        return '{%s}' % ', '.join([arguments[i-1]+': '+arguments[i] for i in range(1,len(arguments))])
        
class PyTupleInit(PyExpression):
    def __init__(self, args):
        self.args = args
    
    def __repr__(self):
        arguments = [str(arg) for arg in self.args]
        return '(%s)' % ', '.join(arguments)
    
    
class PyBinaryOperation(PyExpression):
    def __init__(self, left, op, right):
        self.left = left
        self.right = right
        self.op = op
        
    def __repr__(self):
        return '(%s %s %s)' % (str(self.left), BINARY_OPS[self.op], str(self.right)) # TODO: priority?!
        

class PyUnaryOperation(PyExpression):
    def __init__(self, op, arg):
        self.op = op
        self.arg = arg
        
    def __repr__(self):
        return '(%s%s)' % (UNARY_OPS[self.op], str(self.arg)) # TODO priority?
    
class PyStrAppend(PyExpression):
    def __init__(self, left, right):
        self.left = left
        self.right = right
        
    def __repr__(self):
        return '%s + %s' % (str(self.left), str(self.right))

class PyIfThenElse(PyExpression):
    def __init__(self, ifexpr, thenexpr, elseexpr):
        self.ifexpr = ifexpr
        self.thenexpr = thenexpr
        self.elseexpr = elseexpr
        
    def __repr__(self):
        return '%s if %s else %s' % (str(self.thenexpr), str(self.ifexpr), str(self.elseexpr))
    
class PyGetAttr(PyLValue):
    def __init__(self, obj, attr):
        self.obj = obj
        self.attr = attr
    
    def __repr__(self):
        return '%s.%s' % (str(self.obj), str(self.attr))
        
class PySlice(PyExpression):
    def __init__(self, lower, upper, step):
        self.lower = lower
        self.upper = upper
        self.step = step
    
    def __repr__(self):
        ret = ':'
        if str(self.lower) != 'None':
            ret = '%s:' % str(self.lower)
        if str(self.upper) != 'None':
            ret = ret + str(self.upper)
        if str(self.step) != 'None':
            ret = ret + ':' + str(self.step)
            
        return ret
        
class PyGetElement(PyLValue):
    def __init__(self, collection, index):
        self.collection = collection
        self.index = index
    
    def __repr__(self):
        return '%s[%s]' % (str(self.collection), str(self.index))
        
class PyDelete(PyStatement):
    def __init__(self, args):
        self.args = args
        
    def __repr__(self):
        arguments = [str(arg) for arg in self.args]
        return 'del %s' % ', '.join(arguments)
    
class PyFuncCall(PyExpression):
    def __init__(self, func, args):
        self.func = func
        self.args = args
    
    def __repr__(self):
        arguments = [str(arg) for arg in self.args]
        return '%s(%s)' % (str(self.func), (', ').join(arguments))
    
class PyComprehension(PyExpression):
    def __init__(self, target, iter, ifs):
        self.target = target
        self.iter = iter
        self.ifs = ifs
        
    def __repr__(self):
        return 'for %s in %s if %s' % (self.target, self.iter, ' '.join(['if ' + str(cond) for cond in self.ifs]))
    
class PyListComp(PyExpression):
    def __init__(self, elt, generators):
        self.elt = elt
        self.generators = generators
        
    def __repr__(self):
        return '[%s %s]' % (self.elt , ' '.join([str(gen) for gen in self.generators]))
        
class PySetComp(PyExpression):
    def __init__(self, elt, generators):
        self.elt = elt
        self.generators = generators
        
    def __repr__(self):
        return '{%s %s}' % (self.elt , ' '.join([str(gen) for gen in self.generators]))
        
class PyDictComp(PyExpression):
    def __init__(self, key, value, generators):
        self.key = key
        self.value = value
        self.generators = generators
        
    def __repr__(self):
        return '{%s: %s %s}' % (self.key, self.value, (' ').join([str(gen) for gen in self.generators]) )
    
