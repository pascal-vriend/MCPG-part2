"""
Implementation-detail variation benchmarks (report Part II, experiments).

Two variations, each measured across several distinct random games from the
stated-seed set in ../games (generated with gameseed 12345):

  1. FPI:  plain "reset-all-lower + restart" (fpi.py) vs the freezing
           refinement (fpi_freezing.py). We report wall-clock time and, for
           each variant, whether the *extracted strategy* is sound (no cycle
           in a player's region whose top priority favours the opponent).

  2. PSI:  strategy improvement initialised with the first successor of every
           node (deterministic) vs random.choice initialisation (the default).
           We report the number of outer/inner improvement steps and time.

Run:  python3 tools/variant_benchmarks.py
"""
import os
import sys
import time
import signal
import random
import contextlib
import io

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pg import read_parity_game
import fpi as fpi_plain
from fpi_freezing import solve_fpi as fpi_freeze
from strategy_improvement import PSISolver

GAMES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "games"))
CAP_SECONDS = 30          # per-solve cap
PSI_SEEDS = [1, 2, 3, 4, 5]
VARIANT_SIZES = [50, 100, 150, 200]
# Defect tally uses only games on which reset-all plain FPI is cheap.
TALLY_MAX_SIZE = 200


class Timeout(Exception):
    pass


@contextlib.contextmanager
def time_limit(seconds):
    def handler(signum, frame):
        raise Timeout()
    signal.signal(signal.SIGALRM, handler)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


# ----------------------------------------------------------------------------
# Strategy-soundness check: does following `strategy` inside `player`'s winning
# region ever close a cycle whose maximum priority has the opponent's parity?
# ----------------------------------------------------------------------------
def strategy_defect(G, winner, strategy, player):
    region = {v for v in G.nodes() if winner[v] == player}
    succ = {}
    for v in region:
        if G.getOwner(v) == player:
            s = strategy.get(v)
            succ[v] = [s] if (s is not None and s in region) else []
        else:
            succ[v] = [u for u in G.getSuccessors(v) if u in region]

    color = {}

    def dfs(u, stack):
        color[u] = 1
        for w in succ[u]:
            if color.get(w, 0) == 1:
                cyc = stack[stack.index(w):]
                mp = max(int(G.getPriority(x)) for x in cyc)
                if mp % 2 != player:
                    return True
            elif color.get(w, 0) == 0:
                if dfs(w, stack + [w]):
                    return True
        color[u] = 2
        return False

    for v in region:
        if color.get(v, 0) == 0 and dfs(v, [v]):
            return True
    return False


def any_defect(G, winner, strategy):
    return strategy_defect(G, winner, strategy, 0) or strategy_defect(G, winner, strategy, 1)


# ----------------------------------------------------------------------------
# PSI with instrumentation and a chosen initialisation
# ----------------------------------------------------------------------------
class CountingPSI(PSISolver):
    def init_first_successor(self):
        for n in self.nodes:
            self.str_map[n] = list(self.game.getSuccessors(n))[0]

    def solve_counted(self):
        outer = inner = 0
        while True:
            while True:
                self.compute_vals_seq()
                if self.switch_strategy_seq(pl=1) == 0:
                    break
                inner += 1
            self.mark_solved_seq()
            outer += 1
            if self.switch_strategy_seq(pl=0) == 0:
                break
        return outer, inner


def run_fpi_plain(G):
    with contextlib.redirect_stdout(io.StringIO()):
        return fpi_plain.fpi(G)


# ----------------------------------------------------------------------------
def load(size):
    return read_parity_game(os.path.join(GAMES_DIR, f"{size}.pg"))


