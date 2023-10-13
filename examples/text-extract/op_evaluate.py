import dataclasses
import weave
import typing
import time
import base_types

import pandas as pd

from weave import ops_arrow

import cli


def p_r_f1(tp: int, fp: int, fn: int) -> typing.Tuple[float, float, float]:
    # if any denom is zero, then zero. could use NaN instead...
    precision = 0
    if tp or fp:
        precision = tp / (tp + fp)
    recall = 0
    if tp or fn:
        recall = tp / (tp + fn)
    f1 = 0
    if precision or recall:
        f1 = 2 * (precision * recall) / (precision + recall)
    return precision, recall, f1


def summarize_examples(label: weave.WeaveList, output: weave.WeaveList) -> pd.DataFrame:
    label = label.to_pandas()
    output = output.to_pandas()
    # Initialize summary DataFrame
    result = pd.DataFrame(index=output.index)

    # If output is missing label columns, add nulls
    for col in label.columns:
        if col not in output.columns:
            output[col] = None

    # Add columns for task_correct and task_negative
    for task in output.columns:
        result[f"{task}_correct"] = output[task] == label[task]
        result[f"{task}_negative"] = output[task].isna()

    # Aggregate counts for correct and negative items per row
    result["correct"] = (output == label).sum(axis=1)
    result["negative"] = output.isna().sum(axis=1)

    # Calculate TP, FP, TN, FN per row
    tp = ((label.notna()) & (output == label)).sum(axis=1)
    fp = ((label.notna()) & (output != label)).sum(axis=1)
    tn = ((label.isna()) & (output.isna())).sum(axis=1)
    fn = ((label.isna()) & (output.notna())).sum(axis=1)
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    f1 = 2 * (precision * recall) / (precision + recall)

    # Calculate precision, recall, and F1 score

    # Add these to summary
    result["tp"] = tp
    result["fp"] = fp
    result["tn"] = tn
    result["fn"] = fn
    result["precision"] = precision
    result["recall"] = recall
    result["f1"] = f1

    return ops_arrow.dataframe_to_arrow(result)


def task_pr(example_summary: weave.WeaveList, task_name: str):
    task_negative = example_summary.column(f"{task_name}_negative").to_pandas()
    task_correct = example_summary.column(f"{task_name}_correct").to_pandas()
    tp = (~task_negative & task_correct).sum()
    fp = (~task_negative & ~task_correct).sum()
    tn = (task_negative & task_correct).sum()
    fn = (task_negative & ~task_correct).sum()
    precision, recall, f1 = p_r_f1(tp, fp, fn)
    return {
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def summarize(eval_table: weave.WeaveList, tasks: list[str]) -> dict:
    summary = {}
    for task in tasks:
        summary[f"task_{task}"] = task_pr(eval_table, task)
    for metric in ["precision", "recall", "f1"]:
        summary[f"avg_{metric}"] = sum(
            summary[f"task_{f}"][metric] for f in tasks
        ) / len(tasks)
    return summary


class EvaluateMultiTaskF1Config(typing.TypedDict):
    tasks: typing.List[str]


@weave.op()
def evaluate_multi_task_f1(
    dataset: base_types.Dataset, model: base_types.Model
) -> typing.Any:
    result = []
    latencies = []
    for row in dataset.rows:
        start_time = time.time()
        try:
            model_output = model.predict(row["example"])
        except:
            model_output = {}
        result.append(model_output)
        latencies.append(time.time() - start_time)
    output = weave.WeaveList(result)
    label = dataset.rows.column("label")
    example_summary = summarize_examples(label, output)
    eval_table = weave.WeaveList(
        {
            "dataset_id": dataset.rows.column("id"),
            "output": output,
            "latency": weave.WeaveList(latencies),
            "summary": example_summary,
        }
    )
    tasks = dataset.rows.column("label").to_pandas().columns
    return {
        "summary": summarize(eval_table.column("summary"), tasks),
        "eval_table": eval_table,
    }


def main():
    cli.weave_op_main(evaluate_multi_task_f1)


if __name__ == "__main__":
    main()
