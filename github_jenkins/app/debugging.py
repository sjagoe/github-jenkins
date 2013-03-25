import functools


def profile(fn):
    import line_profiler
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


def log_error(logger):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception:
                logger.exception('Error in view')
                raise
        return wrapper
    return decorator
