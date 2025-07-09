from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import pandas as pd
import rvm
import yaml
from evaluation.monitor.common_monitor import create_trace, evaluate, update_trace

from src.evaluation.monitor import path

try:
    import tikzplotlib
except ImportError:
    tikzplotlib = None

plt.style.use("ggplot")


def eval_lazy(
    spec: List[Tuple[str, str]],
    name: str,
    num_atomics: int,
    max_y: float,
    pred: bool,
    trace_lengths: range,
    xlabel: str,
    num_iters: int,
    seed: int,
    with_tex: bool,
    pred_cost: Dict[str, Dict[str, Dict[str, List[float]]]],
):
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(columns=["Approach", xlabel, "Comp. Time [s]"])
    formulas = [rvm.Parser.parse(form[1], form[0]) for form in spec]

    for trace_length in trace_lengths:
        print(trace_length)
        update_trace(trace := create_trace(trace_length, num_atomics, seed, pred))
        evaluate(
            "PredCost1",
            rvm.Hydra2(formulas, predicateCosts=pred_cost["PredCost1"]),
            trace,
            df,
            None,
            trace_length,
            pred,
            num_iters,
        )
        evaluate(
            "PredCost2",
            rvm.Hydra2(formulas, predicateCosts=pred_cost["PredCost2"]),
            trace,
            df,
            None,
            trace_length,
            pred,
            num_iters,
        )

    # Plotting
    plt.figure(figsize=(10, 8))
    plt.rcParams["svg.fonttype"] = "none"
    for approach in df["Approach"].unique():
        subset = df[df["Approach"] == approach]
        max_y = max(max_y, max(subset["Comp. Time [s]"]))
        plt.plot(
            subset[xlabel].to_numpy(),
            subset["Comp. Time [s]"].to_numpy(),
            marker="o",
            markersize=5,
            linewidth=4,
            label=approach,
        )

    plt.xlabel(xlabel, labelpad=40, color="black")
    plt.ylabel("Computation Time [s]", labelpad=45, color="black")
    plt.ylim(bottom=0, top=max_y)
    plt.yticks(color="black")
    plt.xticks(
        trace_lengths,
        [str(int(i / int(xlabel[xlabel.find("[x") + 2 : -1] if len(xlabel) > 12 else 1))) for i in trace_lengths],
        color="black",
    )
    plt.tick_params(axis="x", which="major", pad=30, color="black")
    plt.tick_params(axis="y", labelcolor="black", top=max_y)
    plt.legend(fontsize=30)
    plt.savefig(f"{path}/{name}.svg")
    if with_tex and tikzplotlib:
        tikzplotlib.save(f"{path}/{name}.tex")
    elif with_tex and not tikzplotlib:
        raise RuntimeError("tikzplotlib not available")


if __name__ == "__main__":
    with open(
        Path(__file__).parent.parent.parent.parent / "configurations/rv_monitor/evaluation_parameters.yaml", "r"
    ) as f:
        params = yaml.safe_load(f)
    seed_var = params["general"]["seed"]
    iters = params["general"]["num_iters"]
    tex = params["general"]["with_tex"]
    for eval_params in params["lazy_eval"]:
        eval_lazy(**eval_params, num_iters=iters, seed=seed_var, with_tex=tex)
