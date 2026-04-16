import logging

# Module-level import so tests can patch func_python._ulimit._resource directly.
# On non-Unix platforms (e.g. Windows) the resource module is unavailable;
# _resource is set to None and _raise_nofile_limit() becomes a no-op.
try:
    import resource as _resource
except ImportError:
    _resource = None

_MAX_NOFILE = 65536  # safe cap when hard == RLIM_INFINITY

_logger = logging.getLogger(__name__)


def _raise_nofile_limit():
    """Raise the process soft open-file limit to the hard limit.

    Matches the automatic behaviour of the Go and Java runtimes.
    Silently skips on non-Unix platforms where resource is unavailable.
    """
    if _resource is None:
        return  # non-Unix (e.g. Windows) — skip

    try:
        soft, hard = _resource.getrlimit(_resource.RLIMIT_NOFILE)
        if soft < hard:
            # When hard is RLIM_INFINITY the kernel rejects setting the soft
            # limit to RLIM_INFINITY without CAP_SYS_RESOURCE, so cap the
            # soft limit at a known-safe value. For finite hard limits, raise
            # the soft limit all the way to the hard limit as the Go and Java
            # runtimes do.
            target = _MAX_NOFILE if hard == _resource.RLIM_INFINITY else hard
            _resource.setrlimit(_resource.RLIMIT_NOFILE, (target, hard))
            _logger.debug("Raised open-file limit from %d to %d", soft, target)
    except (ValueError, OSError) as e:
        _logger.warning("Could not raise open-file limit: %s", e)
