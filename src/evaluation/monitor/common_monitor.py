import subprocess
import time
from pathlib import Path
from typing import List

import matplotlib
import matplotlib.pyplot as plt
import rvm

matplotlib.use("agg")

exec_path = Path(__file__).parent / "exec"
logs_path = Path(__file__).parent / Path("logs")
output_path = Path(__file__).parent / Path("output")
stats_path = Path(__file__).parent / Path("stats")
figs_path = Path(__file__).parent / Path("figs")
config_path = Path(__file__).parent / Path("../../../configurations/rv_monitor/rv_monitor.yaml")

trace = []


def update_trace(new_trace: List[List[str]]):
    """
    Updates the global trace variable with a new trace.
    """
    global trace
    trace = new_trace


def make_event_list(size):
    return [rvm.Event(i, i == size - 1) for i in range(size)]


def create_trace(length: int, num_atomics: int, seed: int, predicate: bool) -> rvm.Trace | List[List[str]]:
    gen_log("./eval", length, 1, 10, seed, num_atomics)

    # Initialize the lists
    actions = []
    time_steps = []

    # Open the file and read the lines
    with open(Path(__file__).parent / "logs/eval.log", "r") as file:
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

    if not predicate:
        atomic_names = {"a", "b"} if num_atomics == 2 else {"a", "b", "c", "d", "e", "f"}
        return rvm.create_trace(atomic_names, actions, time_steps)
    else:
        return actions


# 2ms
def low_comp_time(time_step: int, rand: int) -> bool:
    time.sleep(0.002)
    return True


# 100ms
def high_comp_time(time_step: int, rand: int) -> bool:
    time.sleep(0.1)
    return True


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


# 0.0002ms
def e(time_step: int, rand: int) -> bool:
    time.sleep(0.0002 / 1000)
    return "e" in trace[time_step]


# 0.00001ms
def f(time_step: int, rand: int) -> bool:
    time.sleep(0.00001 / 1000)
    return "f" in trace[time_step]


def gen_log(file_name: str, ts_cnt: int, er: int, delta: int, seed: int, aps: int):
    """
    Generates log. The generated log is stored in the logs directory.

    :param file_name: Name of evaluation.
    :param ts_cnt: Number of different time steps.
    :param er: Number of repetitions of same time step.
    :param delta: Maximal time step.
    :param seed: Seed for generator.
    :param aps: Number of atomic propositions.
    """
    if not logs_path.exists():
        logs_path.mkdir(parents=True, exist_ok=True)

    args = (
        str(exec_path / "gen_log"),
        str(logs_path / file_name),
        str(ts_cnt),
        str(er),
        str(delta),
        str(seed),
        str(aps),
    )
    popen = subprocess.Popen(args)
    popen.wait()


def gen_figs():
    """
    Generates figure which indicates the computation time dependent on the size of the formula. The generated figure
    is stored in the figs directory.
    """
    if not figs_path.exists():
        figs_path.mkdir(parents=True, exist_ok=True)

    sizes, times, mems = [], [], []
    for file_name in [f for f in list(stats_path.glob("*.stat"))]:
        with open(file_name, "r") as fr:
            stat = fr.read()
        msmts = stat.split(" ")
        sizes.append(int(str(file_name).split("_")[-2]))
        times.append(int(msmts[0]))
        mems.append(int(msmts[1]))

    for size, tim in zip(sizes, times):
        plt.plot([size], [tim], marker="o", color="red", fillstyle="none")
    plt.xlabel("Formula Size")
    plt.ylabel("Computation Time [ms]")
    plt.grid()
    plt.savefig(figs_path / "time_complexity.png")
    plt.close()

    for size, mem in zip(sizes, mems):
        plt.plot([size], [mem], marker="o", color="red", fillstyle="none")
    plt.xlabel("Formula Size")
    plt.ylabel("Memory Usage [Bytes]")
    plt.grid()
    plt.savefig(figs_path / "space_complexity.png")
