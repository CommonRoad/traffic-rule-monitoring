import time
from pathlib import Path
from typing import List, Tuple

import pandas as pd
import rvm
import tikzplotlib
from evaluation.run_eval import gen_fmla, gen_log
from matplotlib import pyplot as plt
from tests.bindings.test_bindings import make_event_list

plt.style.use("ggplot")

trace = []


# 0.00001ms
def a(time_step: int, rand: int) -> bool:
    time.sleep(float(0.00001 / 1000))
    return "a" in trace[time_step]


# 0.00005ms
def b(time_step: int, rand: int) -> bool:
    time.sleep(0.00005 / 1000)
    return "b" in trace[time_step]


# 0.00002ms
def c(time_step: int, rand: int) -> bool:
    time.sleep(0.00002 / 1000)
    return "c" in trace[time_step]


# 0.000001ms
def d(time_step: int, rand: int) -> bool:
    time.sleep(0.000001 / 1000)
    return "d" in trace[time_step]


def create_trace(length: int, num_atomics: int, seed: int) -> List[List[str]]:
    gen_log("./eval", length, 1, 10, seed, num_atomics)

    # Initialize the lists
    actions = []

    # Open the file and read the lines
    with open("./logs/eval.log", "r") as file:
        lines = file.readlines()

    # Process each line
    for line in lines:
        # Split the line into parts
        parts = line.strip().split()

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

    return actions


def create_specs(size: int, num_atomics: int, seed: int) -> List[Tuple[str, str]]:
    gen_fmla("./eval", seed, size, 10, 0, 1, num_atomics)

    # Initialize the lists
    formulas = []
    idx = 1

    # Open the file and read the lines
    with open("./fmlas/eval.mdl", "r") as file:
        lines = file.readlines()

    for line in lines:
        line = line.replace("a0", "(a('rand'))")
        line = line.replace("a1", "(b('rand'))")
        line = line.replace("a2", "(c('rand'))")
        line = line.replace("a3", "(d('rand'))")
        formulas.append((f"S{idx}", f"G({line})"))

    return formulas


def evaluate(approach: str, mon: rvm.Hydra2, df: pd.DataFrame, spec_size: int, trace_length: int):
    event_list = make_event_list(trace_length)

    elapsed_time = 0
    num_iters = 5
    for ite in range(num_iters):
        tr = rvm.Trace(
            event_list,
            [rvm.Function(a), rvm.Function(b), rvm.Function(c), rvm.Function(d)],
            rvm.ConstantCollection([rvm.ConstantValue("rand", 0)]),
        )
        start = time.time()
        mon.evaluate(tr)
        elapsed_time += time.time() - start
    df.loc[len(df)] = [approach, spec_size, elapsed_time / num_iters]


def eval_and_fig(name: str, num_atomics: int, trace_length: int, max_y: float):
    if not Path("./monitor_artificial_examples").exists():
        Path("./monitor_artificial_examples").mkdir(parents=True, exist_ok=True)
    seed = 4
    df = pd.DataFrame(columns=["Approach", "Formula Size", "Computation Time [s]"])
    global trace
    trace = create_trace(trace_length, num_atomics, seed)
    for spec_size in range(2, 51, 2):
        print(spec_size)
        specs = create_specs(spec_size, num_atomics, seed)
        formulas = [rvm.Parser.parse(form[1], form[0]) for form in specs]

        evaluate(
            "Baseline",
            rvm.Hydra2(formulas, connectedEval=False, shortCircuiting=False),
            df,
            spec_size,
            trace_length,
        )
        evaluate("Ours", rvm.Hydra2(formulas), df, spec_size, trace_length)

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


eval_and_fig("formula_size_predicate", 4, 1000, 0.3)
