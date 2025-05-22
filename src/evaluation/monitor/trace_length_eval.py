import time
from pathlib import Path
from typing import List, Tuple

import pandas as pd
import rvm
import tikzplotlib
from evaluation.run_eval import gen_log
from matplotlib import pyplot as plt

plt.style.use("ggplot")

specs1 = [
    ("S1", "G((a) S[0, 4] (b))"),
    (
        "S2",
        "G((a) U[0, 4] (b))",
    ),
    ("S3", "G((a) U[0, 4] (b) & (a) S[0, 4] (b))"),
]

specs2 = [
    ("S1", "G(P[0, 4] a)"),
    (
        "S2",
        "G(X[0, 4] b)",
    ),
    ("S3", "G((c) U[0, 4] (d) & (e) S[0, 4] (f))"),
]


def create_trace(length: int, num_atomics: int, seed: int) -> rvm.Trace:
    gen_log("./eval", length, 1, 10, seed, num_atomics)

    # Initialize the lists
    actions = []
    time_steps = []

    # Open the file and read the lines
    with open("./logs/eval.log", "r") as file:
        lines = file.readlines()

    # Process each line
    for line in lines:
        # Split the line into parts
        parts = line.strip().split()

        # The first part is the time step
        time_step = int(parts[0][1:])

        # The remaining parts are the actions
        action = []
        for part in parts[1:]:
            if part == "a0":
                action.append("a")
            elif part == "a1":
                action.append("b")
            elif part == "a2":
                action.append("c")
            elif part == "a3":
                action.append("d")
            elif part == "a4":
                action.append("e")
            elif part == "a5":
                action.append("f")
            else:
                raise RuntimeError("unknown atomic")

        # Add to the lists
        actions.append(action)
        time_steps.append(time_step)

    atomic_names = {"a", "b"} if num_atomics == 2 else {"a", "b", "c", "d", "e", "f"}

    return rvm.create_trace(atomic_names, actions, time_steps)


def evaluate(approach: str, mon: rvm.Hydra2, tr: rvm.Trace, df: pd.DataFrame, trace_length: int):
    elapsed_time = 0
    num_iters = 5
    for ite in range(num_iters):
        start = time.time()
        mon.evaluate(tr)
        elapsed_time += time.time() - start
    df.loc[len(df)] = [approach, trace_length, elapsed_time / num_iters]


def eval_and_fig(spec: List[Tuple[str, str]], name: str, num_atomics: int, max_y: float):
    trace_lengths = range(20000, 220000, 20000)
    x_axis_text = "Trace Length [x10000]"

    if not Path("./monitor_artificial_examples").exists():
        Path("./monitor_artificial_examples").mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(columns=["Approach", x_axis_text, "Comp. Time [s]"])
    formulas = [rvm.Parser.parse(form[1], form[0]) for form in spec]
    for trace_length in trace_lengths:
        print(trace_length)
        trace = create_trace(trace_length, num_atomics, 2)
        evaluate(
            "Baseline",
            rvm.Hydra2(formulas, connectedEval=False, shortCircuiting=False),
            trace,
            df,
            trace_length,
        )
        evaluate("Ours", rvm.Hydra2(formulas), trace, df, trace_length)
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
    plt.savefig(f"./monitor_artificial_examples/{name}.svg")
    tikzplotlib.save(f"./monitor_artificial_examples/{name}.tex")


eval_and_fig(specs1, "running_example_atomic", 2, 1.1)
eval_and_fig(specs2, "dissimilar_atomic", 6, 1.1)
