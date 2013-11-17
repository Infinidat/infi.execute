from .ioloop import IOLoop, time

DEFAULT_SAMPLE_INTERVAL = 0.05

def wait_for_many_results(results, **kwargs):
    ioloop = IOLoop()
    results = dict((result, None) for result in results)
    for result in results.keys():
        result.register_to_ioloop(ioloop)
    timeout = kwargs.pop('timeout', None)
    deadline = _get_deadline(results.keys(), timeout)

    # Note that the _should_still_wait predicate might return False if
    # things happen real quickly
    while True:
        current_time = time()
        ioloop.do_iteration(_get_wait_interval(current_time, deadline))
        _sweep_finished_results(results, ioloop)
        if not _should_still_wait(results, deadline=deadline):
            break
    _sweep_finished_results(results, ioloop)
    return results.values()

def flush(result):
    ioloop = IOLoop()
    result.register_to_ioloop(ioloop)
    ioloop.flush()

def _get_deadline(results, timeout=None):
    """ returns the earliest deadline point in time """
    start_time = time()

    all_deadlines = set(result.get_deadline() for result in results)
    all_deadlines.discard(None)
    if timeout is not None:
        all_deadlines.add(start_time + timeout)
    return min(all_deadlines) if all_deadlines else None

def _get_wait_interval(current_time, deadline):
    if deadline is None:
        return DEFAULT_SAMPLE_INTERVAL
    return max(0, min(DEFAULT_SAMPLE_INTERVAL, (deadline - current_time)))

def _sweep_finished_results(results, ioloop):
    for result in results.keys():
        if results[result] is not None:
            continue
        # we unregister and re-register, because when is_finished returns True, the pipes are flushed and closed
        result.unregister_from_ioloop(ioloop)
        if result.is_finished():
            results[result] = result
        result.register_to_ioloop(ioloop)

def _should_still_wait(results, deadline):
    if all(r is not None for r in results.values()):
        return False
    if deadline is not None and deadline < time():
        return False
    return True
