import weave
import math

import player_random
import player_llm


@weave.op()
def eval_moves(dataset, model):
    eval_rows = []
    for example in dataset.rows:
        position = example["position"]
        move = model.move(position)

        # TODO: have to filter none because weavelist adds them
        scores = {
            move: score
            for move, score in example["moves_scores"].items()
            if score is not None
        }
        min_score = min(scores.values())
        max_score = max(scores.values())
        range_scores = max_score - min_score
        normalized_scores = {
            move: (score - min_score) / range_scores for move, score in scores.items()
        }

        eval_row = {}

        ai_score = scores.get(move, min_score - 1)
        normalized_ai_score = normalized_scores.get(
            move, -0.3
        )  # Default to -0.3 if move not in dataset

        eval_row["raw_score"] = ai_score
        eval_row["norm_score"] = normalized_ai_score

        weighted_norm_score = math.sqrt(1 - normalized_ai_score)
        eval_row["weighted_norm_score"] = weighted_norm_score

        eval_rows.append(eval_row)

    eval_table = weave.WeaveList(eval_rows)

    return {
        "summary": {
            "weighted_norm_score/avg": sum(eval_table.column("weighted_norm_score"))
            / len(eval_table)
        },
        "eval_results": eval_table,
    }


if __name__ == "__main__":
    # model = player_random.RandomPlayer()
    system_message = """You are the most advanced chess AI ever created.
You always think out loud through large trees of moves using SAN notation, before deciding on a final move.
"""
    model = player_llm.LLMPlayer(1, system_message, "gpt-3.5-turbo")

    weave.init("wf-chess2")

    dataset = weave.ref("dataset-10").get()

    ex0 = dataset.rows[0]
    position = ex0["position"]
    print(model.move(position))

    eval_moves(dataset, model)
