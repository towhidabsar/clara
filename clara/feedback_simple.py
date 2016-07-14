'''
Generating simple, but not raw textual feedback from repair
'''

from model import VAR_OUT, VAR_IN, VAR_COND, Var, Op

# TODO: Maybe add importance to feedback, so only
# a limited number of feedback messages would be shown

class SimpleFeedback(object):

    def __init__(self, impl, spec, result):
        self.impl = impl
        self.spec = spec
        self.result = result
        self.feedback = []

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
                expr1 = expr1.replace_vars(nmapping)

                mod1 = self.ismod(var1, expr1)
                mod2 = self.ismod(var2, expr2)

                # Input
                if var1 == VAR_IN:
                    if mod1 and not mod2: # Read input
                        self.add("Read some input with 'scanf' %s", locdesc)
                        continue

                # '*' means adding a new variable (and also statement)
                if var2 == '*':
                    added.add(var1)
                    continue

                # Condition
                if var1 == VAR_COND:
                    self.add("Check " + fnc2.getlocdesc(loc2))
                    continue

                # Output
                if var1 == VAR_OUT:
                    # Distinguish between adding, modification, or removal
                    if mod1 and not mod2: # Add
                        self.add(
                            "Add a 'printf' (output) statement " + locdesc)
                        
                    elif mod1 and mod2: # Modification
                        self.add(
                            "Check a 'printf' (output) statement " + locdesc)

                    elif not mod1 and mod2: # Removal
                        self.add(
                            "Remove a 'printf' (output) statement " + locdesc)

                    else:
                        assert False, 'should not happen'

                    continue

                # Regular variable and as above distinguish between
                # add., mod. and rem., and additionally reading input

                if self.isin(expr1):
                    self.add(
                        "Use 'scanf' to read an input to the variable '%s' %s",
                        var2, locdesc)
                    continue
                
                if mod1 and not mod2: # Add
                    self.add("Add an assignment to the variable '%s' %s", var2, locdesc)
                elif mod1 and mod2: # Mod
                    self.add("Check the assignment(s) to a variable '%s' %s",
                             var2, locdesc)
                elif not mod1 and mod2: # Rem
                    self.add("Remove the assignment(s) to a variable '%s'%s",
                             var2, locdesc)
                else:
                    assert False, 'should not happen'

                # Ignore INPUT and RETURN for now
                
        # Report number of variables to add
        numnew = len(added)
        if numnew > 0:
            if numnew == 1:
                self.add("You will need to use a new variable")
            else:
                self.add("You will need to use some new variables")

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
                

        
