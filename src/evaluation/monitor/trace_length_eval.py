from pathlib import Path
from typing import List, Tuple

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


def eval_trace_length(
    spec: List[Tuple[str, str]],
    name: str,
    num_atomics: int,
    max_y: float,
    pred: bool,
    trace_lengths: range,
    xlabel: str,
    num_iters: int,
    seed: int,
):
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(columns=["Approach", xlabel, "Comp. Time [s]"])
    formulas = [rvm.Parser.parse(form[1], form[0]) for form in spec]

    for trace_length in trace_lengths:
        print(trace_length)
        update_trace(trace := create_trace(trace_length, num_atomics, seed, pred))
        evaluate(
            "Baseline",
            rvm.Hydra2(formulas, connectedEval=False, shortCircuiting=False),
            trace,
            df,
            None,
            trace_length,
            pred,
            num_iters,
        )
        evaluate("Ours", rvm.Hydra2(formulas), trace, df, None, trace_length, pred, num_iters)

    # Plotting
    plt.figure(figsize=(10, 8))
    plt.rcParams["svg.fonttype"] = "none"
    for approach in df["Approach"].unique():
        subset = df[df["Approach"] == approach]
        max_y = max(max_y, max(subset["Comp. Time [s]"]))
        plt.plot(
            subset[xlabel],
            subset["Comp. Time [s]"],
            marker="o",
            markersize=5,
            linewidth=4,
            label=approach,
        )

    plt.xlabel(xlabel, labelpad=40, color="black")
    plt.ylabel("Computation Time [s]", labelpad=45, color="black")
    plt.ylim(bottom=0, top=max_y)
    plt.yticks(color="black")
    plt.xticks(trace_lengths, [str(int(i / 10000)) for i in trace_lengths], color="black")
    plt.tick_params(axis="x", which="major", pad=30, color="black")
    plt.tick_params(axis="y", labelcolor="black", top=max_y)
    plt.legend(fontsize=30)
    plt.savefig(f"{path}/{name}.svg")
    if tikzplotlib:
        tikzplotlib.save(f"{path}/{name}.tex")


if __name__ == "__main__":
    with open(
        Path(__file__).parent.parent.parent.parent / "configurations/rv_monitor/evaluation_parameters.yaml", "r"
    ) as f:
        params = yaml.safe_load(f)
    seed = params["general"]["seed"]
    num_iters = params["general"]["num_iters"]
    for eval_params in params["eval_trace_length"]:
        eval_trace_length(**eval_params, num_iters=num_iters, seed=seed)
