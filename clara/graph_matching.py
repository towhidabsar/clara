import networkx as nx
import matplotlib
import matplotlib.pyplot as plt

from clara.model import SPECIAL_VARS, Const, Var

G =nx.DiGraph()


def connect(locs, trans, labels):
    edges = []
    for i, l in enumerate(locs):
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


def getLableValue(exp):
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
        a += getLableValue(arg)
    return [name] + a


def makeLabel(exp):
    label = set()
    for var, e in exp:
        var = str(var)
        if var in SPECIAL_VARS or 'ind#' in var or 'iter#' in var or 'cond' in var:
            label.add(str(var))
        label = label.union(set(getLableValue(e)))
    return label


def makeGraph(fnc):
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
        label = makeLabel(exp)
        label = ','.join(list(label))
        if not label:
            label = 'EMPTY'
        allLabels[l] = label
        
        G.add_node(label, loc=l, desc=d, lno=lno, exprs=exp)


    connect(loc, trans, allLabels)

    for name, attr in list(G.nodes(data=True)):
        print(name)
        
        if len(attr):
            print('loc : ', attr['loc'])
        
        edges = list(G.edges(name, data=True))
        for e in edges:
            _, to, trans = e
            print(trans['weight'],' : ', to)
        print('\n')

    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, font_weight='bold')
    edge_weight = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_weight)
    plt.savefig('1.png')
