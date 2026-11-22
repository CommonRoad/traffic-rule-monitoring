import multiprocessing
from typing import Any, Callable, Optional, Tuple

# Cut-off time for a single evaluation (20 min), as in the paper; failed evaluations are marked "x".
CUTOFF_SECONDS = 20 * 60
FAILED_CELL = "x"


def _child(conn, func: Callable, args: Tuple) -> None:
    try:
        conn.send(("ok", func(*args)))
    except BaseException as exc:  # noqa: BLE001 - report every failure to the parent
        conn.send(("error", repr(exc)))
    finally:
        conn.close()


def run_with_cutoff(func: Callable, args: Tuple, cutoff: float = CUTOFF_SECONDS) -> Tuple[str, Optional[Any]]:
    """Run func(*args) in a separate process and kill it after cutoff seconds.

    Native (C++) code cannot be interrupted from within the process, hence the separate process.
    Returns ("ok", result), ("timeout", None), or ("error", message)."""
    ctx = multiprocessing.get_context("fork")
    parent_conn, child_conn = ctx.Pipe(duplex=False)
    proc = ctx.Process(target=_child, args=(child_conn, func, args))
    proc.start()
    child_conn.close()
    status: Tuple[str, Optional[Any]]
    if parent_conn.poll(cutoff):
        try:
            status = parent_conn.recv()
        except EOFError:
            status = ("error", f"process died with exit code {proc.exitcode}")
    elif proc.is_alive():
        status = ("timeout", None)
    else:
        status = ("error", f"process died with exit code {proc.exitcode}")
    if proc.is_alive():
        proc.kill()
    proc.join()
    parent_conn.close()
    return status


def format_cell(value: Optional[float]) -> str:
    """Table cell for a computation time; None (cut-off or error) is reported as "x"."""
    return FAILED_CELL if value is None else f"{value:.4f}"
