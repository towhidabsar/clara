'''
Program model
'''

# Special variables definitions
VAR_COND = '$cond'
VAR_RET = '$ret'
VAR_IN = '$in'
VAR_OUT = '$out'
SPECIAL_VARS = set([VAR_COND, VAR_RET, VAR_IN, VAR_OUT])


# Variable helper functions
def isprimed(var):
    if isinstance(var, str):
        return var.endswith("'")
    return var.primed


def prime(var):
    assert not isprimed(var), 'Variable already primed!'
    
    if isinstance(var, str):
        return "%s'" % (var,)

    var = var.copy()
    var.primed = True
    return var


def unprime(var):

    assert isprimed(var), 'Variable not primed!'

    if isinstance(var, str):
        return var[:-1]

    var = var.copy()
    var.primed = False
    return var


class Expr(object):
    '''
    An expression
    '''

    def __init__(self, line=None):
        self.line = line

    def copyargs(self):
        return {'line': self.line}

    
class Var(Expr):
    '''
    Variable
    '''

    def __init__(self, name, primed=False, *args, **kwargs):
        
        super(Var, self).__init__(*args, **kwargs)

        assert isinstance(name, str), \
            "Variable name should be string, got '%s'" % (name,)
        assert isinstance(primed, bool), \
            "Variable 'primed' should be bool, got '%s'" % (primed,)
        
        self.name = name
        self.primed = primed

    def copy(self):
        return Var(self.name, self.primed, **self.copyargs())

    def replace(self, var, expr, primedonly=False):
        if self.name == var and ((not primedonly) or self.primed):
            return expr.copy()
        else:
            return self.copy()

    def replace_vars(self, d):
        if self.name in d:
            v = self.copy()
            v.name = d[self.name]
            return v
        else:
            return self.copy()

    def prime(self, vars):
        if self.name in vars:
            self.primed = True

    def vars(self):
        return set([str(self)])
    
    def __repr__(self):
        if self.primed:
            return "%s'" % (self.name,)
        else:
            return self.name

        
class Const(Expr):
    '''
    Constant
    '''

    def __init__(self, value, *args, **kwargs):

        super(Const, self).__init__(*args, **kwargs)

        assert isinstance(value, str), \
            "Constant value should be string, got '%s'" % (value,)
        
        self.value = value

    def copy(self):
        return Const(self.value, **self.copyargs())

    def replace(self, v, e, primedonly=False):
        return self.copy()

    def replace_vars(self, d):
        return self.copy()

    def prime(self, vars):
        pass

    def vars(self):
        return set()

    def __repr__(self):
        return self.value


class Op(Expr):
    '''
    Operations
    '''

    def __init__(self, name, *args, **kwargs):

        super(Op, self).__init__(**kwargs)

        assert isinstance(name, str), \
            "Operation name should be string, got '%s'" % (name,)
        for i, arg in enumerate(args, 1):
            assert isinstance(arg, Expr), \
                "Operation's argument (#%d) should be Expression, got '%s'" % (
                    i, arg)

        self.name = name
        self.args = list(args)

    def copy(self):
        return Op(self.name,
                  *map(lambda x: x.copy(), self.args),
                  **self.copyargs())

    def replace(self, v, e, primedonly=False):
        return Op(self.name,
                  *map(lambda x: x.replace(v, e, primedonly), self.args),
                  **self.copyargs())

    def replace_vars(self, d):
        return Op(self.name,
                  *map(lambda x: x.replace_vars(d), self.args),
                  **self.copyargs())

    def prime(self, vars):
        map(lambda x: x.prime(vars), self.args)

    def vars(self):
        args = self.args[1:] if self.name == 'FuncCall' else self.args
        return reduce(lambda x, y: x | y, map(lambda x: x.vars(), args),
                      set())

    def __repr__(self):
        return '%s(%s)' % (self.name, ', '.join(map(str, self.args)))
    

