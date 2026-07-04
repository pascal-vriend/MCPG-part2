import sys
from pg import acquire_parity_game, write_solution


def solve_fpi(game):
    n = game.numNodes()
    d = game.maxPriority()

    # 1. STRIP NUMPY OVERHEAD: Convert arrays to pure Python lists
    priority = game.priority.tolist()
    owner = game.owner.tolist()

    # Pre-fetch successors as tuples for speed
    successors = [tuple(game.getSuccessors(v)) for v in range(n)]
    parity = [priority[v] & 1 for v in range(n)]

    # Group nodes by priority
    priority_nodes = [[] for _ in range(d + 1)]
    for v in range(n):
        priority_nodes[priority[v]].append(v)

    # Flattened order array and start indices
    order = []
    p_start = [0] * (d + 1)
    for p in range(d + 1):
        p_start[p] = len(order)
        order.extend(priority_nodes[p])

    # 2. JUMP SPARSE PRIORITIES: Precompute the next active priority in O(1)
    next_active = [d + 1] * (d + 1)
    last = d + 1
    for p in range(d, -1, -1):
        next_active[p] = last
        if priority_nodes[p]:
            last = p

    # 3. PURE LISTS: bytearray has conversion overhead; lists are faster here
    distraction = [0] * n
    frozen = [0] * n
    strategy = [-1] * n

    p = 0

    while p <= d:
        if not priority_nodes[p]:
            p = next_active[p]
            continue

        # --------------------------------------------------
        # INLINED: update_block
        # --------------------------------------------------
        changed = 0
        for v in priority_nodes[p]:
            if frozen[v] or distraction[v]:
                continue

            ow = owner[v]
            par_v = parity[v]

            if ow == 0:
                onestep_winner = 1
                for u in successors[v]:
                    if parity[u] == distraction[u]:
                        onestep_winner = 0
                        strategy[v] = u
                        break
            else:
                onestep_winner = 0
                for u in successors[v]:
                    if parity[u] != distraction[u]:
                        onestep_winner = 1
                        strategy[v] = u
                        break

            if par_v != onestep_winner:
                distraction[v] = 1
                changed += 1
        # --------------------------------------------------

        if changed == 0:
            p = next_active[p]
            continue

        if p != 0:
            # --------------------------------------------------
            # INLINED: freeze_thaw_reset
            # --------------------------------------------------
            pl = p & 1
            for i in range(p_start[p]):
                v = order[i]
                f = frozen[v]

                if f >= p:
                    continue

                if f:
                    if (f & 1) == pl:
                        frozen[v] = p
                    else:
                        frozen[v] = 0
                        distraction[v] = 0
                elif distraction[v]:
                    if parity[v] == pl:
                        frozen[v] = p
                    else:
                        distraction[v] = 0
                elif parity[v] != pl:
                    frozen[v] = p
            # --------------------------------------------------
            p = 0


    # --------------------------------------------------
    # Strategy extraction
    # --------------------------------------------------
    winner = [parity[v] ^ distraction[v] for v in range(n)]
    final_strategy = {}

    for v in range(n):
        if owner[v] == winner[v]:
            if strategy[v] != -1:
                final_strategy[v] = strategy[v]

    winner_dict = {v: winner[v] for v in range(n)}
    return winner_dict, final_strategy


if __name__ == "__main__":
    G = acquire_parity_game()
    winner_dict, strategy_dict = solve_fpi(G)

    output_file = sys.argv[2]
    with open(output_file, "w") as f:
        f.write(write_solution(winner_dict, strategy_dict))