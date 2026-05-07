import logging
import resource
from unittest.mock import MagicMock, patch


def _make_resource(soft, hard, rlim_infinity=None):
    """Build a minimal mock of the resource module."""
    mock = MagicMock(spec=resource)
    mock.RLIMIT_NOFILE = resource.RLIMIT_NOFILE
    mock.RLIM_INFINITY = rlim_infinity if rlim_infinity is not None else resource.RLIM_INFINITY
    mock.getrlimit.return_value = (soft, hard)
    return mock


def _call_with_resource(mock_resource):
    """Call _raise_nofile_limit() with the given resource mock patched in place."""
    with patch("func_python._ulimit._resource", mock_resource):
        from func_python._ulimit import _raise_nofile_limit
        _raise_nofile_limit()
    return mock_resource


# ---------------------------------------------------------------------------
# Unit tests for _raise_nofile_limit()
# ---------------------------------------------------------------------------

def test_raises_soft_limit_to_hard():
    """When soft < hard (finite), setrlimit is called with the full hard value."""
    mock_resource = _make_resource(soft=1024, hard=4096)
    _call_with_resource(mock_resource)
    mock_resource.setrlimit.assert_called_once_with(
        resource.RLIMIT_NOFILE, (4096, 4096)
    )


def test_raises_soft_limit_to_hard_above_65536():
    """Hard limits above 65536 must be honoured in full, not capped."""
    mock_resource = _make_resource(soft=1024, hard=131072)
    _call_with_resource(mock_resource)
    mock_resource.setrlimit.assert_called_once_with(
        resource.RLIMIT_NOFILE, (131072, 131072)
    )


def test_no_change_when_soft_equals_hard():
    """When soft == hard, setrlimit must not be called."""
    mock_resource = _make_resource(soft=4096, hard=4096)
    _call_with_resource(mock_resource)
    mock_resource.setrlimit.assert_not_called()


def test_rlim_infinity_capped_at_max():
    """When hard == RLIM_INFINITY the soft limit must be capped at _MAX_NOFILE."""
    from func_python._ulimit import _MAX_NOFILE
    rlim_infinity = resource.RLIM_INFINITY
    mock_resource = _make_resource(soft=1024, hard=rlim_infinity,
                                   rlim_infinity=rlim_infinity)
    _call_with_resource(mock_resource)
    mock_resource.setrlimit.assert_called_once_with(
        resource.RLIMIT_NOFILE, (_MAX_NOFILE, rlim_infinity)
    )


def test_import_error_is_silently_skipped():
    """When resource is unavailable (non-Unix), no exception is raised."""
    with patch("func_python._ulimit._resource", None):
        from func_python._ulimit import _raise_nofile_limit
        _raise_nofile_limit()  # must not raise


def test_os_error_logs_warning(caplog):
    """When setrlimit raises OSError, a warning is logged and no exception propagates."""
    mock_resource = _make_resource(soft=1024, hard=4096)
    mock_resource.setrlimit.side_effect = OSError("operation not permitted")
    with caplog.at_level(logging.WARNING, logger="func_python._ulimit"):
        _call_with_resource(mock_resource)
    assert any("Could not raise open-file limit" in r.message for r in caplog.records)


def test_value_error_logs_warning(caplog):
    """When setrlimit raises ValueError, a warning is logged and no exception propagates."""
    mock_resource = _make_resource(soft=1024, hard=4096)
    mock_resource.setrlimit.side_effect = ValueError("invalid argument")
    with caplog.at_level(logging.WARNING, logger="func_python._ulimit"):
        _call_with_resource(mock_resource)
    assert any("Could not raise open-file limit" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# Wire-up tests: verify serve() in http.py and cloudevent.py call the helper
# ---------------------------------------------------------------------------

def test_http_serve_calls_raise_nofile_limit():
    """serve() in http.py must call _raise_nofile_limit() before doing anything else."""
    with patch("func_python.http._raise_nofile_limit") as mock_fn:
        with patch("func_python.http.ASGIApplication") as mock_app:
            mock_app.return_value.serve.return_value = None
            from func_python.http import serve

            async def handle(scope, receive, send):
                pass

            serve(handle)

    mock_fn.assert_called_once()


def test_cloudevent_serve_calls_raise_nofile_limit():
    """serve() in cloudevent.py must call _raise_nofile_limit() before doing anything else."""
    with patch("func_python.cloudevent._raise_nofile_limit") as mock_fn:
        with patch("func_python.cloudevent.ASGIApplication") as mock_app:
            mock_app.return_value.serve.return_value = None
            from func_python.cloudevent import serve

            async def handle(scope, receive, send):
                pass

            serve(handle)

    mock_fn.assert_called_once()