class Program(object):
    '''
    Program - consisting of functions
    '''

    def __init__(self):
        self.fncs = {}
        self.meta = {}
        self.warns = []

    def addfnc(self, fnc):
        self.fncs[fnc.name] = fnc

    def getfnc(self, name):
        return self.fncs[name]

    def getfncs(self):
        return self.fncs.values()

    def getfncnames(self):
        return self.fncs.keys()

    def rmfnc(self, name):
        del self.fncs[name]

    def addmeta(self, name, val):
        self.meta[name] = val

    def getmeta(self, name, default=None):
        return self.meta.get(name, default)

    def addwarn(self, msg):
        self.warns.append(msg)

    def slice(self):
        map(lambda x: x.slice(), self.fncs.values())

    def __repr__(self):
        return '\n\n'.join(map(str, self.fncs.values()))

    def getstruct(self):
        
        s = []
        for fname in sorted(self.fncs):
            sf = []
            fnc = self.getfnc(fname)
            dl = {}
            todo = [fnc.initloc]
            locs = list()
            while len(todo) > 0:
                loc, todo = todo[0], todo[1:]
                if loc in dl:
                    continue
                dl[loc] = len(dl) + 1
                locs.append(loc)
                if fnc.trans(loc, True) is not None:
                    todo.append(fnc.trans(loc, True))
                if fnc.trans(loc, False) is not None:
                    todo.append(fnc.trans(loc, False))
                    
            for loc in locs:
                lt = fnc.trans(loc, True)
                if lt is None:
                    lt = ''
                else:
                    lt = str(dl[lt])
                lf = fnc.trans(loc, False)
                if lf is None:
                    lf = ''
                else:
                    lf = str(dl[lf])
                sf.append('%s:%s,%s' % (dl[loc], lt, lf))
            s.append('%s{%s}' % (fname, ' '.join(sf)))
        return ' '.join(s)


