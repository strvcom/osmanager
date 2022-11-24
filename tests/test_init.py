import os


def test_environment():
    """Environment variables should be deleted in conftest.py ."""
    assert os.environ.get("OPENSEARCH_HOST") is None
