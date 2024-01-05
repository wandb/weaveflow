import weave
import math
import asyncio

import player_random
import player_llm
from typing import AsyncIterator, Callable, Iterable, Tuple, TypeVar, Awaitable

import project_settings

T = TypeVar("T")
U = TypeVar("U")


async def async_map(
    sequence: Iterable[T],
    func: Callable[[T], Awaitable[U]],
    max_concurrent_tasks: int,
) -> AsyncIterator[Tuple[T, U]]:
    semaphore = asyncio.Semaphore(max_concurrent_tasks)

    async def process_item(item: T) -> Tuple[T, U]:
        async with semaphore:
            result = await func(item)
            return item, result

    tasks = [asyncio.create_task(process_item(item)) for item in sequence]

    for task in asyncio.as_completed(tasks):
        item, result = await task
        yield item, result


@weave.op()
async def move_and_score(example, model):
    position = example["position"]
    move = await model.move(position)

    scores = {ms["move"]: ms["score"] for ms in example["moves_scores"]}
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
    return eval_row


@weave.op()
async def eval_moves(dataset, model):
    async def eval_example(example):
        return await move_and_score(example, model)

    eval_rows = []
    async for example, eval_row in async_map(dataset.rows, eval_example, 100):
        eval_rows.append(eval_row)

    eval_table = weave.WeaveList(eval_rows)

    return {
        "weighted_norm_score/avg": sum(eval_table.column("weighted_norm_score"))
        / len(eval_table)
    }


if __name__ == "__main__":
    model = player_random.RandomPlayer()
    system_message = """You are a fourth grader.
You always think out loud through large trees of moves using SAN notation, before deciding on a final move.
"""
    # model = player_llm.LLMPlayer(1, system_message, "gpt-3.5-turbo")

    weave.init(project_settings.project_name)

    dataset = weave.ref("dataset-10").get()

    asyncio.run(eval_moves(dataset, model))
