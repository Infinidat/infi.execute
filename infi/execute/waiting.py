import time
from .ioloop import IOLoop

DEFAULT_SAMPLE_INTERVAL = 0.05

def wait_for_many_results(results, **kwargs):
    ioloop = IOLoop()
    results = list(results)
    for result in results:
        result.register_to_ioloop(ioloop)
    timeout = kwargs.pop('timeout', None)
    deadline = _get_deadline(results, timeout)
    returned = [None for result in results]

    # Note that the _should_still_wait predicate might return False if
    # things happen real quickly
    while True:
        current_time = time.time()
        ioloop.do_iteration(_get_wait_interval(current_time, deadline))
        _sweep_finished_results(results, returned)
        if not _should_still_wait(results, deadline=deadline):
            break
    _sweep_finished_results(results, returned)
    return returned

def _get_deadline(results, timeout=None):
    """ returns the earliest deadline point in time """
    start_time = time.time()

    all_deadlines = set(result.get_deadline() for result in results)
    all_deadlines.discard(None)
    if timeout is not None:
        all_deadlines.add(start_time + timeout)
    return min(all_deadlines) if all_deadlines else None

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
