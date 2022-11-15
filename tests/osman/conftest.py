import logging
import os
import pytest

# NOTE: We can't import osman.config here, the import would
#       initialize OsmanConfig class
OSMAN_ENV_VARS = [
    "OPENSEARCH_HOST",
    "OPENSEARCH_PORT",
    "OPENSEARCH_SSL_ENABLED",
    "OPENSEARCH_USER",
    "OPENSEARCH_SECRET",
    "AWS_USER",
    "AWS_SECRET",
    "AUTH_METHOD",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_REGION",
    "AWS_SERVICE",
]
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
    for variable in OSMAN_ENV_VARS:
        if os.environ.get(variable, None) == None:
            continue
        OSMAN_ENV_VARS_SAVED[variable] = os.environ.pop(variable)

@pytest.fixture
def save_and_delete_osman_environment_vars_fixture():
    """
    Pytest fixture, workaround as fixtures can's be called directly.
    """
    save_and_delete_osman_environment_vars()

logging.info("Starting: '%s'" % __file__)
# This can't be done through fixtures, it has to be called
# before any 'import osman'
save_and_delete_osman_environment_vars()