def bench_fpi_variant():
    print("\n=== FPI variant: plain reset-all vs freezing ===")
    print(f"{'size':>5} | {'plain ms':>9} | {'freeze ms':>9} | {'speedup':>7} | "
          f"{'plain defect':>12} | {'freeze defect':>13}")
    print("-" * 78)
    for size in VARIANT_SIZES:
        G = load(size)
        try:
            with time_limit(CAP_SECONDS):
                t = time.perf_counter()
                wp, sp = run_fpi_plain(G)
                tp = (time.perf_counter() - t) * 1000
        except Timeout:
            tp, wp, sp = None, None, None

        t = time.perf_counter()
        wf, sf = fpi_freeze(G)
        tf = (time.perf_counter() - t) * 1000

        dp = any_defect(G, wp, sp) if wp is not None else "n/a"
        df = any_defect(G, wf, sf)
        speed = f"{tp / tf:.1f}x" if tp else "n/a"
        tps = f"{tp:9.1f}" if tp else "  timeout"
        print(f"{size:>5} | {tps} | {tf:9.1f} | {speed:>7} | {str(dp):>12} | {str(df):>13}")


def bench_fpi_defect_tally():
    print("\n=== FPI strategy-defect tally over all games in ../games ===")
    files = sorted(os.listdir(GAMES_DIR), key=lambda f: int(os.path.splitext(f)[0]))
    files = [f for f in files if int(os.path.splitext(f)[0]) <= TALLY_MAX_SIZE]
    plain_bad = freeze_bad = regions_mismatch = total = 0
    for f in files:
        G = read_parity_game(os.path.join(GAMES_DIR, f))
        try:
            with time_limit(CAP_SECONDS):
                wp, sp = run_fpi_plain(G)
        except Timeout:
            continue
        wf, sf = fpi_freeze(G)
        total += 1
        if any(wp[v] != wf[v] for v in wp):
            regions_mismatch += 1
        if any_defect(G, wp, sp):
            plain_bad += 1
        if any_defect(G, wf, sf):
            freeze_bad += 1
    print(f"games checked: {total}")
    print(f"winning-region mismatches (plain vs freeze): {regions_mismatch}")
    print(f"plain  FPI: defective extracted strategy on {plain_bad}/{total} games")
    print(f"freeze FPI: defective extracted strategy on {freeze_bad}/{total} games")


def bench_psi_init():
    print("\n=== PSI variant: deterministic first-successor init vs random init ===")
    print(f"{'size':>5} | {'det outer/inner':>16} | {'det ms':>8} | "
          f"{'rand outer/inner (mean)':>24} | {'rand ms (mean)':>14}")
    print("-" * 86)
    for size in VARIANT_SIZES:
        G = load(size)

        # deterministic init
        try:
            with time_limit(CAP_SECONDS):
                s = CountingPSI(G)
                s.init_first_successor()
                t = time.perf_counter()
                do, di = s.solve_counted()
                dt = (time.perf_counter() - t) * 1000
        except Timeout:
            do = di = dt = None

        # random init, averaged over seeds
        ro = ri = rt = 0.0
        n_ok = 0
        for seed in PSI_SEEDS:
            random.seed(seed)
            try:
                with time_limit(CAP_SECONDS):
                    s = CountingPSI(G)
                    t = time.perf_counter()
                    o, i = s.solve_counted()
                    rt += (time.perf_counter() - t) * 1000
                    ro += o
                    ri += i
                    n_ok += 1
            except Timeout:
                pass
        if n_ok:
            ro, ri, rt = ro / n_ok, ri / n_ok, rt / n_ok
            rand = f"{ro:.1f}/{ri:.1f}"
            rms = f"{rt:14.1f}"
        else:
            rand, rms = "timeout", "       timeout"

        det = f"{do}/{di}" if do is not None else "timeout"
        dms = f"{dt:8.1f}" if dt is not None else " timeout"
        print(f"{size:>5} | {det:>16} | {dms} | {rand:>24} | {rms}")


if __name__ == "__main__":
    print("Games dir:", GAMES_DIR)
    bench_fpi_variant()
    bench_psi_init()
    bench_fpi_defect_tally()
