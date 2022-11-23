import logging
import os

import pytest


def test_environment():
    """
    Environment variables should be deleted in conftest.py
    """
    assert os.environ.get("OPENSEARCH_HOST") is None
