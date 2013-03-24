import functools
import threading




global __profile_lock
__profile_lock = threading.Lock()


def profile(fn):
    import line_profiler
    global __profile_lock
    with __profile_lock:
        if not hasattr(profile, 'profiler'):
            prof = profile.profiler = line_profiler.LineProfiler()
        else:
            prof = profile.profiler
    fn_ = prof(fn)
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        prof.enable_by_count()
        try:
            return fn_(*args, **kwargs)
        finally:
            prof.disable_by_count()
            prof.dump_stats('/home/sjagoe/github-jenkins/prof.lprof')
    return wrapper
