import sys
from pg import acquire_parity_game, write_solution


def fpi(game):
    n = game.numNodes()
    d = game.maxPriority()

    # --------------------------------------------------
    # Precompute everything once
    # --------------------------------------------------

    priority = game.priority
    owner = game.owner

    successors = [tuple(game.getSuccessors(v)) for v in range(n)]

    parity = [int(priority[v] & 1) for v in range(n)]

    priority_nodes = [[] for _ in range(d + 1)]
    for v in range(n):
        priority_nodes[priority[v]].append(v)

    # Oink's distraction bitset
    distraction = [False] * n

    # Strategy chosen during one-step evaluation
    strategy = [-1] * n

    # --------------------------------------------------
    # Main FPI loop
    # --------------------------------------------------

    p = 0
    iterations = 0

    while p <= d:

        iterations += 1
        changed = False

        for v in priority_nodes[p]:

            # Already a distraction
            if distraction[v]:
                continue

            if owner[v] == 0:

                onestep_winner = 1

                for u in successors[v]:
                    if (parity[u] ^ distraction[u]) == 0:
                        onestep_winner = 0
                        strategy[v] = u
                        break

            else:

                onestep_winner = 0

                for u in successors[v]:
                    if (parity[u] ^ distraction[u]) == 1:
                        onestep_winner = 1
                        strategy[v] = u
                        break

            if onestep_winner != parity[v]:
                distraction[v] = True
                changed = True

        if changed:

            # Reset all lower priorities
            for q in range(p):
                for v in priority_nodes[q]:
                    distraction[v] = False

            p = 0

        else:
            p += 1

    print(f"FPI iterations: {iterations}")

    # --------------------------------------------------
    # Construct winners
    # --------------------------------------------------

    winner = {}

    for v in range(n):
        winner[v] = parity[v] ^ distraction[v]

    # --------------------------------------------------
    # Construct strategy
    # --------------------------------------------------

    final_strategy = {}

    for v in range(n):

        winning_player = winner[v]

        if owner[v] != winning_player:
            continue

        chosen = None

        for u in successors[v]:
            if winner[u] == winning_player:
                chosen = u
                break

        if chosen is not None:
            final_strategy[v] = chosen
        elif strategy[v] != -1:
            final_strategy[v] = strategy[v]

    return winner, final_strategy


if __name__ == "__main__":

    G = acquire_parity_game()

    winner_dict, strategy_dict = fpi(G)

    output_file = sys.argv[2]

    with open(output_file, "w") as f:
        f.write(write_solution(winner_dict, strategy_dict))