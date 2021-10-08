import networkx as nx
import matplotlib
import matplotlib.pyplot as plt

G = nx.Graph()

def connect(locs, trans):
    edges = []
    for l in locs:
        t = trans[l]
        true = t[True]
        false = t[False]

        loc = str(l)
        if true:
            edges += [(loc, str(true), True)]
        else:
            edges += [(loc,'None', True)]
        if false:
            edges += [(loc, str(false), False)]
        else:
            edges += [(loc,'None', False)]
    G.add_weighted_edges_from(edges)

def makeGraph(fnc):
    G.add_node('None')
    desc = fnc.locdescs
    trans = fnc.loctrans
    exprs = fnc.locexprs
    loc = list(desc.keys())
    
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
        G.add_node(str(l), desc=d, lno=lno, exprs=exp)

    connect(loc,trans)
    
    pos=nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, font_weight='bold')
    edge_weight = nx.get_edge_attributes(G,'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels = edge_weight)
    plt.savefig('1.png')
