import pytest
import logging

from osman.osman import Osman, OsmanConfig

def test_creating_osman_instance():
    """
    Test two osman clients:
    - a client with no configuration
    - a client with default configuration
    """
    Osman()
    Osman(OsmanConfig())
