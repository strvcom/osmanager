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
def pytest_configure():
    """
    Propagate global variable to the tests.
    """
    pytest.OSMAN_ENV_VARS_SAVED = OSMAN_ENV_VARS_SAVED

def save_and_delete_osman_environment_vars():
    """
    Delete Osman's variables from the environment.
    """
    logging.info("Deleting Osman environment variables")
    for variable in OSMAN_ENVIRONMENT_VARS + ["AWS_USER", "AWS_SECRET"]:
        if os.environ.get(variable, None) is None:
            continue
        OSMAN_ENV_VARS_SAVED[variable] = os.environ.pop(variable)

@pytest.fixture
def save_and_delete_osman_environment_vars_fixture():
    """
    Pytest fixture, workaround as fixtures can's be called directly.
    """
    save_and_delete_osman_environment_vars()

logging.info("Starting: '%s'", __file__)
# This can't be done through fixtures, it has to be called
# before any 'import osman'
save_and_delete_osman_environment_vars()
