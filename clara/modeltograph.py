'''
Converts Program model to a image (graph)
'''

import pygraphviz as pgv


def stmts_to_str(title, types, ss):
    l = [title]
    if types:
        l.append(', '.join(map(lambda x: '%s: %s' % x, types)))
    for (v, e) in ss:
        ls = str(e)
        ls = ls.replace(r'\n', r'\\n')
        ls = ls.replace(r'\r', r'\\r')
        ls = ls.replace(r'\t', r'\\t')
        l.append('%s := %s' % (v, ls))

    ml = max(map(lambda x: len(x), l))
    l.insert(2 if types else 1, '-' * ml)

    return '\n'.join(l)


def create_graph(pm):
    G = pgv.AGraph(directed=True)
    
    for name, fnc in pm.fncs.items():

        fnclab = 'fun %s (%s) : %s --- ' % (
            fnc.name,
            ', '.join(map(lambda x: '%s : %s' % x, fnc.params)),
            fnc.rettype)
        types = fnc.types.items()
        
        for loc in fnc.locs():
            fnclabel = fnclab if loc == fnc.initloc else ''
            label = stmts_to_str('%sL%s' % (fnclabel, loc,), types,
                                 fnc.exprs(loc))
            types = None

            G.add_node('%s-%s' % (name, loc), label=label, shape='rectangle',
                       fontname='monospace')

        for loc in fnc.locs():
            locs = '%s-%s' % (name, loc)
            
            loc2 = fnc.trans(loc, True)
            locs2 = '%s-%s' % (name, loc2)
            if loc2:
                G.add_edge(locs, locs2, label='True')

            loc2 = fnc.trans(loc, False)
            locs2 = '%s-%s' % (name, loc2)
            if loc2:
                G.add_edge(locs, locs2, label='False')

    G.layout('dot')

    return G
