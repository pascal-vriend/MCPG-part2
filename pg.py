import networkx as nx
import numpy as np
import re
import sys

class ParityGame(object):
    def __init__(self, nodecountOrParityGame, graph=None):
        if type(nodecountOrParityGame) == int:
            nodecount = nodecountOrParityGame
            self.graph = nx.empty_graph(nodecount, None, nx.DiGraph)
            self.owner = np.zeros(nodecount, dtype=np.int8)
            self.priority = np.zeros(nodecount, dtype=np.int32)
            self.label = np.zeros(nodecount, dtype=np.object_)
        else:
            originalPG = nodecountOrParityGame
            self.graph = nx.DiGraph(graph)
            self.owner = originalPG.owner.copy()
            self.priority = originalPG.priority.copy()
            self.label = originalPG.label.copy()

    def set_node(self, node, owner, priority, label):
        self.owner[node] = owner
        self.priority[node] = priority
        self.label[node] = label

    def add_edge(self, src, tgt):
        self.graph.add_edge(src, tgt)

    def priorities(self):
        return self.priority.copy()

    def maxPriority(self):
        return max(self.priority[n] for n in self.graph.nodes())

    def nodesWithPriority(self, p):
        return [n for n in self.graph.nodes() if self.priority[n] == p]

    def numNodes(self):
        return len(self.graph)

    def nodes(self):
        return self.graph.nodes()

    def edges(self):
        return [e for e in self.graph.edges]

    def getOwner(self, n):
        return self.owner[n]

    def getPriority(self, n):
        try:
            return [self.priority[nPrime] for nPrime in n]
        except TypeError:
            return self.priority[n]

    def hasEdge(self, u, v):
        return self.graph.has_edge(u, v)

    def withoutNodes(self, U):
        V = [n for n in self.graph.nodes() if n not in U]
        return self.withNodes(V)

    def withNodes(self, U):
        graph = self.graph.subgraph(U)
        return ParityGame(self, graph)

    def getSuccessors(self, n):
        try:
            return [item for sublist in [self.graph.successors(nPrime) for nPrime in n]
                         for item in sublist]
        except TypeError:
            return self.graph.successors(n)

    def getPredecessors(self, n):
        """Returns the predecessors of node n in the current (sub)game."""
        return self.graph.predecessors(n)

    def numSuccessors(self, n):
        return self.graph.out_degree(n)

    def invert(self):
        H = self.withNodes(self.nodes())
        for i in range(len(H.priority)):
            H.priority[i] += 1
        for i in range(len(H.owner)):
            H.owner[i] = (H.owner[i] + 1) % 2
        return H


def read_parity_game(path, verbose=False):
    try:
        with open(path, 'r') as f:
            txt = f.read()
    except Exception:
        txt = path

    f = (s for s in txt.split("\n"))

    m = re.match(r'parity\W+(\d+)', next(f))
    assert m, "File must start with: parity <max_id>;"

    g = ParityGame(int(m.group(1)))

    patt = re.compile(r'(\d+)\W+(\d+)\W+(\d+)\W+((?:\d+[, ]*)+)(.*);')

    for line in f:
        m = re.match(patt, line)
        if m:
            node     = int(m.group(1))
            priority = int(m.group(2))
            owner    = int(m.group(3))
            succ     = map(int, re.findall(r'\d+', m.group(4)))
            label    = m.group(5).strip().strip('"')
            g.set_node(node, owner, priority, label)
            for tgt in succ:
                g.add_edge(node, tgt)
        elif verbose:
            print("bad line: " + line)

    return g


def acquire_parity_game():
    if len(sys.argv) > 1:
        G = read_parity_game(sys.argv[1])
    else:
        G = read_parity_game(sys.stdin.read())
    return G


# -----------------------------------------------------------------------
# Solution writer
# -----------------------------------------------------------------------

def write_solution(winner: dict, strategy: dict, out=None) -> str:
    """
    Serialise a solution to PGSolver output format.

    winner[v]   = 0 or 1  (winning player for node v)
    strategy[v] = chosen successor for v (only needed where owner == winner;
                  can be omitted / None for other nodes)
    out         = file path to write to, or None for stdout only

    Returns the formatted string.
    """
    if not winner:
        return "paritysol 0;\n"

    max_id = max(winner.keys())
    lines = [f"paritysol {max_id};"]

    for v in sorted(winner.keys()):
        w = winner[v]
        s = strategy.get(v)
        if s is not None:
            lines.append(f"{v} {w} {s};")
        else:
            lines.append(f"{v} {w};")

    text = "\n".join(lines) + "\n"

    if out is not None:
        with open(out, "w") as fh:
            fh.write(text)

    return text