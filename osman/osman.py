#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

from .config import OsmanConfig

class Osman:
    """
    Generic OpenSearch helper class
    
    Attributes
    ----------
    client: OpenSearch
        OpenSearch initialized client
    
    """

    def __init__(self, config: OsmanConfig=None):
        """
        Init Osman

        Parameters
        ----------
        config: OsmanConfig
            Configuration params (url, ...) of the OpenSearch instance
        """
        if not config:
            logging.info("No config provided, using a default one")
            config = OsmanConfig(host_url = "http://opensearch-node:9200")

        assert(isinstance(config, OsmanConfig))
        self.config = config

        os_params = {}
        if config.auth_method == "http":
            logging.info(f"Initializing OpenSearch by 'http' auth method, "
                f"host:{config.opensearch_host}, port:{config.opensearch_port}")

            os_params["hosts"] = [config.host_url]

        elif config.auth_method == "awsauth":
            logging.info(f"Initializing OpenSearch by 'awsauth' auth method, "
                f"host:{config.opensearch_host}, port:{config.opensearch_port}")

            os_params["http_auth"] = AWS4Auth(
                    config.aws_access_key_id,
                    config.aws_secret_access_key,
                    config.aws_region,
                    config.aws_service
                )
            os_params["hosts"] = [{
                    "host": config.opensearch_host,
                    "port": config.opensearch_port
                }]
        else:
            # We should never get here
            assert False

        os_params["use_ssl"] = config.opensearch_ssl_enabled
        os_params["http_compress"] = True
        os_params["connection_class"] = RequestsHttpConnection
        self.client = OpenSearch(**os_params)

        try:
            # Test the connection
            logging.info("Getting cluster settings")
            self.client.cluster.get_settings()
        except Exception:
            logging.error("Getting cluster settings failed")
            raise
