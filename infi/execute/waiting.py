import time
import itertools
from .ioloop import IOLoop

def wait_for_many_results(results, **kwargs):
    ioloop = IOLoop()
    results = list(results)
    for result in results:
        result.register_to_ioloop(ioloop)
    timeout = kwargs.pop('timeout', None)
    deadline = _get_deadline(results, timeout)
    returned = [None for result in results]
    while _should_still_wait(results, deadline=deadline):
        current_time = time.time()
        ioloop.do_iteration(_get_wait_interval(current_time, deadline))
        _sweep_finished_results(results, returned)
    _sweep_finished_results(results, returned)
    return returned

DEFAULT_SAMPLE_INTERVAL = 0.05

def _get_deadline(results, deadline):
    returned = None
    for d in itertools.chain([deadline], (result.get_deadline() for result in results)):
        if d is None:
            continue
        if returned is None or d < returned:
            returned = d
    return returned

def _get_wait_interval(current_time, deadline):
    if deadline is None:
        return DEFAULT_SAMPLE_INTERVAL
    return max(0, min(DEFAULT_SAMPLE_INTERVAL, (deadline - current_time)))

def _sweep_finished_results(results, returned):
    for index, result in enumerate(results):
        if result is None:
            continue
        result.poll()
        if result.is_finished():
            returned[index] = result
            results[index] = None

def _should_still_wait(results, deadline):
    if all(r is None for r in results):
        return False
    current_time = time.time()
    if deadline is not None and deadline < time.time():
        return False
    return True
