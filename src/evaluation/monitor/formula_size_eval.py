import time
from typing import List, Tuple

import pandas as pd
import rvm
import tikzplotlib
from matplotlib import pyplot as plt

from src.evaluation.monitor.run_eval import gen_fmla, gen_log

plt.style.use("ggplot")


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
            else:
                raise RuntimeError("unknown atomic")

        # Add to the lists
        actions.append(action)
        time_steps.append(time_step)

    atomic_names = {"a", "b"} if num_atomics == 2 else {"a", "b", "c", "d"}

    return rvm.create_trace(atomic_names, actions, time_steps)


def create_specs(size: int, num_atomics: int, seed: int) -> List[Tuple[str, str]]:
    gen_fmla("./eval", seed, size, 10, 0, 1, num_atomics)

    # Initialize the lists
    formulas = []
    idx = 1

    # Open the file and read the lines
    with open("./fmlas/eval.mdl", "r") as file:
        lines = file.readlines()

    for line in lines:
        line = line.replace("a0", "a")
        line = line.replace("a1", "b")
        line = line.replace("a2", "c")
        line = line.replace("a3", "d")
        formulas.append((f"S{idx}", f"G({line})"))

    return formulas


def evaluate(approach: str, mon: rvm.Hydra2, tr: rvm.Trace, df: pd.DataFrame, spec_size: int):
    elapsed_time = 0
    num_iters = 5
    for ite in range(num_iters):
        start = time.time()
        mon.evaluate(tr)
        elapsed_time += time.time() - start
    df.loc[len(df)] = [approach, spec_size, elapsed_time / num_iters]


def eval_and_fig(name: str, num_atomics: int, trace_length: int, max_formula_size: int, max_y: float):
    seed = 10
    df = pd.DataFrame(columns=["Approach", "Formula Size", "Computation Time [s]"])
    trace = create_trace(trace_length, num_atomics, seed)
    for spec_size in range(2, max_formula_size + 1, 2):
        print(spec_size)
        specs = create_specs(spec_size, num_atomics, seed)
        formulas = [rvm.Parser.parse(form[1], form[0]) for form in specs]

        evaluate(
            "Baseline",
            rvm.Hydra2(formulas, connectedEval=False, shortCircuiting=False),
            trace,
            df,
            spec_size,
        )
        evaluate("Ours", rvm.Hydra2(formulas), trace, df, spec_size)

    plt.figure(figsize=(10, 8))
    plt.rcParams["svg.fonttype"] = "none"
    for approach in df["Approach"].unique():
        subset = df[df["Approach"] == approach]
        plt.plot(
            subset["Formula Size"],
            subset["Computation Time [s]"],
            marker="o",
            markersize=5,
            linewidth=4,
            label=approach,
        )

    # Set labels and legend
    plt.xlabel("Formula Size", labelpad=40, color="black")
    plt.ylabel("Computation Time [s]", labelpad=80, color="black")
    plt.ylim(bottom=0, top=max_y)
    plt.yticks(color="black")
    plt.tick_params(axis="x", which="major", pad=30, color="black")
    plt.tick_params(axis="y", labelcolor="black", top=max_y)
    plt.legend(fontsize=30)
    plt.savefig(f"./monitor_artificial_examples/{name}.svg")
    tikzplotlib.save(f"./monitor_artificial_examples/{name}.tex")


eval_and_fig("formula_size_atomic", 4, 1000, 50, 0.3)
