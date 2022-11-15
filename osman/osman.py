import os
import uuid
import logging
import json

from pathlib import Path
from opensearchpy import OpenSearch, RequestsHttpConnection, helpers
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
            logging.info("No config provided, using a default one")
            config = OsmanConfig(host_url="http://opensearch-node:9200")

        assert isinstance(config, OsmanConfig)
        self.config = config

        os_params = {}
        if config.auth_method == "http":
            logging.info(
                f"Initializing OpenSearch by 'http' auth method, "
                f"host:{config.opensearch_host}, "
                f"port:{config.opensearch_port}"
            )

            os_params["hosts"] = [config.host_url]

        elif config.auth_method == "awsauth":
            logging.info(
                f"Initializing OpenSearch by 'awsauth' auth method, "
                f"host:{config.opensearch_host}, "
                f"port:{config.opensearch_port}"
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
            logging.info("Getting cluster settings")
            self.client.cluster.get_settings()
        except Exception:
            logging.error("Getting cluster settings failed")
            raise

    def create_index(self, name: str, mapping: dict = {}) -> dict:
        """
        Creates an index

        Parameters
        ----------
        name: str
            The name of the index

        Returns
        -------
        dict
            Dictionary with response
        """

        return self.client.indices.create(index=name, body=mapping)

    def delete_index(self, name: str) -> dict:
        """
        Deletes an index

        Parameters
        ----------
        name: str
            The name of the index

        Returns
        -------
        dict
            Dictionary with response
        """

        return self.client.indices.delete(index=name)

    def index_exists(self, name: str) -> dict:
        """
        Checks whether an index exists

        Parameters
        ----------
        name: str
            The name of the index

        Returns
        -------
        dict
            Dictionary with response
        """

        return self.client.indices.exists(index=name)

    def search_index(self, name: str, search_query: dict) -> dict:
        """
        Search the index with provided search query

        Parameters
        ----------
        name: str
            The name of the index
        search_string: dict
            Search query as dictionary {'query': {....}}

        Returns
        -------
        dict
            Dictionary with response
        """

        return self.client.search(
            body=search_query,
            index=name
        )

    def _bulk_json_data(self, index_name: str, documents: list = None):
        """
        Generate data from a json file

        Parameters
        ----------
        index_name: str
            The name of the index to store the data
        documents: list
            Documents should have following format: [{document}, {document}, ...]

        """

        for doc in documents:

            yield {
                "_index": index_name,
                "_id": uuid.uuid4(),
                "_source": doc
            }

    def add_data_to_index(
        self,
        name: str,
        documents: list,
        refresh: bool = False
    ) -> dict:
        """
        Bulk insert data to index

        Parameters
        ----------
        name: str
            Name of the index
        documents: json
            Documents should have following format: [{document}, {document}, ...]
        refresh: bool
            Should the shards in OS refresh automatically?
            True hurts the cluster performance

        Returns
        -------
        dict
            Dictionary with response
        """

        logging.info(f"Creating data in index {name}...")

        try:
            succes, _ = helpers.bulk(
                self.client,
                self._bulk_json_data(
                    index_name=name, documents=documents
                ), refresh=refresh, stats_only=False
            )
        except Exception as e:
            logging.debug(f"Failed: '{e}'")
            raise RuntimeError("Bulk insert failed")

        res = {
            "acknowledged": True,
            "documents_inserted": succes,
            "index": name
        }
        return res
