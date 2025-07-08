from typing import Dict, List

import pandas as pd
import rvm
from evaluation.monitor import path
from evaluation.monitor.common_monitor import create_trace, evaluate, update_trace


def lazy_eval(
    specs: List[str], pred_cost: Dict[str, Dict[str, List[float]]], trace_length: int, num_iters: int, seed: int
):
    formulas = [rvm.Parser.parse(form[1], form[0]) for form in specs]
    df = pd.DataFrame(columns=["Approach", "Trace Length", "Computation Time [s]"])
    update_trace(trace := create_trace(trace_length, 0, seed, True))
    evaluate(
        "PredCost1",
        rvm.Hydra2(formulas, predicateCosts=pred_cost["PredCost1"]),
        trace,
        df,
        None,
        trace_length,
        True,
        num_iters,
    )
    evaluate(
        "PredCost2",
        rvm.Hydra2(formulas, predicateCosts=pred_cost["PredCost2"]),
        trace,
        df,
        None,
        trace_length,
        True,
        num_iters,
    )

    # Store results in a text file
    df.to_csv(f"{path}/lazy_eval_results.txt", index=False)


if __name__ == "__main__":
    lazy_eval(50, 5, 10)
