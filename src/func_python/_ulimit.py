import logging

_MAX_NOFILE = 65536  # safe cap when hard == RLIM_INFINITY


def _raise_nofile_limit():
    """Raise the process soft open-file limit to the hard limit.

    Matches the automatic behaviour of the Go and Java runtimes.
    Silently skips on non-Unix platforms where resource is unavailable.
    """
    try:
        import resource
    except ImportError:
        return  # non-Unix (e.g. Windows) — skip

    try:
        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        if soft < hard:
            # RLIM_INFINITY (9223372036854775807 on Linux) cannot be passed
            # directly to setrlimit — the kernel rejects it with OSError.
            # Cap the target at a known-safe value instead.
            if hard == resource.RLIM_INFINITY:
                target = _MAX_NOFILE
            else:
                target = min(hard, _MAX_NOFILE)
            resource.setrlimit(resource.RLIMIT_NOFILE, (target, hard))
            logging.info("Raised open-file limit from %d to %d", soft, target)
    except (ValueError, OSError) as e:
        logging.warning("Could not raise open-file limit: %s", e)
