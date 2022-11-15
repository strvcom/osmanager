import pytest
import logging
import os
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
    o = Osman()
    assert o.config
    assert o.config.host_url == OpenSearchLocalConfig.url


def test_creating_osman_instance_with_default_config():
    """
    Test Osman client with configuration from url
    """
    o = Osman(OsmanConfig(host_url=OpenSearchLocalConfig.url))
    assert o.config
    assert o.config.host_url == OpenSearchLocalConfig.url


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
    o = Osman(OsmanConfig(**local_config))
    assert o.config
    assert o.client


def test_connectig_osman_to_opensearch_from_environment_variables():
    """
    Test connectig Osman to Opensearch instance configured by
    environment variables

    NOTE: For the future we will add complex testing of reading environment --
    i.e. setting the environment during the test setup (pytest fixtures)
    """
    env_auth_method = os.environ.get("AUTH_METHOD")
    logging.info(f"Testing auth method:'{env_auth_method}'")
    if not env_auth_method:
        logging.warning("No auth method provided by the environment,"
                        " passing without testing")
        return
    logging.info("Testing Osman initialized by environment variables")
    config = OsmanConfig()
    logging.info(f"Host url from env config: '{config.host_url}'")
    o = Osman(config)
    assert o.config
    assert o.client
