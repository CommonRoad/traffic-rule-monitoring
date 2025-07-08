import time
from typing import List, Tuple

import matplotlib.pyplot as plt
import pandas as pd
import rvm
from evaluation.monitor.common_monitor import a, b, c, create_trace, d, e, f, make_event_list, update_trace
from evaluation.monitor.specifications import specs1_atomic, specs1_pred, specs2_atomic, specs2_pred

from src.evaluation.monitor import path

try:
    import tikzplotlib
except ImportError:
    tikzplotlib = None


plt.style.use("ggplot")


def evaluate(
    approach: str, mon: rvm.Hydra2, tr: rvm.Trace, df: pd.DataFrame, trace_length: int, pred: bool, num_iters: int
):
    event_list = make_event_list(trace_length)

    elapsed_time = 0
    for ite in range(num_iters):
        if pred:
            tr = rvm.Trace(
                event_list,
                [
                    rvm.Function(a),
                    rvm.Function(b),
                    rvm.Function(c),
                    rvm.Function(d),
                    rvm.Function(e),
                    rvm.Function(f),
                ],
                rvm.ConstantCollection([rvm.ConstantValue("rand", 0)]),
            )
        start = time.time()
        mon.evaluate(tr)
        elapsed_time += time.time() - start
    df.loc[len(df)] = [approach, trace_length, elapsed_time / num_iters]


def eval_trace_length(
    spec: List[Tuple[str, str]],
    name: str,
    num_atomics: int,
    max_y: float,
    pred: bool,
    seed: int,
    trace_lengths: range,
    x_axis_text: str,
    num_inters: int,
):
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(columns=["Approach", x_axis_text, "Comp. Time [s]"])
    formulas = [rvm.Parser.parse(form[1], form[0]) for form in spec]

    for trace_length in trace_lengths:
        print(trace_length)
        update_trace(trace := create_trace(trace_length, num_atomics, seed, pred))
        evaluate(
            "Baseline",
            rvm.Hydra2(formulas, connectedEval=False, shortCircuiting=False),
            trace,
            df,
            trace_length,
            pred,
            num_inters,
        )
        evaluate("Ours", rvm.Hydra2(formulas), trace, df, trace_length, pred, num_inters)

    # Plotting
    plt.figure(figsize=(10, 8))
    plt.rcParams["svg.fonttype"] = "none"
    for approach in df["Approach"].unique():
        subset = df[df["Approach"] == approach]
        max_y = max(max_y, max(subset["Comp. Time [s]"]))
        plt.plot(
            subset[x_axis_text],
            subset["Comp. Time [s]"],
            marker="o",
            markersize=5,
            linewidth=4,
            label=approach,
        )

    plt.xlabel(x_axis_text, labelpad=40, color="black")
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
    eval_trace_length(
        specs1_pred, "running_example_predicate", 2, 0.6, True, 10, range(500, 5500, 500), "Trace Length [x100]", 5
    )
    eval_trace_length(
        specs2_pred, "dissimilar_predicate", 6, 0.6, True, 10, range(500, 5500, 500), "Trace Length [x100]", 5
    )

    eval_trace_length(
        specs1_atomic,
        "running_example_atomic",
        2,
        1.1,
        False,
        10,
        range(20000, 220000, 20000),
        "Trace Length [x10000]",
        5,
    )
    eval_trace_length(
        specs2_atomic, "dissimilar_atomic", 6, 1.1, False, 10, range(20000, 220000, 20000), "Trace Length [x10000]", 5
    )
