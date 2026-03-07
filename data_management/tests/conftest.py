import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_command():
    """A minimal mock of a Django management command for use in service class tests."""
    cmd = MagicMock()
    cmd.style.SUCCESS.side_effect = lambda msg: msg
    cmd.style.WARNING.side_effect = lambda msg: msg
    cmd.style.ERROR.side_effect = lambda msg: msg
    return cmd
