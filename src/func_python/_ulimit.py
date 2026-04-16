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
            # When hard is RLIM_INFINITY the kernel rejects setting the soft
            # limit to RLIM_INFINITY without CAP_SYS_RESOURCE, so cap the
            # soft limit at a known-safe value. For finite hard limits, raise
            # the soft limit all the way to the hard limit as the Go and Java
            # runtimes do.
            if hard == resource.RLIM_INFINITY:
                target = _MAX_NOFILE
            else:
                target = hard
            resource.setrlimit(resource.RLIMIT_NOFILE, (target, hard))
            logging.info("Raised open-file limit from %d to %d", soft, target)
    except (ValueError, OSError) as e:
        logging.warning("Could not raise open-file limit: %s", e)
