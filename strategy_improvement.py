import sys
import random
from pg import ParityGame, acquire_parity_game, write_solution


class PSISolver:
    def __init__(self, game: ParityGame):
        self.game = game
        self.nodes = list(game.nodes())

        # Determine k as highest priority + 1
        self.k = max((game.getPriority(n) for n in self.nodes), default=-1) + 1

        # State arrays
        self.val = {n: [0] * self.k for n in self.nodes}
        self.str_map = {}
        self.halt = {n: True for n in self.nodes}
        self.done = {n: 0 for n in self.nodes}  # 0=unvisited, 1=visited, 2=cycle, 3=won
        self.won = {n: False for n in self.nodes}

        # Initialize with random strategies to prove the SI algorithm works
        for n in self.nodes:
            successors = list(game.getSuccessors(n))
            self.str_map[n] = random.choice(successors)

    def si_val_less(self, a, b):
        """
        Returns True if the strategy valuation of node 'a' is strictly LESS
        than node 'b' from the perspective of Player 0 (Even).
        """
        if a == b:
            return False

        a_won_or_cycle = (a != -1) and (self.won[a] or self.done[a] == 2)
        b_won_or_cycle = (b != -1) and (self.won[b] or self.done[b] == 2)

        # Infinity checks (cycles / won nodes are treated as +inf for Even)
        if a_won_or_cycle:
            return False  # a is inf, so a >= b
        if b_won_or_cycle:
            return True  # b is inf, a is not, so a < b

        val_a = self.val[a] if a != -1 else [0] * self.k
        val_b = self.val[b] if b != -1 else [0] * self.k

        # Lexicographical comparison (highest priority first)
        for i in range(self.k - 1, -1, -1):
            if val_a[i] == val_b[i]:
                continue
            if i % 2 == 1:
                # Odd priority: Even player prefers lower counts
                return val_a[i] > val_b[i]
            else:
                # Even priority: Even player prefers higher counts
                return val_a[i] < val_b[i]

        return False

    def compute_vals_seq(self):
        """
        Backward propagation to update valuations in O(|V| + |E|) time.
        """
        rev_str = {n: [] for n in self.nodes}
        q = []

        for n in self.nodes:
            if self.done[n] == 3:
                continue  # Skip nodes already won

            s = self.str_map[n]
            if s == -1 or self.halt[s]:
                q.append(n)
            else:
                rev_str[s].append(n)
                if self.done[n] != 2:
                    self.done[n] = 2  # Assume on cycle initially

        while q:
            v = q.pop()
            s = self.str_map[v]

            # Base valuation from successor (or 0-tuple if halted)
            if s == -1 or self.halt[s]:
                self.val[v] = [0] * self.k
            else:
                self.val[v] = list(self.val[s])

            # Add vertex's own priority weight
            self.val[v][self.game.getPriority(v)] += 1
            self.done[v] = 1  # Mark as processed (not a cycle)

            # Push backward
            for from_node in rev_str.get(v, []):
                q.append(from_node)

    def mark_solved_seq(self):
        """
        Because Odd actively avoids cycles, any remaining cycle is forced by Even.
        Mark these Even cycles as won.
        """
        res = 0
        for n in self.nodes:
            if self.done[n] == 2:
                self.won[n] = True
                self.done[n] = 3
                res += 1
        return res

    def switch_strategy_seq(self, pl):
        """
        Evaluates successors and updates strategies for player `pl`.
        Also updates the halting set if evaluating for Even (pl == 0).
        """
        res = 0
        for n in self.nodes:
            if self.done[n] == 3:
                continue
            if self.game.getOwner(n) != pl:
                continue

            changed = False
            cur_strat = self.str_map[n]
            best_strat = cur_strat

            for to in self.game.getSuccessors(n):
                if to == best_strat:
                    continue

                # If target is in halting set, treat its valuation as sink (-1)
                cur_target = -1 if self.halt[best_strat] else best_strat
                new_target = -1 if self.halt[to] else to

                if pl == 0:
                    # Player 0 (Even) wants to MAXIMIZE
                    if self.si_val_less(cur_target, new_target):
                        best_strat = to
                        changed = True
                else:
                    # Player 1 (Odd) wants to MINIMIZE
                    if self.si_val_less(new_target, cur_target):
                        best_strat = to
                        changed = True

            if changed:
                self.str_map[n] = best_strat
                res += 1

        # Check if Player 0 wants to stop halting at any nodes
        if pl == 0:
            for n in self.nodes:
                if self.halt[n] and self.si_val_less(-1, n):
                    self.halt[n] = False
                    res += 1

        return res

    def solve(self):
        """
        The main Strategy Improvement execution loop.
        """
        while True:
            # Inner Loop: Player 1 (Odd) optimizes against Player 0
            while True:
                self.compute_vals_seq()
                count = self.switch_strategy_seq(pl=1)
                if count == 0:
                    break

            # Mark Even-won cycles
            self.mark_solved_seq()

            # Outer Loop: Player 0 (Even) updates strategy & halting set
            count = self.switch_strategy_seq(pl=0)
            if count == 0:
                break

        # Extract winner and strategies
        winner = {}
        final_strat = {}

        for n in self.nodes:
            win_player = 0 if self.won[n] else 1
            winner[n] = win_player
            # Only record strategy if the node belongs to the winning player
            if self.game.getOwner(n) == win_player:
                final_strat[n] = self.str_map[n]

        return winner, final_strat


if __name__ == "__main__":
    G = acquire_parity_game()

    # Initialize and run the Strategy Improvement Solver natively
    solver = PSISolver(G)
    winner, strategy = solver.solve()

    # Write the refined total strategy profile back to output
    output_file = sys.argv[2]
    with open(output_file, "w") as f_out:
        f_out.write(write_solution(winner, strategy))