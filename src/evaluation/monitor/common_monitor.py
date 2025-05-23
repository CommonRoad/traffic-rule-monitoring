"""
Script for Hydra2 experiments.
"""

import subprocess
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt

matplotlib.use("agg")

exec_path = Path(__file__).parent / "exec"
fmlas_path = Path(__file__).parent / Path("fmlas")
logs_path = Path(__file__).parent / Path("logs")
output_path = Path(__file__).parent / Path("output")
stats_path = Path(__file__).parent / Path("stats")
figs_path = Path(__file__).parent / Path("figs")
config_path = Path(__file__).parent / Path("../../../configurations/rv_monitor/rv_monitor.yaml")


def gen_fmla(file_name: str, seed: int, size: int, max_int: int, typ: int, scale: int, aps: int):
    """
    Generates formula. The generated formula is stored in the fmlas directory.

    :param file_name: Name of evaluation.
    :param seed: Seed for generator.
    :param size: Number of operators and atomic proposition in formula.
    :param max_int: Maximal lower and upper bound for time interval.
    :param typ: Type of temporal logic (MTL: 0, MDL: 1, MFOTL: 2).
    :param scale: Scale factor.
    :param aps: Maximal number of atomic propositions.
    """
    if not fmlas_path.exists():
        fmlas_path.mkdir(parents=True, exist_ok=True)

    args = (
        str(exec_path / "gen_fmla"),
        str(fmlas_path / file_name),
        str(size),
        str(max_int),
        str(typ),
        str(scale),
        str(seed),
        str(aps),
    )
    popen = subprocess.Popen(args)
    popen.wait()


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
