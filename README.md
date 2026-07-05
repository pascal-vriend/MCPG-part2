# Part 2

This directory contains four parity game solvers, each implemented as a standalone
script. Every solver reads a parity game in **PGSolver format** and writes a
solution (winning regions + strategies) back out, so they can be plugged directly
into the [Oink](https://github.com/trolando/oink) `test_solvers` harness as
external solvers for correctness and performance comparison.

All solvers share the same interface:

```bash
python3 <solver>.py <input.pg> <output.sol>
```

- `<input.pg>` — a parity game in PGSolver format (also accepted on `stdin`).
- `<output.sol>` — file to write the solution to, in `paritysol` format.

The shared building blocks are:

- `pg.py` — the `ParityGame` class, the PGSolver parser, and the solution writer.
- `attractor.py` — attractor-set computation used by Zielonka's algorithm.

---

## Solver 1 – Fixpoint Iteration (FPI)

Run:

```bash
python3 fpi.py games/100.pg out.sol
```

Distraction-based fixpoint iteration, following Oink's FPI formulation. The plain
version (`fpi.py`) restarts from priority `0` whenever a distraction is found.
It computes the **correct winning regions**, but Oink rejects it with a "loser can
win" error: its strategy *extraction* picks the first successor that stays in the
winning region, which can close a cycle whose top priority favours the opponent.
The freezing version keeps the move recorded during one-step evaluation instead and
is the correct one (see the report, Part II, "Variant 1" for the full diagnosis).

A tuned variant is provided in `fpi_freezing.py`, which adds **freezing/thawing**
of lower priorities and skips empty priority levels. This is the version used for
benchmarking, since it is significantly faster:

```bash
python3 fpi_freezing.py games/100.pg out.sol
```

---

## Solver 2 – Zielonka's Recursive Algorithm

Run:

```bash
python3 zielonka.py games/100.pg out.sol
```

The classic recursive attractor-decomposition algorithm. It repeatedly removes the
attractor towards the highest-priority vertices (via `attractor.py`) and recurses
on the remaining subgame, combining the winning regions and strategies of both
players.

---

## Solver 3 – Small Progress Measures (SPM)

Run:

```bash
python3 spm.py games/100.pg out.sol
```

Lifts progress measures to a fixed point to determine the winning region of the
minimizing player. The algorithm is run **symmetrically**: once on the original
game for Player 0 (Even), and once on the priority-shifted game for Player 1 (Odd),
so that both players' winning sets and strategies are extracted from the same core
routine.

---

## Solver 4 – Strategy Improvement (PSI)

Run:

```bash
python3 strategy_improvement.py games/100.pg out.sol
```

Discrete strategy improvement. Player 0's strategy is fixed while Player 1
optimises against it (inner loop); Even-won cycles are then marked, and Player 0
improves its strategy and halting set (outer loop). The two loops alternate until
no improving switch remains.

> Note: strategies are initialised **randomly**, so the number of improvement
> iterations may vary between runs, but the computed winner is always the same.

---

## Running against Oink

The solvers are designed to be validated against Oink's built-in solvers. Assuming /oink and /part2 live in a shared folder, from the
Oink `build/` directory, register a script as an external solver with `%I` / `%O`
standing for the input and output files:

```bash
# Check correctness of all four solvers on 5 random games of size 15
./test_solvers \
  --fpi --zlk --psi \
  --size 15 --count 5 \
  --external "fpi_freezing:python3 ../../part2/fpi_freezing.py %I %O" \
  --external "zielonka:python3 ../../part2/zielonka.py %I %O" \
  --external "strat_improv:python3 ../../part2/strategy_improvement.py %I %O"
```

You can also run a single solver against a directory of test games:

```bash
./test_solvers --spm ../tests --external "spm_ext:python3 ../../part2/spm.py %I %O"
```

---

## Tools

The `tools/` directory contains helpers for generating benchmarks and plotting
performance:

| File | Description |
|------|-------------|
| `generate_games.sh` | Generates 50 random parity games, sizes linearly interpolated from 10 to 500, into `games/`, using Oink's game generator. |
| `plot_random_games_external.py` | Benchmarks the pure-Python FPI-freezing and Zielonka solvers over every game in `games/` and saves `random_games_comparison.png`. |
| `plot_random_games_oink.py` | Runs Oink's own `fpi`, `spm`, and `zlk` solvers over `games/` and plots their timings as `random_games_comparison_oink.png`. |
| `variant_benchmarks.py` | Implementation-detail experiments: basic vs freezing FPI (time + strategy-soundness check) and PSI deterministic vs random initialisation (iteration counts). |

Generate the benchmark set with:

```bash
cd tools
./generate_games.sh
```
