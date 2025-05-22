import time

import rvm
from tests.bindings.test_bindings import make_event_list

specs = [("S1", "G(low_comp_time('rand') | high_comp_time('rand'))")]


# 2ms
def low_comp_time(time_step: int, rand: int) -> bool:
    time.sleep(0.002)
    return True


# 100ms
def high_comp_time(time_step: int, rand: int) -> bool:
    time.sleep(0.1)
    return True


def evaluate(mon: rvm.Hydra2, trace_length: int):
    event_list = make_event_list(trace_length)
    tr = rvm.Trace(
        event_list,
        [rvm.Function(low_comp_time), rvm.Function(high_comp_time)],
        rvm.ConstantCollection([rvm.ConstantValue("rand", 0)]),
    )

    elapsed_time = 0
    num_iters = 5
    for ite in range(num_iters):
        start = time.time()
        mon.evaluate(tr)
        elapsed_time += time.time() - start

    print(elapsed_time / num_iters)


predicate_cost_1 = {
    "low_comp_time": [1.0, 1.0, 0.0],
    "high_comp_time": [100.0, 0.0, 0.0],
}

predicate_cost_2 = {
    "low_comp_time": [100.0, 0.0, 0.0],
    "high_comp_time": [1.0, 1.0, 0.0],
}

formulas = [rvm.Parser.parse(form[1], form[0]) for form in specs]
evaluate(rvm.Hydra2(formulas, predicateCosts=predicate_cost_1), 50)
evaluate(rvm.Hydra2(formulas, predicateCosts=predicate_cost_2), 50)
