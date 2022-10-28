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
    TODO
    user, secrets, aws setup
    """
    def __init__(self, host_url='http://opensearch-node:9200'):
        self.host_url = host_url

class Osman:
    """
    Generic OpenSearch helper class
    
    Attributes
    ----------
    client: OpenSearch
        OpenSearch initialized client
    
    """

    #########
    def __init__(self, config=None):
        """
        Init Osman

        Parameters
        ----------
        config: OsmanConfig
            Configuration params (url, ...) of the OpenSearch instance
        """
        if config is None:
            logging.info('No config provided, using default one')
            config = OsmanConfig()

        logging.info(f'Initializing OpenSearch client with {config.host_url}')
        self.client = OpenSearch(
            hosts=[config.host_url],
            use_ssl=False,
        )
        try:
            # Test the connection
            logging.info("Getting cluster settings")
            self.client.cluster.get_settings()
        except Exception:
            #TODO
            logging.error(f"Getting cluster settings failed")
            raise

    #########
    def add_data_to_index(self, index_name, data):
        """
        Bulk insert data to index.

        Parameters
        ----------
        index_name: str
            Name of the index
        data: json
            Data should have following format: [{document}, {document}, ...]
        """
        bulk_data = []
        for doc_id, document in enumerate(data):
            bulk_data.append({"create": {"_index": index_name, '_id': doc_id}})
            bulk_data.append(document)

        logging.info(f"Creating data in index {index_name}...")
        res = self.client.bulk(bulk_data)
        if res['errors'] != False:
            logging.error("Creating some data failed")
            logging.debug(f"Result: '{res}'")
            for item in res.get('items', None):
                logging.error("error type: '{error_type}'".format(
                    error_type=item['create']['error']['type']
                ))
                logging.error("error reason: '{reason}'".format(
                    reason=item['create']['error']['reason']
                ))
            #TODO
            raise RuntimeError('Bulk insert failed')
        return res
