'''
Generating simple, but not raw textual feedback from repair
'''

from model import VAR_OUT, VAR_IN, VAR_COND, VAR_RET, Var, Op, Const
from model import isprimed, unprime, prime

# TODO: Maybe add importance to feedback, so only
# a limited number of feedback messages would be shown

class SimpleFeedback(object):

    def __init__(self, impl, spec, result):
        self.impl = impl
        self.spec = spec
        self.result = result
        self.feedback = []

        self.compops = set(['<=', '<', '>', '>=', '==', '!='])
        self.arithops = set(['+', '-', '*', '/'])
        self.logicops = set(['&&', '||'])

        self.ops = self.compops | self.arithops | self.logicops

        self.opdefs = [
            ('comparison', self.compops),
            ('arithmetic', self.arithops),
            ('logical', self.logicops),
        ]

    def add(self, msg, *args):
        if args:
            msg %= args
        self.feedback.append(msg)

    def genfeedback(self):
        # Iterate all functions
        # fname - function name
        # mapping - one-to-one mapping of variables
        # repairs - list of repairs
        # sm - structural matching betweeb locations of programs
        for fname, (mapping, repairs, sm) in self.result.items():

            # Remember deleted and added variables
            deleted = set()
            added = set()

            # Remember all vars in impl.
            vars2 = set(mapping.values())
            
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
                    locdesc = 'at line %s' % (expr2.line,)
                else:
                    # Or location description
                    locdesc = fnc2.getlocdesc(loc2)

                # Delete feedback
                if var1 == '-':
                    if not var2 in deleted:
                        self.add("Remove variable '%s' and assignments to it",
                                 var2)
                        deleted.add(var2)
                    continue

                # Rewrite expr1 (from spec.) with variables of impl.
                expr1org = expr1.copy()
                expr1 = expr1.replace_vars(nmapping)

                mod1 = self.ismod(var1, expr1org)
                mod2 = self.ismod(var2, expr2)

                # Ignore return statements
                if var1 == VAR_RET:
                    continue

                # '*' means adding a new variable (and also statement)
                if var2 == '*':
                    added.add(var1)
                    continue

                # Input
                if var1 == VAR_IN:
                    if mod1 and not mod2: # Read input
                        self.add("Read some input with 'scanf' %s", locdesc)
                    continue

                # Condition
                if var1 == VAR_COND:
                    self.add("Check %s%s", fnc2.getlocdesc(loc2), self.hint(expr1, expr2))
                    continue

                # Output
                if var1 == VAR_OUT:
                    # Distinguish between adding, modification, or removal
                    if mod1 and not mod2: # Add
                        self.add(
                            "Add a 'printf' (output) statement " + locdesc)
                        
                    elif mod1 and mod2: # Modification
                        self.add(
                            "Check the 'printf' (output) statement %s%s", locdesc,
                            self.hint(expr1, expr2, out=True))

                    elif not mod1 and mod2: # Removal
                        self.add(
                            "Remove the 'printf' (output) statement " + locdesc)

                    else:
                        assert False, 'should not happen'

                    continue

                # Regular variable and as above distinguish between
                # add., mod. and rem., and additionally reading input

                if self.isin(expr1):
                    if not self.isin(expr2):
                        self.add(
                            "Use 'scanf' to read an input to the variable '%s' %s",
                            var2, locdesc)
                    continue
                
                if mod1 and not mod2: # Add
                    self.add("Add an assignment to the variable '%s' %s", var2, locdesc)
                elif mod1 and mod2: # Mod
                    #self.add("%% %s=%s (%s) %s=%s (%s)", var1, expr1org, mod1, var2, expr2, mod2)
                    self.add("Check the assignment(s) to the variable '%s' %s%s",
                             var2, locdesc, self.hint(expr1, expr2))
                elif not mod1 and mod2: # Rem
                    self.add("Remove the assignment(s) to the variable '%s'%s",
                             var2, locdesc)
                else:
                    assert False, 'should not happen'
                
            # Report number of variables to add
            numnew = len(added)
            if numnew > 0:
                if numnew == 1:
                    self.add("You will need to use a new variable; for example add 'int %s' at the beginning of the function '%s'",
                             self.newvars(vars2, 1), fname)
                else:
                    self.add("You will need to use some new variables; for example add 'int %s, ...' at the beginning of the function '%s'",
                             self.newvars(vars2, 2), fname)

    def newvars(self, vars, n):
        nvars = set(['n', 'i', 'a', 'b', 'm', 'x', 'y', 'z', 'c', 'j', 'k', 'l'])
        ovars = []
        for v in nvars:
            if v not in vars:
                ovars.append(v)
                if len(ovars) >= n:
                    break
        return ', '.join(ovars)

    def hint(self, expr1, expr2, out=False):
        if out:
            h = self.getouthint(expr1, expr2)
        else:
            h = self.gethint(expr1, expr2, True)
        if h:
            return ' (hint: %s) (repair: %s)' % (h, expr1)
        else:
            return ' (repair: %s)' % (expr1,)

    def getouthint(self, expr1, expr2):
        if (isinstance(expr1, Op) and expr1.name == 'StrAppend' and
            isinstance(expr2, Op) and expr2.name == 'StrAppend'):
            expr1 = expr1.args[1]
            expr2 = expr2.args[1]

            if (isinstance(expr1, Op) and expr1.name == 'StrFormat' and
                isinstance(expr2, Op) and expr2.name == 'StrFormat'):

                if (expr1.args[0].value != expr2.args[0].value):
                    return 'check the format string'

                if len(expr1.args) != len(expr2.args):
                    return 'check the number of arguments'

                for arg1, arg2 in zip(expr1.args[1:], expr2.args[1:]):
                    h = self.gethint(arg1, arg2, first=True)
                    if h:
                        return h

    def gethint(self, expr1, expr2, first=False):
        '''
        Tries to generate some useful hints
        '''

        # Constant
        if isinstance(expr1, Const):
            if isinstance(expr2, Const):    
                if expr1.value != expr2.value:
                    return "use some other constant intead of '%s'" % (expr2.value,)
                else:
                    return
            else:
                if first:
                    return 'use a constant'
                else:
                    return

        # Different variable name
        if isinstance(expr1, Var):
            if isinstance(expr2, Var):
                if expr1.name != expr2.name:
                    return "use another variable instead of '%s'" % (expr2.name,)
                else:
                    return
            else:
                if isinstance(expr2, Const):
                    return "replace '%s' by a variable" % (expr2.value,)
                
                if first:
                    return 'use just a variable'
                else:
                    return

        # Check for changing an order of statement
        vars1 = expr1.vars()
        vars2 = expr2.vars()
        for var1 in vars1:
            if isprimed(var1):
                if unprime(var1) in vars2:
                    return "try changing the order of statements by moving it after the assignment to '%s', or vice-versa" % (unprime(var1),)
            else:
                if prime(var1) in vars2:
                    return "try changing the order of statements by moving it before the assignment to '%s', or vice-versa" % (var1,)

        # Operator comparison
        if isinstance(expr1, Op):

            if isinstance(expr2, Op):
                
                # Comparison operators
                for opname, ops in self.opdefs:
                    if expr1.name in ops:
                        if expr2.name in ops:
                
                            # Different operators
                            if expr1.name != expr2.name:
                                return "use a different %s operator instead of '%s'" % (
                                    opname, expr2.name,)

                            # Same operator (check sides)
                            h1 = self.gethint(expr1.args[0], expr2.args[0])
                            if h1:
                                return h1
                            h2 = self.gethint(expr1.args[1], expr2.args[1])
                            if h2:
                                return h2

                            se11 = str(expr1.args[0])
                            se12 = str(expr1.args[1])
                            se21 = str(expr2.args[0])
                            se22 = str(expr2.args[1])

                            if se11 == se21 and se12 != se22:
                                return "check the right side of the '%s' operator" % (expr2.name,)
                            if se11 != se21 and se12 == se22:
                                return "check the left side of the '%s' operator" % (expr2.name,)

                        else:
                            aa = 'an' if opname[0] == 'a' else 'a'
                            return 'use %s %s operator' % (aa, opname)

            if expr1.name == 'ite':
                return self.ite_hint(expr1, expr2)

    def ite_hint(self, expr1, expr2):
        '''
        Hints when expr1 is if-then-else
        '''

        #print expr2, isinstance(expr2, Op) and expr2.name == 'ite'

        if isinstance(expr2, Op) and expr2.name == 'ite':
            h = self.gethint(expr1.args[0], expr2.args[0])
            if h:
                return h
            h = self.gethint(expr1.args[1], expr2.args[1])
            if h:
                return h
            h = self.gethint(expr1.args[2], expr2.args[2])
            if h:
                return h
        else:
            return 'try using an if-then-else to make a conditional assignment'

    def ismod(self, var, expr):
        '''
        Checks if expr is modified
        '''

        return not (isinstance(expr, Var) and expr.name == var
                    and expr.primed == False)

    def isin(self, expr):
        '''
        Checks if expr is reading of the input
        '''

        return (isinstance(expr, Op) and 
            (expr.name == 'ListHead' or (expr.name == 'ArrayAssign'
                                         and self.isin(expr.args[2]))))
                

        
