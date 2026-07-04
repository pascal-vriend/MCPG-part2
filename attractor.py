from pg import ParityGame
from collections import deque


def compute_attractor(game: ParityGame, player: int, target_set: set) -> tuple[set, dict]:
    """
    Computes the attractor set for a given player and target set of nodes.

    Returns:
        - attractor: set of nodes belonging to the attractor.
        - strategy: dict mapping nodes owned by 'player' inside the attractor
                    to the successor node that keeps them in the attractor.
    """
    attractor = set(target_set)
    strategy = {}
    queue = deque(target_set)

    # Track how many outgoing edges from an opponent's node lead OUT of the attractor.
    # We copy out-degrees for nodes not owned by the target player.
    out_degrees = {}
    for n in game.nodes():
        if game.getOwner(n) != player:
            out_degrees[n] = game.numSuccessors(n)

    while queue:
        curr = queue.popleft()

        for pred in game.getPredecessors(curr):
            if pred in attractor:
                continue

            if game.getOwner(pred) == player:
                # If the player owns the predecessor, they can choose to step into the attractor
                attractor.add(pred)
                strategy[pred] = curr
                queue.append(pred)
            else:
                # If the opponent owns it, they are forced only if ALL successors lead into it
                out_degrees[pred] -= 1
                if out_degrees[pred] == 0:
                    attractor.add(pred)
                    queue.append(pred)

    return attractor, strategy