#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
from opensearchpy import OpenSearch
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

        logging.info(f"Initializing OpenSearch client with {config.host_url}")
        self.client = OpenSearch(
            hosts=[config.host_url],
            use_ssl=False,
        )
        try:
            # Test the connection
            logging.info("Getting cluster settings")
            self.client.cluster.get_settings()
        except Exception:
            logging.error("Getting cluster settings failed")
            raise
