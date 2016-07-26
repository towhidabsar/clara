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
        self.arithops = set(['+', '-', '*', '/', '%'])
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

            # Remember input feedback
            infeed = False

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

                # Remember current var
                self.cvar = var2

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
                    if (not infeed) and mod1 and not mod2: # Read input
                        self.add("Read some input with 'scanf' %s", locdesc)
                        infeed = True
                    continue

                # Condition
                if var1 == VAR_COND:
                    self.add("Change %s%s", fnc2.getlocdesc(loc2), self.hint(expr1, expr2))
                    continue

                # Output
                if var1 == VAR_OUT:
                    # Distinguish between adding, modification, or removal
                    if mod1 and not mod2: # Add
                        self.add(
                            "Add a 'printf' (output) statement " + locdesc)
                        
                    elif mod1 and mod2: # Modification
                        self.add(
                            "Change the 'printf' (output) statement %s%s", locdesc,
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
                        infeed = True
                        for i, feed in enumerate(self.feedback):
                            if feed.startswith('Read some input'):
                                self.feedback.pop(i)
                                break
                    continue
                
                if mod1 and not mod2: # Add
                    self.add("Assign a value to the variable '%s' %s", var2, locdesc)
                elif mod1 and mod2: # Mod
                    #self.add("%% %s=%s (%s) %s=%s (%s)", var1, expr1org, mod1, var2, expr2, mod2)
                    self.add("Change the assigned value(s) to the variable '%s' %s%s",
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
                    self.add("You will need to declare and use a new variable in the beginning of the function '%s'",
                             fname)
                else:
                    self.add("You will need to declare and use some new variables in the beginning of the function '%s'",
                             fname)

    def hint(self, expr1, expr2, out=False):
        if out:
            h = self.getouthint(expr1, expr2)
        else:
            h = self.gethint(expr1, expr2, True)
            
        if h:
            h = ' (hint: %s)' % (h,)
        else:
            h = ''

        #h += ' (repair: %s)' % (expr1,)

        return h

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

        elif isinstance(expr1, Op) and expr1.name == 'ite':
            h = self.ite_hint(expr1, expr2)
            if h:
                return h

        h = self.gettemplate(expr1, outer=True)
        if h:
            return 'use template: %s' % (h,)

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
            elif isinstance(expr2, Var):
                return "use a constant instead of a variable '%s'" % (expr2.name,)
            
            else:
                if first:
                    return 'use a just constant'
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

        # Different variable name
        if isinstance(expr1, Var):
            if isinstance(expr2, Var):
                if expr1.name != expr2.name:
                    return "use another variable instead of '%s'" % (expr2.name,)
                else:
                    return
            else:
                if isinstance(expr2, Const):
                    return "replace the constant '%s' by a variable" % (expr2.value,)
                
                if first:
                    return 'use just a variable'
                else:
                    return

        # Operation comparison
        if isinstance(expr1, Op):

            if isinstance(expr2, Op):
                
                # Operators
                for opname, ops in self.opdefs:
                    if expr1.name in ops:
                        if expr2.name in ops:

                            same1 = self.issame(expr1.args[0], expr2.args[0])
                            same2 = self.issame(expr1.args[1], expr2.args[1])
                
                            # Different operators
                            if same1 and same2 and expr1.name != expr2.name:
                                return "use a different %s operator instead of '%s'" % (
                                    opname, expr2.name,)
                            
                            if same1 and expr1.name == expr2.name:
                                h = self.gethint(expr1.args[1], expr2.args[1])
                                if h:
                                    return h

                            if same2 and expr1.name == expr2.name:
                                h = self.gethint(expr1.args[0], expr2.args[0])
                                if h:
                                    return h

                            if first and expr1.name == expr2.name:
                                h1 = self.gethint(expr1.args[0], expr2.args[0])
                                h2 = self.gethint(expr1.args[1], expr2.args[1])
                                if h1 and h2:
                                    return '%s and %s' % (h1, h2)

            if first and expr1.name == 'ite':
                h = self.ite_hint(expr1, expr2)
                if h:
                    return h

        # Nothing else to do, except to generate a template
        if first:
            t = self.gettemplate(expr1, outer=True)
            if t:
                return 'use the template "%s"' % (t,)

    def ite_hint(self, expr1, expr2):
        '''
        Hints when expr1 is if-then-else
        '''

        #print expr2, isinstance(expr2, Op) and expr2.name == 'ite'

        if isinstance(expr2, Op) and expr2.name == 'ite':
            samecond = self.issame(expr1.args[0], expr2.args[0])
            sameT = self.issame(expr1.args[1], expr2.args[1])
            sameF = self.issame(expr1.args[2], expr2.args[2])
            
            if sameT and sameF:
                h = self.gethint(expr1.args[0], expr2.args[0], first=True)
                if h:
                    return h

            if samecond and sameF:
                h = self.gethint(expr1.args[1], expr2.args[1])
                if h:
                    return h

            if samecond and sameT:
                h = self.gethint(expr1.args[2], expr2.args[2])
                if h:
                    return h
        else:
            if not self.hasite(expr2):
                return 'try using an if-then-else to make a conditional assignment/output'

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

    def hasite(self, expr):
        '''
        Check if an expression has a ITE node
        '''
        
        if isinstance(expr, Const) or isinstance(expr, Var):
            return False

        if isinstance(expr, Op):
            if expr.name == 'ite':
                return True
            
            for arg in expr.args:
                if self.hasite(arg):
                    return True

            return False

    def issame(self, expr1, expr2):
        '''
        Checks if two expressions are the same
        '''
        
        if isinstance(expr1, Const):
            if isinstance(expr2, Const):
                if expr1.value == expr2.value:
                    return True
                elif expr1.value.replace(' ', '') == expr2.value.replace(' ', ''):
                    return True
            else:
                return False

        if isinstance(expr1, Var):
            if (isinstance(expr2, Var) and expr1.name == expr2.name
                and expr1.primed == expr2.primed):
                return True
            else:
                return False

        if isinstance(expr1, Op):
            if (not isinstance(expr2, Op) or expr1.name != expr2.name
                or len(expr1.args) != len(expr2.args)):
                return False
        
            for arg1, arg2 in zip(expr1.args, expr2.args):
                if not self.issame(arg1, arg2):
                    return False

            return True

    def gettemplate(self, expr, outer=False):
        '''
        Generates a template out of a (correct) expression
        '''

        if isinstance(expr, Const) or isinstance(expr, Var):
            return '_'

        if isinstance(expr, Op):

            # Operators
            for _, ops in self.opdefs:
                if expr.name in ops and len(expr.args) == 2:
                    t1 = self.gettemplate(expr.args[0])
                    t2 = self.gettemplate(expr.args[1])
                    if t1 and t2:
                        h = '%s %s %s' % (t1, expr.name, t2)
                        if outer:
                            return h
                        else:
                            return '(%s)' % (h,)

            # TODO: Unary operators (!?)

            # Printf
            if expr.name == 'StrAppend':
                expr2 = expr.args[1]
                if isinstance(expr2, Op) and expr2.name == 'StrFormat':
                    targs = map(lambda x: self.gettemplate(x, outer=True), expr2.args)

                    if not all(targs):
                        return

                    return 'printf(%s);' % (', '.join(targs), )

            # If-then-else
            if expr.name == 'ite':
                tcond = self.gettemplate(expr.args[0], outer=True)
                tt = self.gettemplate(expr.args[1], outer=True)
                tf = self.gettemplate(expr.args[2], outer=True)

                if not tcond or not tt or not tf:
                    return

                if not tt.startswith('if') and self.cvar != VAR_OUT:
                    tt = '%s = %s;' % (self.cvar, tt)

                ismod2 = self.ismod(self.cvar, expr.args[2])
                
                if not tf.startswith('if') and self.cvar != VAR_OUT:
                    tf = '%s = %s;' % (self.cvar, tf)

                if ismod2:
                    return 'if (%s) { %s } else { %s }' % (tcond, tt, tf)
                else:
                    return 'if (%s) { %s }' % (tcond, tt)

        
