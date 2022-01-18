import networkx as nx
import matplotlib
import matplotlib.pyplot as plt
from itertools import permutations

from clara.model import SPECIAL_VARS, Const, Var


def jaccard(list1, list2):
    intersection = len(list(set(list1).intersection(list2)))
    union = (len(list1) + len(list2)) - intersection
    return float(intersection) / union


class GraphMatching():
    def __init__(self, fnc1, fnc2):
        self.ICF = fnc2
        self.CF = fnc1
        self.ICG = None
        self.CG = None
        self.labelMatch = []
        self.edgeMatch = []
        self.ICDict = {}
        self.CDict = {}
        self.ICDictInvert = {}
        self.CDictInvert = {}
        self.finalMatrix = []
        self.finalMatching = {}
        self.longer = 0
        self.removedLocs = {}

    def createGraphs(self):
        self.ICG = self.makeGraph(self.ICF)
        self.CG = self.makeGraph(self.CF)
        self.CDict = self.createLocLabelDict(self.CG)
        self.ICDict = self.createLocLabelDict(self.ICG)

    def createLocLabelDict(self, G):
        locLabels = {}
        for name, attr in list(G.nodes(data=True)):
            locLabels[name] = attr['label']
        return locLabels

    def connect(self, locs, trans, labels, G):
        edges = []
        for l in locs:
            t = trans[l]
            true = t[True]
            false = t[False]
            label = labels[l]
            if not label:
                print(l)
            if true:
                edges += [(l, true, True)]
            else:
                edges += [(l, 0, True)]
            if false:
                edges += [(l, false, False)]
            else:
                edges += [(l, 0, False)]
        G.add_weighted_edges_from(edges)
        return G

    def getLableValue(self, exp):
        if isinstance(exp, Var):
            e = exp.name.strip()
            if 'ind#' in e or 'iter#' in e or 'cond' in e:
                return [e]
            return []
        if isinstance(exp, Const):
            value = exp.value
            if '"' in value:
                value = value.replace("'", '').strip()
            return [value]
        name = exp.name
        args = exp.args
        a = []
        for arg in args:
            a += self.getLableValue(arg)
        return [name] + a

    def makeLabel(self, exp):
        label = []
        for var, e in exp:
            var = str(var)
            if var in SPECIAL_VARS or 'ind#' in var or 'iter#' in var or 'cond' in var:
                label += [str(var)]
            label += self.getLableValue(e)
        return label

    def makeGraph(self, fnc):
        G = nx.MultiDiGraph()
        G.add_node(0, label='None')
        desc = fnc.locdescs
        trans = fnc.loctrans
        exprs = fnc.locexprs
        loc = list(desc.keys())
        allLabels = {}
        for l in loc:
            lno = desc[l].split(" ")[-1]
            exp = exprs[l]
            label = self.makeLabel(exp)
            label = ','.join(list(label))
            if not label:
                label = 'EMPTY'
            allLabels[l] = label

            G.add_node(l, label=label, desc=desc[l], lno=lno, exprs=exp)

        G = self.connect(loc, trans, allLabels, G)
        return G

    def printGraph(self, G):
        for name, attr in list(G.nodes(data=True)):
            print('loc : ', name)

            if len(attr):
                print('label : ', attr['label'])

            edges = list(G.edges(name, data=True))
            for e in edges:
                _, to, trans = e
                print(trans['weight'], ' : ', to)
            print('\n')

    def matchLabels(self):
        G1 = self.CG
        G2 = self.ICG

        len1 = len(list(G1.nodes()))
        len2 = len(list(G2.nodes()))

        labelMatrix = [[0 for _ in range(0, len1)] for _ in range(0, len2)]

        for i, (_, cattr) in enumerate(list(G1.nodes(data=True))):
            cname = cattr['label'].split(',')
            for j, (_, iattr) in enumerate(list(G2.nodes(data=True))):
                iname = iattr['label'].split(',')
                labelMatrix[i][j] = jaccard(cname, iname)

        self.labelMatch = labelMatrix

        self.printGraph(G1)
        print('\n')
        self.printGraph(G2)
        print('\n')
        print(labelMatrix)

    def matchEdges(self):
        G1 = self.CG
        G2 = self.ICG
        dict1 = self.CDict
        dict2 = self.ICDict
        labelDist = self.labelMatch

        len1 = len(list(G1.nodes()))
        len2 = len(list(G2.nodes()))
        edgeMatrix = [[0 for i in range(0, len1)] for i in range(0, len2)]
        for i, (cname, cattr) in enumerate(list(G1.nodes(data=True))):
            for j, (iname, iattr) in enumerate(list(G2.nodes(data=True))):
                if len(cattr) == 0 and len(iattr) == 0:
                    edgeMatrix[i][j] = 1
                elif len(cattr) == 0:
                    edgeMatrix[i][j] = 0
                elif len(iattr) == 0:
                    edgeMatrix[i][j] = 0
                else:
                    edges1 = list(G1.edges(cname, data=True))
                    _, t1, _ = edges1[0]
                    _, f1, _ = edges1[1]
                    edges2 = list(G2.edges(iname, data=True))
                    _, t2, _ = edges2[0]
                    _, f2, _ = edges2[1]
                    t1 = dict1[t1]
                    t2 = dict2[t2]
                    f1 = dict1[f1]
                    f2 = dict2[f2]
                    edgeMatrix[i][j] = 0.5*labelDist[t1][t2] + \
                        0.5*labelDist[f1][f2]
        self.edgeMatch = edgeMatrix
        # print(edgeMatrix)

    def createFinalSimilarity(self):
        edges = self.edgeMatch
        labels = self.labelMatch
        len2 = len(edges)
        len1 = len(edges[0])
        matching = {}
        final = [[0 for i in range(0, len1)] for i in range(0, len2)]
        for i in range(0, len1):
            temp = 0
            index = 0
            for j in range(0, len2):
                val = (edges[i][j] + labels[i][j]) / 2
                if val > temp:
                    temp = val
                    index = j
                final[i][j] = (edges[i][j] + labels[i][j]) / 2
            matching[i] = [index, temp]
        self.finalMatrix = final
        self.finalMatching = matching
        print(matching)

    def allNodeCombinations(self):
        G1 = self.CG
        G2 = self.ICG
        d1 = self.CDict
        d2 = self.ICDict

        self.printGraph(G1)

        l1 = list(G1.nodes())
        l2 = list(G2.nodes())
        rev = False
        if len(l1) < len(l2):
            temp = l2
            l2 = l1
            l1 = temp
            rev = True
            self.longer = 1
        elif len(l1) > len(l2):
            self.longer = 2

        allComb = []
        permut = permutations(l1, len(l2))
        for comb in permut:
            zipped = zip(comb, l2)
            allComb.append(list(zipped))

        bestMatch = []
        score = 0

        print(G1.nodes(data=True))
        for match in allComb:
            currScore = 0
            for n1, n2 in match:
                lab1 = 0
                lab2 = 0
                if rev:
                    lab1 = d2[n1]
                    lab2 = d1[n2]
                else:
                    lab1 = d1[n1]
                    lab2 = d2[n2]

                labelDist = jaccard(lab1.split(','), lab2.split(','))

                edges1 = []
                edges2 = []
                if rev:
                    edges1 = list(G1.edges(n2, data=True))
                    edges2 = list(G2.edges(n1, data=True))
                else:
                    edges1 = list(G1.edges(n1, data=True))
                    edges2 = list(G2.edges(n2, data=True))

                if len(edges1) == 0 and len(edges2) == 0:
                    currScore += 0.5 + 0.5*labelDist
                    continue
                elif len(edges1) == 0 or len(edges2) == 0:
                    currScore += 0.5*labelDist
                    continue

                _, t1, _ = edges1[0]
                _, f1, _ = edges1[1]
                _, t2, _ = edges2[0]
                _, f2, _ = edges2[1]
                

                # if rev:
                #     t1 = d2[t1]
                #     t2 = d1[t2]
                #     f1 = d2[f1]
                #     f2 = d1[f2]
                # else:
                t1 = d1[t1]
                t2 = d2[t2]
                f1 = d1[f1]
                f2 = d2[f2]

                t1 = t1.split(',')
                t2 = t2.split(',')
                f1 = f1.split(',')
                f2 = f2.split(',')

                edgeDist = 0.5*jaccard(t1, t2) + 0.5*jaccard(f1, f2)
                currScore += (labelDist + edgeDist) / 2

            if currScore > score:
                score = currScore
                bestMatch = match
        matching = {}
        # d1 = self.CDict
        # d2 = self.ICDict

        for n1, n2 in bestMatch:
            if rev:
                matching[n2] = n1
            else:
                matching[n1] = n2
        print(matching)
        self.createModel(rev, bestMatch, matching)

    def createModel(self, rev, bestMatch, matching):
        d1 = self.CDict
        d2 = self.ICDict

        G1 = self.CG
        G2 = self.ICG

        # if rev:
        #     new_e1 = {}
        #     new_d1 = {}
        #     new_t1 = {}
        #     for n1, n2 in bestMatch:
        #         if n1 == 'None' and n2 == 'None':
        #             continue
        #         loc2 = d2[n1]
        #         new_e1[loc2] = G1.nodes[n2]['exprs']
        #         new_d1[loc2] = G1.nodes[n2]['desc']

        #         edges1 = list(G1.edges(n2, data=True))
        #         _, t1, _ = edges1[0]
        #         _, f1, _ = edges1[1]
        #         if t1 == 'None':
        #             t1 = None
        #         else:
        #             t1 = d1[t1]

        #         if f1 == 'None':
        #             f1 = None
        #         else:
        #             f1 = d1[f1]
        #         new_t1[loc2] = {True: t1, False: f1}
        #     for k in matching:
        #         if matching[k] == 1:
        #             self.CF.initloc = k
        #     self.CF.locexprs = new_e1
        #     self.CF.loctrans = new_t1
        #     self.CF.locdescs = new_d1

        # else:
        new_e2 = {}
        new_d2 = {}
        new_t2 = {}
        match_incorr = {}
        for n1, n2 in bestMatch:
            c1 = n1
            c2 = n2
            if rev:
                c1 = n2
                c2 = n1
            # loc1 = d1[c1]
            # loc2 = d2[c2]
            match_incorr[c2] = c1

        print('\n', match_incorr, '\n', bestMatch)

        # print('\n', self.ICF.loctrans)
        # print('\n', self.ICDict)
        print('\n', self.ICF, '\n')

        print('\n', self.CF, '\n')

        for n1, n2 in bestMatch:
            c1 = n1
            c2 = n2
            if rev:
                c1 = n2
                c2 = n1
            if c1 == 0 and c2 == 0:
                continue
            loc1 = c1
            new_e2[loc1] = G2.nodes[c2]['exprs']
            print(loc1, G2.nodes[c2]['desc'])
            new_d2[loc1] = G2.nodes[c2]['desc']

            edges2 = list(G1.edges(loc1, data=True))
            _, t2, _ = edges2[0]
            _, f2, _ = edges2[1]

            if t2 == 0:
                t2 = None

            if f2 == 0:
                f2 = None
            new_t2[loc1] = {True: t2, False: f2}
        if self.longer == 2:
            locs = d1.keys()
            extra = sorted(list(set(locs) - set(matching.keys())))
            for e in extra:
                new_e2[e] = {}
                edges2 = list(G1.edges(e, data=True))
                _, t2, _ = edges2[0]
                _, f2, _ = edges2[1]
                if t2 == 0:
                    t2 = None

                if f2 == 0:
                    f2 = None

                new_t2[e] = {True: t2, False: f2}
            for e in extra[::-1]:
                trans = new_t2[e][True]
                flag = False
                while(trans not in new_d2):
                    if trans == max(extra) or trans == None:
                        flag = True
                        break
                    if new_t2[trans][True] < trans:
                        trans = new_t2[trans][False]
                    else:
                        trans = new_t2[trans][True]
                if flag:
                    des = 'At the end of the function'
                else:
                    des = new_d2[trans]
                new_d2[e] = des
        remLocs = list(self.ICF.locexprs.keys() - match_incorr.keys())
        for l in remLocs:
            self.removedLocs[l] = (self.ICF.locexprs[l], self.ICF.locdescs[l])
        self.ICF.initloc = 1
        self.ICF.locexprs = new_e2
        self.ICF.loctrans = new_t2
        self.ICF.locdescs = new_d2


        # print(new_e2)
        print('\n', self.ICF, '\n')
        # print('\n', self.CF.locexprs)
        
        # print('\n', new_t2)
        # print('\n', self.CF.loctrans)
