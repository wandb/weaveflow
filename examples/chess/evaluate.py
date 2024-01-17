import weave
import asyncio
from weave.weaveflow import evaluate

import player_random
import player_llm

import project_settings


@weave.op()
def score_move(example, prediction):
    scores = {ms["move"]: ms["score"] for ms in example["moves_scores"]}
    min_score = min(scores.values())
    max_score = max(scores.values())
    range_scores = max_score - min_score
    normalized_scores = {
        move: (score - min_score) / range_scores for move, score in scores.items()
    }

    scores = {}

    ai_score = scores.get(prediction, min_score - 1)
    normalized_ai_score = normalized_scores.get(prediction, -0.3)
    return {
        "ai_score": ai_score,
        "normalized_ai_score": normalized_ai_score,
    }


if __name__ == "__main__":
    # model = player_random.RandomPlayer()
    system_message = """You are a the most advanced chess AI ever created.
You always think out loud through large trees of moves using SAN notation, before deciding on a final move.
"""
    model = player_llm.LLMPlayer(2, system_message, "gpt-3.5-turbo")

    weave.init(project_settings.project_name)

    dataset = weave.ref("dataset-10").get()

    @weave.op()
    def example_to_model_input(example):
        return example["position"]

    evaluation = evaluate.Evaluation(
        dataset, scores=[score_move], example_to_model_input=example_to_model_input
    )
    print(asyncio.run(evaluation.evaluate(model)))
