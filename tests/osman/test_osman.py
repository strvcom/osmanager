import pytest
import logging
import os

from osman import Osman, OsmanConfig

def test_creating_osman_instance_with_no_config():
    """
    Test Osman client with no configuration
    """
    o = Osman()
    assert o.config
    assert o.config.host_url == "http://opensearch-node:9200"

def test_creating_osman_instance_with_default_config():
    """
    Test Osman client with configuration from url
    """
    o = Osman(OsmanConfig(host_url="http://opensearch-node:9200"))
    assert o.config
    assert o.config.host_url == "http://opensearch-node:9200"


def test_connectig_osman_to_local_opensearch():
    """
    Test connectig Osman to a local Opensearch instance
    """
    o = Osman(OsmanConfig(
                auth_method="http",
                opensearch_host="opensearch-node",
                opensearch_port=9200,
                opensearch_ssl_enabled=False,
            ))
    assert o.config
    assert o.client

def test_connectig_osman_to_opensearch_from_environment_variables():
    """
    Test connectig Osman to Opensearch instance configured by
    environment variables
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
