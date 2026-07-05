import sys
from pg import ParityGame, acquire_parity_game, write_solution


class SPMSolver:
    def __init__(self, game: ParityGame):
        self.game = game
        self.nodes = list(game.nodes())

    def _run_spm(self, shift=0):
        """
        Runs the Small Progress Measures algorithm.
        shift=0: Solves for Player 0 (Even) minimizing the measure.
        shift=1: Solves for Player 1 (Odd). By adding 1 to all priorities,
                 we invert the parity of the graph, allowing us to use the
                 exact same logic to extract Odd's winning strategy.
        """
        # Determine k based on the shifted priorities
        k = max((self.game.getPriority(n) + shift for n in self.nodes), default=-1) + 1

        # Calculate maximum limits n_i for each odd priority
        limits = [0] * k
        for n in self.nodes:
            p = self.game.getPriority(n) + shift
            if p % 2 == 1:
                limits[p] += 1

        # Measure array (None represents Top)
        measure = {n: [0] * k for n in self.nodes}

        def is_top(m):
            return m is None

        def cmp(m1, m2):
            """Lexicographical comparison (highest priority index dominates)."""
            if m1 is None and m2 is None: return 0
            if m1 is None: return 1
            if m2 is None: return -1
            for i in range(k - 1, -1, -1):
                if m1[i] != m2[i]:
                    return 1 if m1[i] > m2[i] else -1
            return 0

        def prog(m_w, p_v):
            """The SPM progression function (Truncate, Increment, Carry)."""
            if is_top(m_w):
                return None

            t = list(m_w)

            # 1. Truncate lower priorities
            for i in range(p_v):
                t[i] = 0

            if p_v % 2 == 0:
                return t

            # 2. Increment and Carry for odd priorities
            t[p_v] += 1
            for i in range(p_v, k):
                if i % 2 == 1 and t[i] > limits[i]:
                    t[i] = 0  # Reset
                    # Carry over to the next highest odd priority
                    next_odd = i + 2
                    if next_odd < k:
                        t[next_odd] += 1
                    else:
                        return None  # Overflow to Top
            return t

        # Main SPM fixed-point iteration
        changed = True
        while changed:
            changed = False
            for n in self.nodes:
                if is_top(measure[n]):
                    continue

                p_v = self.game.getPriority(n) + shift
                owner = self.game.getOwner(n)

                # The minimizer wants to avoid Top. The maximizer wants to push to Top.
                is_minimizer = (owner == 0 and shift == 0) or (owner == 1 and shift == 1)

                succs = list(self.game.getSuccessors(n))
                best_m = prog(measure[succs[0]], p_v)

                for w in succs[1:]:
                    m_val = prog(measure[w], p_v)
                    if is_minimizer:
                        if cmp(m_val, best_m) < 0:
                            best_m = m_val
                    else:
                        if cmp(m_val, best_m) > 0:
                            best_m = m_val

                # Strict monotonic increase: Lift(v)
                if cmp(best_m, measure[n]) > 0:
                    measure[n] = best_m
                    changed = True

        # Extract the winning set and strategy for the minimizing player
        W_minimizer = set()
        strategy = {}

        for n in self.nodes:
            if not is_top(measure[n]):
                W_minimizer.add(n)
                owner = self.game.getOwner(n)
                is_minimizer = (owner == 0 and shift == 0) or (owner == 1 and shift == 1)

                if is_minimizer:
                    p_v = self.game.getPriority(n) + shift
                    best_w = None
                    best_val = None

                    succs = list(self.game.getSuccessors(n))
                    for w in succs:
                        m_val = prog(measure[w], p_v)
                        # Find the successor that strictly minimizes the measure
                        if best_val is None or cmp(m_val, best_val) < 0:
                            best_val = m_val
                            best_w = w
                    strategy[n] = best_w

        return W_minimizer, strategy

    def solve(self):
        """
        Runs SPM symmetrically to trivially extract both sets of winning strategies.
        """
        # 1. Run standard SPM to get Even's winning set and strategies
        W0, strat0 = self._run_spm(shift=0)

        # 2. Run dual SPM to extract Odd's winning set and strategies
        W1, strat1 = self._run_spm(shift=1)

        winner = {}
        strategy = {}

        for n in self.nodes:
            if n in W0:
                winner[n] = 0
                if self.game.getOwner(n) == 0 and n in strat0:
                    strategy[n] = strat0[n]
            else:
                winner[n] = 1
                if self.game.getOwner(n) == 1 and n in strat1:
                    strategy[n] = strat1[n]

        return winner, strategy


if __name__ == "__main__":
    G = acquire_parity_game()

    solver = SPMSolver(G)
    winner, strategy = solver.solve()

    output_file = sys.argv[2]
    with open(output_file, "w") as f_out:
        f_out.write(write_solution(winner, strategy))