class Function(object):
    '''
    Function - consisting of params (with type), a return value, and locations.
    '''

    def __init__(self, name, params, rettype):
        '''
        name - string
        params - list of (type, name) pairs
        rettype - Type (string)
        '''

        assert isinstance(name, str), \
            "Function name should be a string, got '%s'" % (name,)
        assert isinstance(params, list), \
            "Function parameters should be a list, got '%s'" % (list,)
        for i, param in enumerate(params, 1):
            assert isinstance(param, tuple) and len(param) == 2, \
                "Parameter (#%d) should be a pair, got '%s'" % (i, param)
            assert isinstance(param[0], str) and isinstance(param[1], str), \
                "Parameter (#%d) should be a pair of strings, got '%s'" % (
                    i, param)
        assert isinstance(rettype, str), \
            "Function return type should be a string, got '%s'" % (rettype,)

        self.name = name
        self.params = list(params)
        self.rettype = rettype

        self.initloc = None   # Initial location
        self.locexprs = {}   # Location -> (VarxExpr)*
        self.loctrans = {}  # Location -> {True,False} -> Location
        self.locdescs = {}  # Location -> Str (description)
        self.types = {}  # Var -> Type

    def addloc(self, loc=None, desc=None):
        '''
        Adds a new location to a function.
        loc - loc number (None for automatic generation)
        desc - description of a location
        '''

        # Generate next location if None
        if loc is None:
            if self.loctrans:
                loc = max(self.loctrans.keys()) + 1
            else:
                loc = 1

        # Check that location is a new integer
        assert isinstance(loc, int), \
            "Location should be 'int', got '%s'" % (loc,)
        assert loc not in self.loctrans.keys(), \
            'Location %d already exists' % (loc,)

        # Assign init location if one doesn't exist yet
        if self.initloc is None:
            self.initloc = loc

        # Init exprs, trans, descs
        self.locexprs[loc] = []
        self.loctrans[loc] = {True: None, False: None}
        self.locdescs[loc] = desc

        return loc

    def locs(self):
        '''
        Returns a set of locations
        '''

        return set(self.locexprs.keys())

    def getlocdesc(self, loc):
        '''
        Gets description of a location
        '''

        assert loc in self.locdescs, "Unknown location: '%s'" % (loc,)
        
        return self.locdescs[loc]

    def exprs(self, loc):
        '''
        Returns a list of (var, expr) pairs for a given location
        '''

        assert loc in self.locexprs, "Unknown location: '%s'" % (loc,)

        return list(self.locexprs[loc])

    def getexpr(self, loc, var):
        '''
        Returns an expression for var at loc
        '''

        for (var2, expr) in self.locexprs[loc]:
            if var == var2:
                return expr
            
        return Var(var)

    def hasexpr(self, loc, var):
        '''
        Returns True if there is an expression for var at loc
        '''

        for (var2, _) in self.locexprs[loc]:
            if var == var2:
                return True
            
        return False

    def numexprs(self, loc):
        '''
        Returns the number of exprs for a given location
        '''

        assert loc in self.locexprs, "Unknown location: '%s'" % (loc,)

        return len(self.locexprs[loc])

    def rmlastexprs(self, loc, num):
        '''
        Removes last num exprs from a location
        '''

        assert loc in self.locexprs, "Unknown locarion: '%s'" % (loc,)
        assert isinstance(num, int) and num > 0, \
            "Expected int>0 for num, got: '%s'" % (num,)

        self.locexprs[loc] = self.locexprs[loc][:-num]

    def trans(self, loc, cond):
        '''
        Returns a transition location for loc and cond
        '''

        return self.loctrans[loc][cond]

    def addexpr(self, loc, var, expr, idx=None):
        '''
        Adds expr for var to loc
        '''

        # Check
        assert loc in self.locexprs, "Unknown location: '%s'" % (loc,)
        assert isinstance(var, str), "Expected 'str', got '%s'" % (var,)
        assert isinstance(expr, Expr), "Expected 'Expr', for '%s'" % (expr,)

        # Add
        if idx is None:
            self.locexprs[loc].append((var, expr))
        else:
            self.locexprs[loc].insert(idx, (var, expr))

    def addtrans(self, loc1, cond, loc2):
        '''
        Adds transition from loc1 to loc2 with label cond
        '''

        # Check
        assert loc1 in self.locexprs,\
            "Unknown location: '%s'" % (loc1,)
        assert loc2 in self.locexprs, \
            "Unknown location: '%s'" % (loc2,)
        assert cond in {True, False}, \
            "Invalid label (condition): '%s'" % (cond,)
        assert self.loctrans[loc1][cond] is None, \
            "Transition '%s' (%s) already exists" % (loc1, cond)

        self.loctrans[loc1][cond] = loc2

    def numtrans(self, loc):
        '''
        Gives number of transitions for a given location
        '''

        assert loc in self.loctrans, "Unknown location: '%s'" % (loc,)

        return sum(1 for v in self.loctrans[loc].values() if v is not None)

    def rmtrans(self, loc, cond):
        '''
        Removes transition from loc1 with label cond
        '''

        assert loc in self.locexprs, \
            "Unknown location: '%s'" % (loc,)
        assert cond in {True, False}, \
            "Invalid label (condition): '%s'" % (cond,)

        self.loctrans[loc][cond] = None

    def rmloc(self, loc):
        '''
        Removes a location
        '''

        assert loc in self.locexprs, "Unknown location: '%s'" % (loc,)

        self.locexprs.pop(loc)
        self.loctrans.pop(loc)
        self.locdescs.pop(loc)

    def replaceexprs(self, loc, exprs):
        '''
        Replaces exprs for a location
        '''

        assert loc in self.locexprs, "Unknown location: '%s'" % (loc,)

        self.locexprs[loc] = []

        for v, e in exprs:
            self.addexpr(loc, v, e)

    def addtype(self, var, type, skiponexist=True):
        '''
        Adds new variable with type
        '''

        assert isinstance(var, str), "Expected string, got '%s'" % (var,)
        assert isinstance(type, str), "Expected string, got '%s'" % (type,)

        if var in self.types and skiponexist:
            return
        
        self.types[var] = type

    def gettype(self, var):
        '''
        Gets type of a variable or None
        '''

        assert isinstance(var, str), "Expected string, got '%s'" % (var,)

        return self.types.get(var, None)

    def getvars(self):
        '''
        Gets a set of all vars
        '''
        return set(self.types.keys())

    def getparamnames(self):
        '''
        Gets list of parameters names
        '''

        return [p[0] for p in self.params]

    def used(self):
        '''
        Finds used (before and after assignment) variables for each location
        '''

        usedpre, usedpost = {}, {}

        for loc in self.locs():
            usedpre[loc] = set([])
            usedpost[loc] = set([])
            
            for (_, expr) in self.exprs(loc):
                used = expr.vars()
                usedpre[loc] |= set(filter(lambda x: not isprimed(x), used))
                usedpost[loc] |= set(map(unprime,
                                         filter(lambda x: isprimed(x), used)))

        return usedpre, usedpost

    def live(self, used=None):
        '''
        Finds "live" variables for each location
        Algorithm from wikipedia:
        https://en.wikipedia.org/wiki/Live_variable_analysis
        '''

        # Initialization
        if used is None:
            used = self.used()
        used = used[0]

        locs = self.locs()
        assigned = {loc: {var for (var, _) in self.exprs(loc)} for loc in locs}
        succ = {loc: {l for l in self.loctrans[loc].values() if l is not None}
                for loc in locs}

        # Note: Special vars are always live!
        livein = {loc: set(SPECIAL_VARS) for loc in locs}
        livein[self.initloc] |= {v for (v, _) in self.params}
        liveout = {loc: set(SPECIAL_VARS) for loc in locs}

        changed = True
        while changed:
            changed = False

            for loc in locs:
                n, m = len(livein[loc]), len(liveout[loc])
                
                livein[loc] = used[loc] | (liveout[loc] - assigned[loc])

                for sloc in succ[loc]:
                    liveout[loc] |= livein[sloc]

                if n != len(livein[loc]) or m != len(liveout[loc]):
                    changed = True

        return (livein, liveout)

    def slice(self, merge=False):
        '''
        Slices (removes and (in more aggresive mode) merges) expressions
        Note: Merge is unsound!
        '''

        used = self.used()
        livein, liveout = self.live(used=used)
        usedpre, usedpost = used

        for loc in self.locs():

            exprs = []
            m = {}

            for (var, expr) in self.exprs(loc):

                for v, e in m.items():
                    expr = expr.replace(v, e.copy(), primedonly=True)
                
                # Definitively unsed var!
                if var not in SPECIAL_VARS and var not in usedpost[loc] \
                   and var not in liveout[loc]:
                    continue

                # This variable can be merged
                if var not in SPECIAL_VARS and var not in liveout[loc] \
                   and merge:
                    m[var] = expr
                    continue

                exprs.append((var, expr))

            self.replaceexprs(loc, exprs)

        # Remove unused variables
        usedpre, usedpost = self.used()
        used = set()
        for loc in self.locs():
            used |= usedpre[loc] | usedpost[loc]
        used |= {v for (v, _) in self.params}
        for v in list(self.types):
            if v not in used:
                del self.types[v]
        
    def __repr__(self):
        s = [
            'fun %s (%s) : %s' % (self.name,
                                  ', '.join(map(lambda x: '%s: %s' % x,
                                                self.params)),
                                  self.rettype),
            '-' * 69,
            ', '.join(map(lambda x: '%s : %s' % x, self.types.items())),
        ]
        for loc in sorted(self.locexprs.keys()):
            s.append('')
            s.append('Loc %d' % (loc,))
            s.append('-' * 39)
            
            for (var, expr) in self.locexprs[loc]:
                s.append('  %s := %s' % (var, expr))

            s.append('-' * 39)

            s.append('  True -> %s   False -> %s' % (
                self.loctrans[loc][True], self.loctrans[loc][False]))

        return '\n'.join(s)