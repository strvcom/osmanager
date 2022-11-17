"""
Test Osman class initialization
"""
import logging
import os
import pytest
from parameterized import parameterized

from osman import Osman, OsmanConfig


class OpenSearchLocalConfig:
    """
    Config holder for local OpenSearch instance

    """
    url = "http://opensearch-node:9200"
    auth_method = "http"
    host = "opensearch-node"
    port = 9200
    ssl_enabled = False


def test_creating_osman_instance_with_no_config():
    """
    Test Osman client with no configuration
    """
    os_man = Osman()
    assert os_man.config
    assert os_man.config.host_url == OpenSearchLocalConfig.url


def test_creating_osman_instance_with_default_config():
    """
    Test Osman client with configuration from url
    """
    os_man = Osman(OsmanConfig(host_url=OpenSearchLocalConfig.url))
    assert os_man.config
    assert os_man.config.host_url == OpenSearchLocalConfig.url


@parameterized.expand([(
    "test local instance",
    {
        "auth_method": OpenSearchLocalConfig.auth_method,
        "opensearch_host": OpenSearchLocalConfig.host,
        "opensearch_port": OpenSearchLocalConfig.port,
        "opensearch_ssl_enabled": OpenSearchLocalConfig.ssl_enabled,
    }
)])
def test_connection_to_local_opensearch(_, local_config: dict):
    """
    Test connection to a local Opensearch instance
    """
    os_man = Osman(OsmanConfig(**local_config))
    assert os_man.config
    assert os_man.client

def test_connectig_osman_to_opensearch_from_environment_variables(monkeypatch):
    """
    Test connectig Osman to Opensearch instance configured by
    environment variables
    """

    # The environment variables were deleted in conftest.py, restore it
    for variable, value in pytest.OSMAN_ENV_VARS_SAVED.items():
        monkeypatch.setenv(variable, value)

    env_auth_method = os.environ.get("AUTH_METHOD")
    logging.info("Testing auth method:'%s'", env_auth_method)
    if not env_auth_method:
        logging.warning("No auth method provided by the environment,"
                        " passing without testing")
        return

    logging.info("Testing Osman initialized by environment variables")
    # Use some host_url to create instance
    config = OsmanConfig(host_url="http://example.com")

    # Overwrite config attributes from the environment
    config._reload_defaults_from_env()

    logging.info("OpenSearch host from env config: '%s'",
        {config.opensearch_host})
    os_man = Osman(config)
    assert os_man.config
    assert os_man.client
    assert os_man.config.auth_method == env_auth_method
    assert os_man.config.opensearch_host == \
        pytest.OSMAN_ENV_VARS_SAVED["OPENSEARCH_HOST"]
