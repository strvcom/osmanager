#!/usr/bin/env python
# -*- coding: utf-8 -*-

from opensearchpy import OpenSearch
import logging

class OsmanConfig:
    """
    Configuration holder

    Attributes
    ----------
    host_url: str
        Url of the OpenSearch instance
    
    In the future there will be stored additionals attributes like:
        - user, secrets, aws setup, ...
    """
    def __init__(self, host_url="http://opensearch-node:9200"):
        self.host_url = host_url

class Osman:
    """
    Generic OpenSearch helper class
    
    Attributes
    ----------
    client: OpenSearch
        OpenSearch initialized client
    
    """

    def __init__(self, config=None):
        """
        Init Osman

        Parameters
        ----------
        config: OsmanConfig
            Configuration params (url, ...) of the OpenSearch instance
        """
        if not config:
            logging.info("No config provided, using default one")
            config = OsmanConfig()

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
