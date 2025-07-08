import time
from pathlib import Path
from typing import List, Tuple

import pandas as pd
import rvm
from evaluation.monitor.specifications import gen_fmla

try:
    import tikzplotlib
except ImportError:
    tikzplotlib = None
from matplotlib import pyplot as plt

from src.evaluation.monitor import path
from src.evaluation.monitor.common_monitor import a, b, c, create_trace, d, make_event_list, update_trace

plt.style.use("ggplot")


def create_specs(size: int, num_atomics: int, seed: int, pred: bool) -> List[Tuple[str, str]]:
    gen_fmla("./eval", seed, size, 10, 0, 1, num_atomics)

    # Initialize the lists
    formulas = []
    idx = 1

    # Open the file and read the lines
    with open(Path(__file__).parent / "fmlas/eval.mdl", "r") as file:
        lines = file.readlines()

    for line in lines:
        line = line.replace("a0", "(a('rand'))" if pred else "a")
        line = line.replace("a1", "(b('rand'))" if pred else "b")
        line = line.replace("a2", "(c('rand'))" if pred else "c")
        line = line.replace("a3", "(d('rand'))" if pred else "d")
        formulas.append((f"S{idx}", f"G({line})"))

    return formulas


def evaluate(
    approach: str,
    mon: rvm.Hydra2,
    tr: rvm.Trace,
    df: pd.DataFrame,
    spec_size: int,
    trace_length: int,
    pred: bool,
    num_iters: int,
):
    event_list = make_event_list(trace_length)
    elapsed_time = 0
    for ite in range(num_iters):
        if pred:
            tr = rvm.Trace(
                event_list,
                [rvm.Function(a), rvm.Function(b), rvm.Function(c), rvm.Function(d)],
                rvm.ConstantCollection([rvm.ConstantValue("rand", 0)]),
            )
        start = time.time()
        mon.evaluate(tr)
        elapsed_time += time.time() - start
    df.loc[len(df)] = [approach, spec_size, elapsed_time / num_iters]


def formula_size_eval(
    name: str,
    num_atomics: int,
    trace_length: int,
    max_formula_size: int,
    max_y: float,
    pred: bool,
    seed: int,
    num_iters: int,
):
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(columns=["Approach", "Formula Size", "Computation Time [s]"])
    update_trace(trace := create_trace(trace_length, num_atomics, seed, pred))
    for spec_size in range(2, max_formula_size + 1, 2):
        print(spec_size)
        specs = create_specs(spec_size, num_atomics, seed, pred)
        formulas = [rvm.Parser.parse(form[1], form[0]) for form in specs]
        evaluate(
            "Baseline",
            rvm.Hydra2(formulas, connectedEval=False, shortCircuiting=False),
            trace,
            df,
            spec_size,
            trace_length,
            pred,
            num_iters,
        )
        evaluate("Ours", rvm.Hydra2(formulas), trace, df, spec_size, trace_length, pred, num_iters)

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
    plt.savefig(f"{path}/{name}.svg")
    if tikzplotlib is not None:
        tikzplotlib.save(f"{path}/{name}.tex")


if __name__ == "__main__":
    formula_size_eval("formula_size_atomic", 4, 1000, 50, 0.3, False, 10, 5)
    formula_size_eval("formula_size_predicate", 4, 1000, 50, 0.3, True, 10, 5)
