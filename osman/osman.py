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

    def __init__(self, config: OsmanConfig = None):
        """
        Init Osman

        Parameters
        ----------
        config: OsmanConfig
            Configuration params (url, ...) of the OpenSearch instance
        """
        if not config:
            logging.info("No config provided, using a default one.")
            config = OsmanConfig(host_url="http://opensearch-node:9200")

        assert isinstance(config, OsmanConfig)
        self.config = config

        os_params = {}
        if config.auth_method == "http":
            logging.info(
                f"Initializing OpenSearch by 'http' auth method, "
                f"host:{config.opensearch_host}, \
                port:{config.opensearch_port}."
            )

            os_params["hosts"] = [config.host_url]

        elif config.auth_method == "awsauth":
            logging.info(
                f"Initializing OpenSearch by 'awsauth' auth method, "
                f"host:{config.opensearch_host}, \
                port:{config.opensearch_port}."
            )

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
            logging.info("Getting cluster settings.")
            self.client.cluster.get_settings()
        except Exception:
            logging.error("Getting cluster settings failed.")
            raise

    def create_index(self, index_name: str, index_mapping: dict = {}):
        """
        Creates an index

        Parameters
        ----------
        index_name: str
            The name of the index

        Returns
        -------
        dict
            dictionary with response
        """
        return self.client.indices.create(index_name, body=index_mapping)

    def delete_index(self, index_name: str):
        """
        Deletes an index

        Parameters
        ----------
        index_name: str
            The name of the index


        Returns
        -------
        dict
            dictionary with response
        """
        return self.client.indices.delete(index=index_name)

    def index_exists(self, index_name: str):
        """
        Checks whether an index exists.

        Parameters
        ----------
        index_name: str
            The name of the index

        Returns
        -------
        dict
            dictionary with response
        """
        return self.client.indices.exists(index_name)

    def search(self, index_name: str, search_query: dict):
        """
        Search the index with provided search query

        Parameters
        ----------
        index_name: str
            The name of the index
        search_string: dict
            Search query as dictionary {'query': {....}}

        Returns
        -------
        dict
            dictionary with response
        """
        response = self.client.search(
            body=search_query,
            index=index_name
        )
        return response

    def add_data_to_index(self, index_name: str, data: dict, refresh=False):
        """
        Bulk insert data to index.

        Parameters
        ----------
        index_name: str
            Name of the index
        data: json
            Data should have following format: [{document}, {document}, ...]
        refresh: bool
            Should the shards in OS refresh automatically?
            True hurts the cluster performance.
        """
        bulk_data = []
        for doc_id, document in enumerate(data):
            bulk_data.append({"create": {"_index": index_name, "_id": doc_id}})
            bulk_data.append(document)

        logging.info(f"Creating data in index {index_name}...")
        res = self.client.bulk(bulk_data, refresh=refresh)
        if res["errors"] is not False:
            logging.error("Creating some data failed.")
            logging.debug(f"Result: '{res}'.")
            for item in res.get('items', None):
                logging.error(
                    "error type: '{error_type}',error reason: '{reason}.'".
                    format(
                        error_type=item["create"]["error"]["type"],
                        reason=item["create"]["error"]["reason"]
                    )
                )

            raise RuntimeError("Bulk insert failed.")
        return res
