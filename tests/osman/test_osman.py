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

def test_connectig_osman_to_opensearch_from_environment_variables():
    """
    Test connectig Osman to Opensearch instance configured by
    environment variables
    """
    logging.info("Testing auth method:" + os.environ.get("AUTH_METHOD", "--"))
    o = Osman(OsmanConfig())
    assert o.config
    assert o.client

