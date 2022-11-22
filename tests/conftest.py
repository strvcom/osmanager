"""
Tests initialization and setup
"""
import logging
import os
import sys
import pytest

# This ugly hack allows importing 'osman.environment' without initializing
# osman package (i.e. without executing osman/__init__.py)
# We need to prevent initializing OsmanConfig class
ORIG_SYS_PATH=sys.path.copy()
sys.path.append(os.path.join(".", "osman"))
from environment import OSMAN_ENVIRONMENT_VARS
sys.path = ORIG_SYS_PATH

# Dictionary to save deleted environment variables
OSMAN_ENV_VARS_SAVED = {}

def pytest_sessionstart(session):
    """
    Initialize pytest, delete and save Osman's environment variables
    """
    logging.info("Starting: '%s'", __file__)

    # The following can't be done through fixtures, it has to be called
    # before any 'import osman'
    logging.info("Deleting Osman environment variables")
    for variable in OSMAN_ENVIRONMENT_VARS + ["AWS_USER", "AWS_SECRET"]:
        if os.environ.get(variable) is None:
            continue
        OSMAN_ENV_VARS_SAVED[variable] = os.environ.pop(variable)
    
    pytest.OSMAN_ENV_VARS_SAVED = OSMAN_ENV_VARS_SAVED
