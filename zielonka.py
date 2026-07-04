import sys

from attractor import compute_attractor
from pg import ParityGame, acquire_parity_game, write_solution


def solve_zielonka(game: ParityGame) -> tuple[dict, dict]:
    # Base case: empty game
    if game.numNodes() == 0:
        return {}, {}

    highest_priority = game.maxPriority()
    current_player = highest_priority % 2
    opponent = 1 - current_player

    highest_priority_vertices = set(game.nodesWithPriority(highest_priority))

    # Attractor towards the highest-priority vertices
    current_player_attractor, current_player_attractor_strategy = (compute_attractor(game, current_player, highest_priority_vertices))

    # Solve the remaining game
    remaining_game = game.withoutNodes(current_player_attractor)
    remaining_winners, remaining_strategy = solve_zielonka(remaining_game)

    # Which vertices does the opponent win in the remaining game?
    opponent_winning_region = {vertex for vertex, winner in remaining_winners.items() if winner == opponent}

    # Case 1:
    # Opponent wins nothing after removing the attractor.
    if not opponent_winning_region:
        winner = {vertex: current_player for vertex in current_player_attractor}
        strategy = dict(current_player_attractor_strategy)

        winner.update(remaining_winners)
        strategy.update(remaining_strategy)

    # Case 2:
    # Opponent wins something and can attract more vertices.
    else:
        opponent_attractor, opponent_attractor_strategy = (compute_attractor(game, opponent, opponent_winning_region))
        reduced_game = game.withoutNodes(opponent_attractor)

        reduced_winners, reduced_strategy = solve_zielonka(reduced_game)

        winner = {vertex: opponent for vertex in opponent_attractor}

        strategy = dict(opponent_attractor_strategy)

        # Preserve strategies from the first recursive call
        for vertex in opponent_winning_region:
            if vertex in remaining_strategy:
                strategy[vertex] = remaining_strategy[vertex]

        winner.update(reduced_winners)
        strategy.update(reduced_strategy)

    # Assign strategies for winning vertices that still don't have one
    for vertex, winning_player in winner.items():
        if game.getOwner(vertex) == winning_player and vertex not in strategy:
            valid_successors = [successor for successor in game.getSuccessors(vertex) if winner.get(successor) == winning_player]

            if valid_successors:
                strategy[vertex] = valid_successors[0]

    return winner, strategy


if __name__ == "__main__":
    G = acquire_parity_game()
    winner, strategy = solve_zielonka(G)

    final_strat = {}
    for n in winner.keys():
        # A strategy is only required/written if the winner matches the node owner
        if G.getOwner(n) == winner[n]:
            if n in strategy:
                final_strat[n] = strategy[n]
            else:
                player_winning_region = winner[n]
                valid_successors = [
                    succ for succ in G.getSuccessors(n)
                    if winner.get(succ) == player_winning_region
                ]

                if valid_successors:
                    final_strat[n] = valid_successors[0]
                else:
                    # Absolute fallback if no internal moves exist (should be dead code)
                    final_strat[n] = next(iter(G.getSuccessors(n)))

    output_file = sys.argv[2]
    with open(output_file, "w") as f:
        f.write(write_solution(winner, final_strat))