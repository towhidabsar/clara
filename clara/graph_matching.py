import sys
import time
from matplotlib.pyplot import flag
import networkx as nx
from itertools import permutations, product

from clara.model import SPECIAL_VARS, Const, Var

# find jaccard distance between two labels
def jaccard(list1, list2):
    intersection = len(list(set(list1).intersection(list2)))
    union = (len(list1) + len(list2)) - intersection
    return float(intersection) / union


class GraphMatching():
    def __init__(self, fnc1, fnc2, option):
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
        self.finalScore = {}
        self.longer = 0
        self.removedLocs = {}
        self.option = option
        self.result = []
        self.perms = []

    def createGraphs(self):
        self.ICG = self.makeGraph(self.ICF)
        self.CG = self.makeGraph(self.CF)
        self.CDict = self.createLocLabelDict(self.CG)
        self.ICDict = self.createLocLabelDict(self.ICG)

    # creates a dictionary where the key is the location and the label is the value
    def createLocLabelDict(self, G):
        locLabels = {}
        for name, attr in list(G.nodes(data=True)):
            locLabels[name] = attr['label']
        return locLabels

    # connects the graph by adding the edges
    # locs is the list of locations
    # trans is the dictionary of tranistions and locations
    # labels is the label name for each node
    # G is the graph
    def connect(self, locs, trans, G):
        edges = []
        # traverses through the locations to access the transitions
        for l in locs:
            # extracts the transitions for the location
            t = trans[l]
            true = t[True]
            false = t[False]

            # adds the edges to the list
            if true:
                edges += [(l, true, True)]
            else:
                edges += [(l, 0, True)]
            if false:
                edges += [(l, false, False)]
            else:
                edges += [(l, 0, False)]
        # adds the edges to the graph
        G.add_weighted_edges_from(edges)
        return G

    # gets the label value of an expression based on the type of expression
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

    # creates a label for a node
    # calls getLabelValue on each expression in the node and appends it to a list
    def makeLabel(self, exp):
        label = []
        for var, e in exp:
            var = str(var)
            if var in SPECIAL_VARS or 'ind#' in var or 'iter#' in var or 'cond' in var:
                label += [str(var)]
            label += self.getLableValue(e)
        return label

    # creates the graph from the function
    def makeGraph(self, fnc):
        # the multidigraph indicates its directed and can have multiple repeated edges
        G = nx.MultiDiGraph()

        # since a transition can go to None, it gives it the location 0 as 0 can never exist
        G.add_node(0, label='None')

        # extracts the locations and dicts for descriptions, transitions and expressions
        desc = fnc.locdescs
        trans = fnc.loctrans
        exprs = fnc.locexprs
        loc = list(desc.keys())
        allLabels = {}

        # creates a node in the graph for every location with a label, line no, exp and desc
        for l in loc:
            lno = desc[l].split(" ")[-1]
            exp = exprs[l]
            label = self.makeLabel(exp)
            label = ','.join(list(label))
            if not label:
                label = 'EMPTY'
            allLabels[l] = label

            G.add_node(l, label=label, desc=desc[l], lno=lno, exprs=exp)

        # calls connect to add the edges to the graph
        G = self.connect(loc, trans, G)
        return G

    #  used to visualise the graph
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

    def createMatchDict(self):
        G1 = self.CG
        G2 = self.ICG
        d1 = self.CDict
        d2 = self.ICDict
        labelSim = {0: {0: 1}}

        # checks to see which graph is shorter
        l1 = list(G1.nodes())
        l2 = list(G2.nodes())
        len_l1 = len(l1)
        len_l2 = len(l2)
        self.shorter = 1
        if len_l1 < len_l2:
            self.result += ['DEL', len_l2-len_l1]
        elif len_l1 > len_l2:
            temp = l2
            l2 = l1
            l1 = temp
            self.result += ['ADD', len_l1-len_l2]
            self.shorter = 2

        # removing node 0 from comparisons because that will always match with each other
        l1.remove(0)
        l2.remove(0)
        for n1 in l1:
            labelSim[n1] = {}
            if self.shorter == 2:
                lab1 = d2[n1]
            else:
                lab1 = d1[n1]
            for n2 in l2:
                if self.shorter == 2:
                    lab2 = d1[n2]
                else:
                    lab2 = d2[n2]
                val = jaccard(lab1.split(','), lab2.split(','))
                labelSim[n1][n2] = val

        possibleMatch = {0: [0]}
        print("Smaller: ", self.shorter)
        for n1 in labelSim:
            options = [k for k, _ in sorted(
                labelSim[n1].items(), key=lambda item: item[1], reverse=True)]
            possibleMatch[n1] = options
        start = time.time()
        # perms = self.createPermutations(possibleMatch)
        self.permBackTrack([0] + l1, possibleMatch, {}, labelSim)
        end = time.time()
        print('Done permutataions', end - start)
        # print('possible match', possibleMatch)
        start = time.time()
        (bestMatch, score) = self.findBestMatch(self.perms, labelSim)
        end = time.time()
        # print('Model Creation', end - start)
        score /= len(possibleMatch)

        print("Score:", score)
        if score < 0.6:
            print('SCORE TOO LESS')
            sys.exit(0)
        self.createModel2(bestMatch)

    def findBestMatch(self, phi, labelScores):
        G1 = self.CG
        G2 = self.ICG
        bestMatch = []
        score = 0
        
        # traversing a possible match for the graphs
        for match in phi:
            currScore = 0
            # traversing each node match
            for n1 in match:
                if n1 == 0:
                    currScore += 1
                    continue
                n2 = match[n1]
                labelDist = labelScores[n1][n2]
                if self.option != 3:
                    edges1 = []
                    edges2 = []
                    if self.shorter == 2:
                        edges1 = list(G1.edges(n2, data=True))
                        edges2 = list(G2.edges(n1, data=True))
                    else:
                        edges1 = list(G1.edges(n1, data=True))
                        edges2 = list(G2.edges(n2, data=True))

                    _, t1, _ = edges1[0]
                    _, f1, _ = edges1[1]
                    _, t2, _ = edges2[0]
                    _, f2, _ = edges2[1]

                    edgeDist = 0
                    if self.shorter == 2:
                        if (t1 == match[t2]):
                            edgeDist += 1
                        if (f1 == match[f2]):
                            edgeDist += 1
                    else:
                        if (t2 == match[t1]):
                            edgeDist += 1
                        if (f2 == match[f1]):
                            edgeDist += 1

                    edgeDist *= 0.5
                    currScore += (labelDist + edgeDist) / 2
                else:
                    currScore += labelDist
            # if currScore is greater than this is the best match of graphs
            if currScore > score:
                score = currScore
                bestMatch = match
        return (bestMatch, score)

    def cartesianProduct(self, set_a, set_b, last, possibleMatch):
        result =[]
        for i in range(0, len(set_a)):
            vals_used = 0
            for j in range(0, len(set_b)):
                if vals_used == 2:
                    break
                if type(set_a[i]) != list:        
                    set_a[i] = [set_a[i]]
                # if set_b[j] in set_a[i]:
                #     continue
                temp = [num for num in set_a[i]]
                temp.append(set_b[j])
                if len(temp) == len(set(temp)):
                    vals_used += 1
                    if last:
                        result.append(dict(zip(possibleMatch, temp)))
                    else:
                        result.append(temp)
                
        return result

    def permBackTrack(self, U, possibleMatch, phi, labelSim):
        if len(U) == len(phi):
            if phi not in self.perms:
                self.perms += [dict(phi)]
            if len(self.perms) == 10000:
                return True
            return False
        unmappedU = set(U) - set(phi.keys())

        for currU in unmappedU:
            unmappedV = set(possibleMatch[currU]) - set(phi.values())

            for currV in unmappedV:
                temp_phi = phi
                temp_phi[currU] = currV
                flag = self.permBackTrack(U, possibleMatch, temp_phi, labelSim)
                if flag:
                    return True
        return False

    def createPermutations(self, possibleMatch):
        perms = []
        # print(len(possibleMatch))
        # size = 0.2 * math.factorial((len(possibleMatch) - 1))
        size = 1
        list_a = list(possibleMatch.values())
        temp = list_a[0]
        
        # do product of N sets
        for i in range(1, len(possibleMatch)):
            temp = self.cartesianProduct(temp, list_a[i], i + 1 == len(possibleMatch), possibleMatch)
            # print(i, len(temp))
        # print(temp)
        # values = (p for p in product(*possibleMatch.values()) if len(set(p)) == len(p))
        # for _ in range(0,size):
        #     # if len(perms) == int(size):
        #     #     return perms
        #     # print(v, set(v), len(perms), len(v), len(set(v)))
        #     # if len(set(v)) != len(v):
        #     #     continue
        #     perms.append(dict(zip(possibleMatch, next(values))))
        return temp

    # analyzes both the graphs and finds a matching based on label distance and edges
    def allNodeCombinations(self):
        G1 = self.CG
        G2 = self.ICG
        d1 = self.CDict
        d2 = self.ICDict

        # checks to see which graph is longer
        l1 = list(G1.nodes())
        l2 = list(G2.nodes())
        rev = False
        len_l1 = len(l1)
        len_l2 = len(l2)
        if len_l1 < len_l2:
            self.result += ['DEL', len_l2-len_l1]
            temp = l2
            l2 = l1
            l1 = temp
            rev = True
            self.shorter = 1
        elif len_l1 > len_l2:
            self.result += ['ADD', len_l1-len_l2]
            self.shorter = 2

        # finds all possible combinations of node matching (exhaustive list)
        # the allComb is a list of lists where the outer list contains 1 possible matching for the entire graph
        allComb = []
        permut = permutations(l1, len(l2))
        for comb in permut:
            if len(allComb) == 1000:
                break
            zipped = zip(comb, l2)
            allComb.append(list(zipped))

        bestMatch = []
        score = 0

        # traversing a possible match for the graphs
        for match in allComb:
            currScore = 0
            # traversing each node match
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
                if self.option != 3:
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
                else:
                    currScore += labelDist
            # if currScore is greater than this is the best match of graphs
            if currScore > score:
                score = currScore
                bestMatch = match
        matching = {}
        print("old ", bestMatch)
        for n1, n2 in bestMatch:
            if rev:
                matching[n2] = n1
            else:
                matching[n1] = n2
        final_score = score/len(l1)
        print("Score:", final_score)
        if final_score < 0.6:
            print('SCORE TOO LESS')
            sys.exit(0)
        self.createModel(bestMatch)

    def createModel2(self, bestMatch):
        # print("Correct\n", self.CF)
        # print("\nIncorrect\n", self.ICF)
        G1 = self.CG
        G2 = self.ICG
        # intialize the following dicts for new expressions, descriptions and transitions of the model
        new_e2 = {}
        new_d2 = {}
        new_t2 = {}
        if self.shorter == 1:
            initloc = bestMatch[self.CF.initloc]
        else:
            # find the maximum location number so we don't have repeated locations
            maxLoc = max(G2.nodes())
            lastLoc = maxLoc
            mappedG1Locs = set(bestMatch.values())
            unmappedG1Locs = list(set(G1.nodes()) - mappedG1Locs)
            new_locs = {}

            # create a mapping of new locations to be added from G1 -> G2
            for l in unmappedG1Locs:
                maxLoc += 1
                new_locs[l] = maxLoc
            
            new_locs.update({v:k for k, v in bestMatch.items()})

        for loc1 in bestMatch:
            if loc1 == 0:
                continue
            loc2 = bestMatch[loc1]

            # if G2 is smaller, reverse the locations as bestMatch is a map from G2 -> G1
            if (self.shorter == 2):
                temp = loc1
                loc1 = loc2
                loc2 = temp
                if loc1 == self.CF.initloc:
                    initloc = loc2
            new_e2[loc2] = G2.nodes[loc2]['exprs']
            new_d2[loc2] = G2.nodes[loc2]['desc']

            edges = list(G1.edges(loc1, data=True))
            _, t_edge, _ = edges[0]
            _, f_edge, _ = edges[1]
            if self.shorter == 1:
                t = None if bestMatch[t_edge] == 0 else bestMatch[t_edge]
                f = None if bestMatch[f_edge] == 0 else bestMatch[f_edge]
            else:
                t = None if new_locs[t_edge] == 0 else new_locs[t_edge]
                f = None if new_locs[f_edge] == 0 else new_locs[f_edge]
            new_t2[loc2] = {True: t, False: f}

        # add the remaining locations since G2 is smaller
        if self.shorter == 2:
            for currLoc in unmappedG1Locs:
                edges = list(G1.edges(currLoc, data=True))
                _, finalTrue, _ = edges[0]
                _, finalFalse, _ = edges[1]
                trans = finalTrue
                mainLoc = currLoc
                desc = 'At the end of the function'
                flag = False
                # _, f_edge, _ = edges[1]
                while(trans == 0 or trans not in mappedG1Locs):
                    if trans == lastLoc:
                        flag = True
                        break
                    if trans < currLoc or trans == 0:
                        _, false_edge, _ = edges[1]
                        if trans == 0 and false_edge == 0:
                            flag = True
                            break
                        currLoc = trans
                        trans = false_edge
                    else:
                        currLoc = trans
                        edges = list(G1.edges(trans, data=True))
                        _, true_edge, _ = edges[0]
                        trans = true_edge
                newG2Loc = new_locs[mainLoc]
                new_e2[newG2Loc] = []
                new_t2[newG2Loc] = {True: None if finalTrue == 0 else new_locs[finalTrue], False: None if finalFalse == 0 else new_locs[finalFalse]}
                
                if not flag:
                    desc = G2.nodes[new_locs[trans]]['desc']
                new_d2[newG2Loc] = desc
        if self.shorter == 1:
            # adds all the expressions into a list so they can be adde to the feedback
            remLocs = list(self.ICF.locexprs.keys() - bestMatch.values())
            for l in remLocs:
                self.removedLocs[l] = (self.ICF.locexprs[l], self.ICF.locdescs[l])
        self.ICF.initloc = initloc
        self.ICF.locexprs = new_e2
        self.ICF.loctrans = new_t2
        self.ICF.locdescs = new_d2

        # print('\n\nNew Incorrect', self.ICF)

        print('\n', bestMatch)



    # based on the correct graph and the matching, it recreates the incorrect model
    # if the correct graph is longer, nodes are added to the incorrect graph
    # if the correct graph is shorter, nodes are removed from the incorrect graph
    def createModel(self, bestMatch):
        d1 = self.CDict

        G1 = self.CG
        G2 = self.ICG

        # intialize the following dicts for new expressions, descriptions and transitions of the model
        new_e2 = {}
        new_d2 = {}
        new_t2 = {}
        
        # creates a dictionary for the mapped nodes
        match_incorr = {}
        print(bestMatch)
        for n1 in bestMatch:
            n2 = bestMatch[n1]
            c1 = n1
            c2 = n2
            if self.shorter == 1:
                c1 = n2
                c2 = n1
            match_incorr[c2] = c1

        # based on the matches it recreates the new model
        # n1 and n2 are location/node numbers
        for n1 in bestMatch:
            n2 = bestMatch[n1]
            c1 = n1
            c2 = n2
            if self.shorter == 1:
                c1 = n2
                c2 = n1
            if c1 == 0 and c2 == 0:
                continue
            loc1 = c1
            # add all the expressions & descriptions of this location into the old one
            new_e2[loc1] = G2.nodes[c2]['exprs']
            new_d2[loc1] = G2.nodes[c2]['desc']

            if self.option == 2:
                # add the edges from the incorrect program
                edges2 = list(G2.edges(c2, data=True))
                _, t2, _ = edges2[0]
                _, f2, _ = edges2[1]

                if t2 == 0:
                    t2 = None
                # maps t2 to its new value
                if t2 in match_incorr:
                    t2 = match_incorr[t2]
                else:
                    t2 = None

                if f2 == 0:
                    f2 = None
                # maps f2 to its new value
                if f2 in match_incorr:
                    f2 = match_incorr[f2]
                else:
                    f2 = None
                new_t2[loc1] = {True: t2, False: f2}
            else:
                # add the edges from the correct program to ensure the graphs match
                edges2 = list(G1.edges(loc1, data=True))
                _, t2, _ = edges2[0]
                _, f2, _ = edges2[1]

                if t2 == 0:
                    t2 = None

                if f2 == 0:
                    f2 = None
                new_t2[loc1] = {True: t2, False: f2}

        # this indicates that the correct program is longer so new locations must be added
        # new locations are always empty
        if self.shorter == 2:
            locs = d1.keys()
            extra = sorted(list(set(locs) - set(bestMatch.values())))
            for e in extra:
                new_e2[e] = []
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
        # adds all the expressions into a list so they can be adde to the feedback
        remLocs = list(self.ICF.locexprs.keys() - match_incorr.keys())
        for l in remLocs:
            self.removedLocs[l] = (self.ICF.locexprs[l], self.ICF.locdescs[l])

        # we always start from location 1
        self.ICF.initloc = 1
        self.ICF.locexprs = new_e2
        self.ICF.loctrans = new_t2
        self.ICF.locdescs = new_d2
