import importlib
import logging
import sys
import unittest
from unittest.mock import MagicMock, patch, call


def _load_ulimit(mock_resource=None):
    """Import (or reload) _ulimit with an optional resource module mock."""
    if mock_resource is not None:
        with patch.dict(sys.modules, {"resource": mock_resource}):
            import func_python._ulimit as ulimit
            importlib.reload(ulimit)
    else:
        import func_python._ulimit as ulimit
        importlib.reload(ulimit)
    return ulimit


class TestRaiseNofileLimit(unittest.TestCase):

    def _make_resource(self, soft, hard, rlim_infinity=None):
        """Build a minimal mock of the resource module."""
        mock_resource = MagicMock()
        mock_resource.RLIMIT_NOFILE = 7  # any constant
        mock_resource.getrlimit.return_value = (soft, hard)
        mock_resource.RLIM_INFINITY = (
            rlim_infinity if rlim_infinity is not None else 9223372036854775807
        )
        return mock_resource

    def test_raises_soft_limit_to_hard(self):
        """When soft < hard, setrlimit is called with the target value."""
        mock_resource = self._make_resource(soft=1024, hard=4096)
        ulimit = _load_ulimit(mock_resource)

        with patch.dict(sys.modules, {"resource": mock_resource}):
            ulimit._raise_nofile_limit()

        mock_resource.setrlimit.assert_called_once_with(
            mock_resource.RLIMIT_NOFILE, (4096, 4096)
        )

    def test_no_change_when_soft_equals_hard(self):
        """When soft == hard, setrlimit must not be called."""
        mock_resource = self._make_resource(soft=4096, hard=4096)
        ulimit = _load_ulimit(mock_resource)

        with patch.dict(sys.modules, {"resource": mock_resource}):
            ulimit._raise_nofile_limit()

        mock_resource.setrlimit.assert_not_called()

    def test_rlim_infinity_capped_at_max(self):
        """When hard == RLIM_INFINITY the target must be capped at _MAX_NOFILE."""
        RLIM_INFINITY = 9223372036854775807
        mock_resource = self._make_resource(soft=1024, hard=RLIM_INFINITY,
                                            rlim_infinity=RLIM_INFINITY)
        ulimit = _load_ulimit(mock_resource)

        with patch.dict(sys.modules, {"resource": mock_resource}):
            ulimit._raise_nofile_limit()

        mock_resource.setrlimit.assert_called_once_with(
            mock_resource.RLIMIT_NOFILE, (ulimit._MAX_NOFILE, RLIM_INFINITY)
        )

    def test_import_error_is_silently_skipped(self):
        """When resource is unavailable (non-Unix), no exception is raised."""
        with patch.dict(sys.modules, {"resource": None}):
            import func_python._ulimit as ulimit
            importlib.reload(ulimit)
            # Should complete without raising anything
            ulimit._raise_nofile_limit()

    def test_os_error_logs_warning(self, caplog=None):
        """When setrlimit raises OSError, a warning is logged and no exception propagates."""
        mock_resource = self._make_resource(soft=1024, hard=4096)
        mock_resource.setrlimit.side_effect = OSError("operation not permitted")
        ulimit = _load_ulimit(mock_resource)

        with patch.dict(sys.modules, {"resource": mock_resource}):
            with self.assertLogs(level=logging.WARNING) as log_ctx:
                ulimit._raise_nofile_limit()

        self.assertTrue(
            any("Could not raise open-file limit" in msg for msg in log_ctx.output)
        )

    def test_value_error_logs_warning(self):
        """When setrlimit raises ValueError, a warning is logged and no exception propagates."""
        mock_resource = self._make_resource(soft=1024, hard=4096)
        mock_resource.setrlimit.side_effect = ValueError("invalid argument")
        ulimit = _load_ulimit(mock_resource)

        with patch.dict(sys.modules, {"resource": mock_resource}):
            with self.assertLogs(level=logging.WARNING) as log_ctx:
                ulimit._raise_nofile_limit()

        self.assertTrue(
            any("Could not raise open-file limit" in msg for msg in log_ctx.output)
        )


if __name__ == "__main__":
    unittest.main()
