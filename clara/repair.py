'''
Repair algorithm
'''

# Python imports
import sys
import time

# External libs
from zss import Node, simple_distance as tree_distance

# clara imports
from common import debug
from interpreter import RuntimeErr, isundef
from model import isprimed, unprime, prime, SPECIAL_VARS, VAR_IN, VAR_OUT
from model import Var, Const, Op
from matching import Matching


class StructMismatch(Exception):
    pass


class Timeout(Exception):
    pass


def unprimes(x):
    return unprime(x) if isprimed(x) else x


def label_dist(m):

    def f(l1, l2):
        if not l1:
            return 0 if (not l2) else 3
        if not l2:
            return 0 if (not l1) else 3

        (t1, v1) = l1
        (t2, v2) = l2

        if t1 != t2:
            return 2

        if t2 == 'V':
            if isprimed(v2):
                v2 = prime(m.get(unprime(v2), 'X'))
            else:
                v2 = m.get(v2, 'X')

        return 0 if v1 == v2 else 1
    
    return f


class Repair(object):

    def __init__(self, timeout=60, verbose=False, solver=None,
                 allowsuboptimal=True, cleanstrings=False):
        self.starttime = None
        self.timeout = timeout
        self.verbose = verbose
        self.cleanstrings = cleanstrings

        if solver is None:
            from ilp import Solver
            solver = Solver
        self.solver = solver(verbose=verbose, allowsuboptimal=allowsuboptimal)

    def lefttime(self):
        if not self.timeout:
            return 365 * (24 * 3600)  # A year
        return self.timeout - (time.time() - self.starttime)
                   
    def debug(self, msg, *args):
        if not self.verbose:
            return
        debug(msg, *args)

    def gettrace(self, P, inter, ins, args, entryfnc):

        # Check inputs and arguments
        assert ins or args, "Inputs or argument required"
        if ins:
            assert isinstance(ins, list), "List of inputs expected"
        if args:
            assert isinstance(args, list), "List of arguments expected"

        if ins and args:
            assert len(ins) == len(args), \
                "Equal number of inputs and arguments expected"

        # Populate ins or args (whichever may be missing)
        if not ins:
            ins = [None for _ in xrange(len(args))]
        if not args:
            args = [None for _ in xrange(len(ins))]

        I = inter(entryfnc=entryfnc)
        T = {}
        for i, a in zip(ins, args):
            t = I.run(P, ins=i, args=a)

            # Split trace w.r.t. fncs and locs
            for (fnc, loc, mem) in t:
                if fnc not in T:
                    T[fnc] = {}
                if loc not in T[fnc]:
                    T[fnc][loc] = []
                T[fnc][loc].append(mem)

        return T
    
    def repair(self, P, Q, inter, ins=None, args=None, entryfnc=None,
               ignoreio=False, ignoreret=False):

        self.starttime = time.time()

        self.vignore = set()
        if ignoreio:
            self.vignore |= set([VAR_IN, VAR_OUT])

        # (1) Check struct match
        M = Matching(verbose=self.verbose)
        self.sm = M.match_struct(P, Q)
        if self.sm is None:
            raise StructMismatch('')

        # (2) Obtain trace of P
        self.trace = self.gettrace(P, inter, ins, args, entryfnc)

        # (3) Repair each fnc sepearately
        self.inter = inter()
        results = {}
        for fnc1 in P.getfncs():
            fnc2 = Q.getfnc(fnc1.name)
            results[fnc1.name] = (self.repair_fnc(fnc1, fnc2) +
                                  (self.sm[fnc1.name],))

        self.debug('total time: %.3f', round(time.time() - self.starttime, 3))

        return results

    def filter_potential(self, P):
        for loc1 in P:
            for var1 in P[loc1]:
                totalcost = 0
                newp = []
                for (m, cost, order) in sorted(P[loc1][var1],
                                               key=lambda x: x[1]):
                    totalcost += cost
                    
                if totalcost == 0:
                    self.debug('removing %s-%s from P, due to total cost 0',
                               loc1, var1)
                    P[loc1][var1] = []

    def repair_fnc(self, f1, f2):

        # Remember params mapping
        self.pmap = {p1: p2 for (p1, p2) in zip(f1.getparamnames(),
                                                f2.getparamnames())}

        P = {}
        pgenstart = time.time()
        # (1) Generate "potential" sets
        self.V1 = (f1.getvars() | SPECIAL_VARS | set(['-'])) - self.vignore
        self.V2 = (f2.getvars() | SPECIAL_VARS | set(['*'])) - self.vignore
        self.getexprs(f1, f2)
        for loc1 in f1.locs():
            loc2 = self.sm[f1.name][loc1]
            P[loc1] = {}
            for var1 in self.V1 | set(['-']):
                self.debug('Generating P for %s-%s', loc1, var1)
                tptime = time.time()
                P[loc1][var1] = list(self.potential(f1, f2, loc1, var1, loc2))
                if self.verbose:
                    assert var1 == '-' or len(P[loc1][var1]) > 0, \
                        '%s,%s' % (loc1, var1)
                    for (m, cost, order) in P[loc1][var1]:
                        self.debug('P %s-%s-%s %s %s %s',
                                   f1.name, loc1, var1, cost, m, order)
                    self.debug('P for %s-%s generated in %.3fs',
                               loc1, var1, round(time.time() - tptime, 3))
        self.filter_potential(P)
        self.pgentime = time.time() - pgenstart

        # (2) Give "potential" sets to a solver
        solvertime = self.lefttime()
        res = self.solver.solve(self.V1 | set(['-']), self.V2 | set(['*']), P,
                                timeout=solvertime)
        self.debug('PGEN time: %.3f' % round(self.pgentime, 3))
        self.debug('mapping: %s', res[0])
        self.debug('repairs: %s', res[1])
        return res

    def getexprs(self, f1, f2):

        self.E1 = {}
        self.T1 = {}
        for loc1 in f1.locs():
            self.E1[loc1] = {}
            self.T1[loc1] = {}
            for var1 in self.V1:
                self.E1[loc1][var1] = f1.getexpr(loc1, var1)
                self.T1[loc1][var1] = self.totree(self.E1[loc1][var1])
                if self.verbose:
                    self.debug('T1 %s-%s-%s := %s', f1.name, loc1, var1,
                               self.treetostr(self.T1[loc1][var1]))

        self.E2 = {}
        self.T2 = {}
        for loc2 in f2.locs():
            self.E2[loc2] = {}
            self.T2[loc2] = {}
            for var2 in self.V2:
                self.E2[loc2][var2] = f2.getexpr(loc2, var2)
                self.T2[loc2][var2] = self.totree(self.E2[loc2][var2])
                if self.verbose:
                    self.debug('T2 %s-%s-%s := %s', f2.name, loc2, var2,
                               self.treetostr(self.T2[loc2][var2]))

    def totree(self, e):
        if isinstance(e, Var):
            return Node(('V', str(e)))
        if isinstance(e, Const):
            return Node(('C', str(e)))
        if isinstance(e, Op):
            n = Node(('O', e.name))
            for arg in e.args:
                n.addkid(self.totree(arg))
            return n

    def treetostr(self, node):
        l = Node.get_label(node)
        t = None
        if isinstance(l, tuple):
            t, l = l
        if t == 'O':
            return '%s(%s)' % (l, ', '.join(
                map(self.treetostr, Node.get_children(node))))
        return l

    def distance(self, t1, t2, m):
        return tree_distance(t1, t2, label_dist=label_dist(m))

    def one_to_ones(self, S1, S2, m1, m2, taken=None):

        if self.lefttime() < 0:
            raise Timeout()

        if taken is None:
            taken = set()

        if len(S1) == 0 or len(S2) == len(taken):
            yield []
            return

        s1, SS1 = S1[0], S1[1:]

        for s2 in S2:

            if s2 in taken:
                continue
                
            if s1 == m1 and s2 != m2:
                continue

            if s2 != '*' and s2 == m2 and s1 != m1:
                continue

            if (s1 in SPECIAL_VARS or s2 in SPECIAL_VARS) and s1 != s2:
                continue

            if s1 in self.pmap and s2 != self.pmap[s1]:
                continue

            if s2 == '*':
                newtaken = taken
            else:
                newtaken = set(taken)
                newtaken.add(s2)

            for m in self.one_to_ones(SS1, S2, m1, m2, newtaken):
                m = list(m)
                m.append((s1, s2))
                yield m

    def getorder(self, var, expr, m):
        if var == '*' or var in SPECIAL_VARS:
            return []
        vars = expr.vars()
        order = []
        for var2 in vars:
            if isprimed(var2):
                var2 = unprime(var2)
                var2 = m[var2]
                if var2 == '*':
                    continue
                if var == var2:
                    return None
                order.append((var2, var))
            else:
                var2 = m[var2]
                if var2 == '*':
                    continue
                if var != var2 and var2 != '*':
                    order.append((var, var2))
        order.sort()
        return order

    def potential(self, f1, f2, loc1, var1, loc2):

        varp1 = prime(var1)
        expr1 = self.E1[loc1][var1]
        isid = isinstance(expr1, Var) and expr1.name == var1
        tree1 = self.T1[loc1][var1]
        vars1 = list(set(map(unprimes, expr1.vars())) | set([var1]))
        vars1.sort()
        
        V1 = list(self.V1 - set(['-']))
        V1.sort()
        V2 = list(self.V2)
        V2.sort()
        
        for var2 in V2:

            sofar = set()

            # Special vars can be only mapped to special vars
            if (var1 in SPECIAL_VARS or var2 in SPECIAL_VARS) and var1 != var2:
                continue

            # Params can only be mapped to params
            if var1 in self.pmap and var2 != self.pmap[var1]:
                continue

            # Cannot delete new variable
            if var1 == '-' and var2 == '*':
                continue

            expr2 = self.E2[loc2][var2]
            tree2 = self.T2[loc2][var2]
            vars2 = list(set(map(unprimes, expr2.vars())) | set([var2]))
            vars2.sort()

            # (0) Deletes are special
            if var1 == '-':
                delexpr = Var(var2)
                deltree = self.totree(delexpr)
                delcost = self.distance(tree2, deltree, {var2: var2})
                if delcost:
                    yield ([(var1, var2)], delcost, ())
                continue

            # (1) Generate corrects (if not new variable)
            if var2 != '*':
                for m in self.one_to_ones(vars2, V1, var2, var1):
                    m = [(s2, s1) for (s1, s2) in m]
                    ok = True
                    for mem1 in self.trace.get(f1.name, {}).get(loc1, []):
                        val1 = mem1.get(varp1)
                        
                        if isundef(val1):
                            continue
                        
                        if isinstance(val1, str) and self.cleanstrings:
                            val1 = val1.strip()
                            
                        mem2 = {v2: mem1.get(v1) for (v1, v2) in m}
                        mem2.update({prime(v2): mem1.get(prime(v1))
                                     for (v1, v2) in m})
                        try:
                            val2 = self.inter.execute(expr2, mem2)
                            if isinstance(val2, str) and self.cleanstrings:
                                val2 = val2.strip()

                            if  val2 != val1:
                                ok = False
                                break
                        except RuntimeErr:
                            ok = False
                            break
                    if ok:
                        order = self.getorder(var2, expr2,
                                              {v: v for v in vars2})
                        if order is None:
                            assert False, 'order error %s %s' % (var2, expr2)
                        ms = list(m)
                        ms.sort()
                        sofar.add((tuple(ms), tuple(order)))
                        yield (m, 0, set(order))

            # (2) Generate repairs
            for m in self.one_to_ones(vars1, V2, var1, var2):
                order = self.getorder(var2, expr1, dict(m))
                if order is None:
                    self.debug(
                        'skipping repair %s := %s (%s) because \
impossible order',
                        var1, expr1, m)
                    continue
                if isid and var2 == '*':
                    cost = 0
                else:
                    cost = self.distance(tree2, tree1, dict(m))
                    
                # Account for *declaring* a new variable
                if var2 == '*' and loc1 == 1:
                    cost += 1
                
                ms = list(m)
                ms.sort()
                if (tuple(ms), tuple(order)) in sofar:
                    continue
                yield (m, cost, set(order))
