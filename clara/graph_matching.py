import networkx as nx
import matplotlib
import matplotlib.pyplot as plt

from clara.model import SPECIAL_VARS, Const, Var
from clara.repair import label_dist


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

    def createGraphs(self):
        self.ICG = self.makeGraph(self.ICF)
        self.CG = self.makeGraph(self.CF)
        self.CDict = self.createLocLabelDict(self.CG)
        self.ICDict = self.createLocLabelDict(self.ICG)

    def createLocLabelDict(self, G):
        locLabels = {}
        for name, attr in list(G.nodes(data=True)):
            if len(attr):
                locLabels[name] = attr['loc']
            else:
                locLabels[name] = 0
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
                edges += [(label, labels[true], True)]
            else:
                edges += [(label, 'None', True)]
            if false:
                edges += [(label, labels[false], False)]
            else:
                edges += [(label, 'None', False)]
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
        G.add_node('None')
        desc = fnc.locdescs
        trans = fnc.loctrans
        exprs = fnc.locexprs
        loc = list(desc.keys())
        allLabels = {}
        for l in loc:
            des = desc[l].split(" ")
            lno = des[-1]
            d = []
            if 'loop' in des:
                d += ['loop']
            elif ' if ' in des:
                d += ['if']
            elif 'else' in des:
                d += ['else']
            if 'after' in des or '*after*' in des:
                d += ['after']
            elif 'update' in des:
                d += ['update']
            elif 'condition' in des:
                d += ['condition']
            elif 'inside' in des:
                d += ['inside']
            elif 'beginning' in des:
                d += ['beginning of fnc']
                lno = '1'
            elif 'print' in des:
                d += ['print']
            d = ' '.join(d)
            exp = exprs[l]
            label = self.makeLabel(exp)
            label = ','.join(list(label))
            if not label:
                label = 'EMPTY'
            allLabels[l] = label

            G.add_node(label, loc=l, desc=d, lno=lno, exprs=exp)

        G = self.connect(loc, trans, allLabels, G)
        return G

    def printGraph(self, G):
        for name, attr in list(G.nodes(data=True)):
            print(name)

            if len(attr):
                print('loc : ', attr['loc'])

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

        labelMatrix = [[0 for i in range(0, len1)] for i in range(0, len2)]

        for i, cname in enumerate(list(G1.nodes())):
            cname = cname.split(',')
            for j, iname in enumerate(list(G2.nodes())):
                iname = iname.split(',')
                labelMatrix[i][j] = jaccard(cname, iname)

        self.labelMatch = labelMatrix

        self.printGraph(G1)
        print('\n')
        self.printGraph(G2)
        print('\n')
        # print(labelMatrix)

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
                    edgeMatrix[i][j] = 0.5*labelDist[t1][t2] + 0.5*labelDist[f1][f2]
        self.edgeMatch = edgeMatrix
        # print(edgeMatrix)

    def createFinalSimilarity(self):
        edges = self.edgeMatch
        labels = self.labelMatch
        len2 = len(edges)
        len1 = len(edges[0])
        matching = {}
        final = [[0 for i in range(0, len1)] for i in range(0, len2)]
        for i in range(0,len1):
            temp = 0
            index = 0
            for j in range(0,len2):
                val = (edges[i][j] + labels[i][j]) / 2
                if val > temp:
                    temp = val
                    index = j
                final[i][j] = (edges[i][j] + labels[i][j]) / 2
            matching[i] = [index, temp]
        self.finalMatrix = final
        self.finalMatching = matching
        print(matching)

    # def printFinal(self):
