import time

import rvm
from evaluation.monitor import path
from evaluation.monitor.common_monitor import high_comp_time, low_comp_time, make_event_list
from evaluation.monitor.specifications import predicate_cost_1, predicate_cost_2, specs_lazy


def lazy_eval(mon: rvm.Hydra2, trace_length: int, num_iters) -> float:
    event_list = make_event_list(trace_length)
    tr = rvm.Trace(
        event_list,
        [rvm.Function(low_comp_time), rvm.Function(high_comp_time)],
        rvm.ConstantCollection([rvm.ConstantValue("rand", 0)]),
    )

    elapsed_time = 0
    for ite in range(num_iters):
        start = time.time()
        mon.evaluate(tr)
        elapsed_time += time.time() - start

    return elapsed_time / num_iters


if __name__ == "__main__":
    formulas = [rvm.Parser.parse(form[1], form[0]) for form in specs_lazy]
    res_pred1 = lazy_eval(rvm.Hydra2(formulas, predicateCosts=predicate_cost_1), 50, 5)
    res_pred2 = lazy_eval(rvm.Hydra2(formulas, predicateCosts=predicate_cost_2), 50, 5)

    # Store results in a text file
    with open(f"{path}/lazy_eval_results.txt", "w") as f:
        f.write(f"Result with predicate_cost_1: {res_pred1}\n")
        f.write(f"Result with predicate_cost_2: {res_pred2}\n")
