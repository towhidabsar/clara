'''
Python interpreter
'''

# Python imports
import math
import string

from copy import deepcopy

# Feedback lib imports
from py_parser import PyParser

from interpreter import Interpreter, addlanginter, RuntimeErr, UndefValue
from model import Var, Op, VAR_IN, VAR_OUT, VAR_RET, prime


def eargs(fun):
    '''
    Decorator to evaluate args
    '''

    # Wrapper function that calls original 'fun'
    def wrap(self, f, mem):
        args = map(lambda x: self.execute(x, mem), f.args)
        return fun(self, *args)

    return wrap


class PyInterpreter(Interpreter):

    BINARY_OPS = set()
    UNARY_OPS = set()
    DEFAULT_RETURN = None

    def execute_Const(self, c, mem):

        c = c.value
        
        # Undef
        if c == '?':
            return UndefValue

        # Integer
        try:
            if len(c) > 0 and c[-1] == 'l':
                c = c[:-1]
            return int(c)
        except ValueError:
            pass

        # Float
        try:
            return float(c)
        except ValueError:
            pass

        # Complex
        if len(c) > 0 and c[-1] == 'j':
            try:
                return complex(c)
            except ValueError:
                pass
        
        # String
        if len(c) >= 2 and c[0] == c[-1] == '"':
            return c[1:-1]

        # Bool
        if c in ('True', 'False'):
            return c == 'True'

        # None
        if c == 'None':
            return None

        assert False, 'unknown constant: %s' % (c,)

    @eargs
    def execute_int(self, x):
        return int(x)

    @eargs
    def execute_float(self, x):
        return float(x)

    @eargs
    def execute_bool(self, x):
        return bool(x)

    @eargs
    def execute_str(self, x):
        return str(x)

    @eargs
    def execute_ListInit(self, *a):
        return list(a)

    @eargs
    def execute_list(self, *a):
        return list(a)

    @eargs
    def execute_DictInit(self, *d):
        return {k: v for (k, v) in zip(d[0::2], d[1::2])}

    @eargs
    def execute_dict(self, *d):
        return dict(*d)

    @eargs
    def execute_SetInit(self, *s):
        return set(s)

    @eargs
    def execute_set(self, *s):
        return set(*s)

    @eargs
    def execute_TupleInit(self, *t):
        return tuple(t)

    @eargs
    def execute_tuple(self, *t):
        return tuple(*t)

    @eargs
    def execute_Not(self, x):
        return not x

    def execute_And(self, f, mem):
        x = self.execute(f.args[0], mem)
        if not x:
            return False
        return self.execute(f.args[1], mem)

    def execute_Or(self, f, mem):
        x = self.execute(f.args[0], mem)
        if x:
            return x
        return self.execute(f.args[1], mem)

    def execute_GetAttr(self, g, mem):
        name = g.args[1].value

        if isinstance(g.args[0], Var) \
           and g.args[0].name in PyParser.MODULE_NAMES:
            mname = g.args[0].name
            if mname == 'string':
                return getattr(string, name)
            elif name == 'math':
                return getattr(math, name)
            
        return getattr(self.execute(g.args[0], mem), name)

    @eargs
    def execute_abs(self, x):
        return abs(x)

    @eargs
    def execute_round(self, *a):
        return round(*a)

    @eargs
    def execute_Pow(self, x, y):
        return x ** y

    @eargs
    def execute_pow(self, *a):
        return pow(*a)

    @eargs
    def execute_math_pow(self, *a):
        return math.pow(*a)
    
    @eargs
    def execute_sum(self, *x):
        return sum(*x)

    @eargs
    def execute_max(self, *x):
        return max(*x)

    @eargs
    def execute_Invert(self, x):
        return ~x

    @eargs
    def execute_UAdd(self, x):
        return +x

    @eargs
    def execute_USub(self, x):
        return -x

    @eargs
    def execute_BitAnd(self, x, y):
        return x & y

    @eargs
    def execute_BitOr(self, x, y):
        return x | y

    @eargs
    def execute_BitXor(self, x, y):
        return x ^ y

    @eargs
    def execute_RShift(self, x, y):
        return x >> y

    @eargs
    def execute_LShift(self, x, y):
        return x << y

    @eargs
    def execute_Mod(self, x, y):
        return x % y

    @eargs
    def execute_Add(self, x, y):
        return x + y

    @eargs
    def execute_Sub(self, x, y):
        return x - y

    @eargs
    def execute_Div(self, x, y):
        return x / y

    @eargs
    def execute_FloorDiv(self, x, y):
        return x // y

    @eargs
    def execute_Mult(self, x, y):
        return x * y

    @eargs
    def execute_Lt(self, x, y):
        return x < y

    @eargs
    def execute_LtE(self, x, y):
        return x <= y

    @eargs
    def execute_Gt(self, x, y):
        return x > y

    @eargs
    def execute_GtE(self, x, y):
        return x >= y

    @eargs
    def execute_Eq(self, x, y):
        return x == y

    @eargs
    def execute_NotEq(self, x, y):
        return x != y

    @eargs
    def execute_In(self, x, y):
        return x in y

    @eargs
    def execute_NotIn(self, x, y):
        return x not in y

    @eargs
    def execute_Is(self, x, y):
        return x is y

    @eargs
    def execute_IsNot(self, x, y):
        return x is not y

    @eargs
    def execute_GetElement(self, x, y):
        return x[y]

    @eargs
    def execute_Slice(self, a, b, c):
        return slice(a, b, c)

    @eargs
    def execute_len(self, x):
        return len(x)

    @eargs
    def execute_AssignElement(self, l, i, v):
        l = deepcopy(l)
        l[i] = v
        return l

    @eargs
    def execute_append(self, l, e):
        l = deepcopy(l)
        l.append(e)
        return l

    @eargs
    def execute_sort(self, l, *a):
        l = deepcopy(l)
        l.sort(*a)
        return l

    @eargs
    def execute_range(self, *a):
        return list(range(*a))

    def execute_xrange(self, e, mem):
        return self.execute_range(e, mem)

    @eargs
    def execute_extend(self, l, i):
        l = deepcopy(l)
        l.extend(i)
        return l

    @eargs
    def execute_remove(self, l, i):
        l = deepcopy(l)
        l.remove(i)
        return l

    @eargs
    def execute_insert(self, l, i, v):
        l = deepcopy(l)
        l.insert(i, v)
        return l

    @eargs
    def execute_items(self, d):
        return d.items()

    @eargs
    def execute_keys(self, d):
        return d.keys()

    @eargs
    def execute_index(self, l, v, *a):
        return l.index(v, *a)

    @eargs
    def execute_pop(self, l, *a):
        nl = deepcopy(l)
        res = nl.pop(*a)
        return (nl, res)

    @eargs
    def execute_Delete(self, l, i):
        nl = deepcopy(l)
        del nl[i]
        return nl

    @eargs
    def execute_reverse(self, l):
        return list(reversed(l))

    @eargs
    def execute_enumerate(self, *a):
        return list(enumerate(*a))

    def execute_reversed(self, o, mem):
        return self.execute_reverse(o, mem)

    def execute_Comp(self, c, mem):
        # Arg #1 is a list of names
        names = self.extract_names(c.args[0])

        # Arg #2 is an expression evaluating to a list
        l = list(self.execute(c.args[1], mem))

        # Arg #3 is a filter expression
        f = c.args[2]

        # If there is only one name, transform list elements
        # into "one-tuples"
        if len(names) == 1:
            l = [(x,) for x in l]

        # Run filter
        nl = []
        for el in l:

            # Construct a new memory
            newmem = deepcopy(mem)
            for var, val in zip(names, el):
                newmem[var] = val

            # Get filter value
            ok = self.execute(f, newmem)
            if ok:
                nl.append(el)

        return names, nl

    def execute_ListComp(self, lc, mem):

        # Execute comprehension expression
        vars, l = self.execute(lc.args[1], mem)

        # Generator expression
        expr = lc.args[0]

        # Construct a new list
        nl = []
        for el in l:

            # Construct a new memory from a list element
            newmem = deepcopy(mem)
            for var, val in zip(vars, el):
                newmem[var] = val

            # Get a value of an element by executing it
            el = self.execute(expr, newmem)
            nl.append(el)

        return nl

    def execute_SetComp(self, sc, mem):
        return set(self.execute_ListComp(sc, mem))

    def execute_DictComp(self, dc, mem):

        # Comprehension expression
        vars, l = self.execute(dc.args[2], mem)

        # Key, value exprs
        ke, ve = dc.args[:2]

        # Construct a dict
        nd = {}
        for el in l:

            # New memory from a list element
            newmem = deepcopy(mem)
            for var, val in zip(vars, el):
                newmem[var] = val

            # Get key and value by executing expressions
            key = self.execute(ke, newmem)
            val = self.execute(ve, newmem)
            nd[key] = val

        return nd

    def extract_names(self, node):
        # Single variable
        if isinstance(node, Var):
            return [node.name]

        # Tuple of variables
        if isinstance(node, Op) and node.name == 'TupleInit':
            vars = []
            for arg in node.args:
                assert isinstance(arg, Var), 'unsupported list of names'
                vars.append(arg.name)
            return vars

        assert False, 'unsupported list of names'
        
    def convert(self, v, t):
        return v


addlanginter('py', PyInterpreter)
