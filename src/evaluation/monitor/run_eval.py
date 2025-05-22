"""
Script for Hydra2 experiments.
"""

import subprocess
import time
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import psutil
import yaml
from yaml import Loader

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


def eval_rv_monitors(file_name: str, rv_exec_path: str):
    """
    Evaluates an MTL formula with an RV monitoring algorithm. The resulted verdicts are stored in the output
    directory.

    :param file_name: Name of file.
    :param rv_exec_path: Path to runtime verification executable.
    :return:
    """
    fmla_path = fmlas_path / f"{file_name}.mtl"
    log_path = logs_path / f"{file_name}.log"
    stat_path = stats_path / f"{file_name}.stat"
    args = (rv_exec_path, fmla_path, log_path, stat_path)

    start = time.time()
    with subprocess.Popen(args, stdout=subprocess.PIPE) as popen:
        mem_samples = []
        while popen.poll() is None:
            mem_samples.append(psutil.virtual_memory().used)
        end = time.time()

        output = popen.stdout.read().decode("utf-8")
        with open(output_path / f"{file_name}.rv", mode="w") as fw:
            fw.write(output)

        tim = int((end - start) * 1000)
        mem = max(mem_samples)
        with open(stat_path, "w") as fw:
            fw.write(str(tim) + " " + str(mem))


def run_experiment(exp_name: str):
    """
    Generates randomly formulas and logs for a range of sizes based on different seeds and then evaluates them by
    a RV monitoring algorithm. The resulted verdicts are returned and stored in the output directory. All parameters
    for the generation of formulas and logs are extracted from the configuration file.

    :param exp_name: Name of experiment.
    :return:
    """
    assert config_path.is_file(), f"Configuration file {config_path} is not specified!"

    if not output_path.exists():
        output_path.mkdir(parents=True, exist_ok=True)
    if not stats_path.exists():
        stats_path.mkdir(parents=True, exist_ok=True)

    with open(config_path, "r") as f:
        config = yaml.load(f, Loader=Loader)

    exp = config["experiment"]
    fmla = exp["fmla"]
    log = exp["log"]
    for path in exp["rv_exec"]:
        print(Path(__file__).parent.parent / path)
        if (Path(__file__).parent.parent / path).exists():
            rv_exec = Path(__file__).parent.parent / path
            break
    for size in range(fmla["sizes"]["min"], fmla["sizes"]["max"] + 1):
        for seed in exp["seeds"]:
            file_name = "_".join(map(str, [exp_name, size, seed]))
            gen_fmla(
                file_name,
                seed,
                size,
                fmla["max_int"],
                fmla["type"],
                fmla["scale"],
                exp["aps"],
            )
            fmla_path = fmlas_path / f"{file_name}.mdl"
            with open(fmla_path, "r") as fr:
                fmla_content = fr.read()
            if fmla_content.__contains__("[0,0]"):  # TODO: Remove when bug is fixed for formulas containing [0,0]
                with open(fmla_path, "w") as fw:
                    fw.write("G(true)")
            else:
                fmla_globally = "G(" + fmla_content + ")"
                with open(fmla_path, "w") as fw:
                    fw.write(fmla_globally)
            fmla_path.rename(str(fmla_path).replace(".mdl", ".mtl"))
            gen_log(file_name, log["ts_cnt"], log["er"], log["delta"], seed, exp["aps"])
            eval_rv_monitors(file_name, rv_exec)

    for file_name in [f for f in list(fmlas_path.glob("*"))]:
        if file_name.suffix == ".mfotl":
            file_name.unlink()
    for file_name in [f for f in list(logs_path.glob("*"))]:
        for ending in [".mlog", ".r2u2"]:
            if file_name.suffix == ending:
                file_name.unlink()

    gen_figs()


if __name__ == "__main__":
    run_experiment("test_experiment")
