import time

import rvm

from src.evaluation.monitor.trace_length_eval_predicate import make_event_list


# 2ms
def low_comp_time(time_step: int, rand: int) -> bool:
    time.sleep(0.002)
    return True


# 100ms
def high_comp_time(time_step: int, rand: int) -> bool:
    time.sleep(0.1)
    return True


def lazy_eval(mon: rvm.Hydra2, trace_length: int):
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
