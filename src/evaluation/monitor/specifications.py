import subprocess
from pathlib import Path

fmlas_path = Path(__file__).parent / Path("fmlas")
exec_path = Path(__file__).parent / "exec"


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
