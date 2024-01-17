import pandas as pd
import random
import chess
import chess.engine
import tqdm
import weave
from weave import weaveflow


import project_settings


def generate_random_chess_dataset(large_dataset_path, small_dataset_size=25):
    engine = chess.engine.SimpleEngine.popen_uci("stockfish")
    engine.configure({"Threads": 8, "Hash": 16000})

    # Load the large dataset
    df = pd.read_csv(large_dataset_path)

    small_dataset = []

    for i in tqdm.tqdm(range(small_dataset_size)):
        while True:
            row = df.sample(n=1).iloc[0]
            moves = row["moves"].split(" ")
            # Choose a random turn within the game, dropping the last 2 moves
            if len(moves) >= 10:
                break
        turn_index = random.randint(0, len(moves) - 3)

        board = chess.Board()
        for move in moves[: turn_index + 1]:
            try:
                board.push_san(move)
            except ValueError:
                break  # Invalid move found, skip to next game

        # Find top N moves, but with limited time search instead of depth
        # Note, multipv reduces quality of best move found
        info = engine.analyse(board, chess.engine.Limit(time=5), multipv=20)

        # Prepare moves and their scores
        moves_scores = []
        for item in info:
            move = item.get("pv")[0]
            score = item.get("score").relative.score(mate_score=100000)
            moves_scores.append({"move": move.uci(), "score": score})

        # Add to the small dataset
        small_dataset.append(
            {
                "game_id": row["id"],
                "position": board.fen(),
                "turn": turn_index + 1,
                "moves_scores": moves_scores,
            }
        )

    engine.quit()
    return small_dataset


if __name__ == "__main__":
    dataset = generate_random_chess_dataset("games.csv", small_dataset_size=25)
    weave.init(project_settings.project_name)
    weave.publish(weaveflow.Dataset(dataset), "dataset-10")
