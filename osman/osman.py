"""Osman -- OpenSearch Manager."""
import json
import logging
import uuid

import deepdiff
from opensearchpy import OpenSearch, RequestsHttpConnection, exceptions, helpers
from requests_aws4auth import AWS4Auth

from osman.config import OsmanConfig


def _bulk_json_data(index_name: str, documents: list, id_key: str = None):
    """
    Generate data dictionary.

    Helper method for add_data_to_index.

    Parameters
    ----------
    index_name: str
        name of the index
    documents: list
        iterable yielding documents. TODO iterable instead of list?
    id_key: str
        key from a document used for indexing or None
    Yields
    ------
    dict
        dictionary with _index (index_name), _id (generated id),
            _source (one document)
    """
    for doc in documents:
        index_id = doc[id_key] if id_key else uuid.uuid4()
        yield {"_index": index_name, "_id": index_id, "_source": doc}


def _compare_scripts(script_local: str, script_os: str) -> dict:
    """
    Compare two scripts and return the differences.

    Helper method for upload_search_template.

    Parameters
    ----------
    script_local: str
        json string of the local script
    script_os: str
        json string of the script in os
    Returns
    ------
    dict
        dictionary containing the differences between the two scripts
    """
    script_local = json.loads(script_local)
    script_os = json.loads(script_os)

    if script_local == script_os:
        logging.info("Local script and OS script are equal.")
        return None

    diff = deepdiff.DeepDiff(script_local, script_os)
    logging.info("Local script and OS script are not equal.")
    return diff


class Osman(object):
    """
    Generic OpenSearch helper class.

    Attributes
    ----------
    client: OpenSearch
        OpenSearch initialized client
    """

    def __init__(self, config: OsmanConfig = None):
        """
        Init Osman.

        Parameters
        ----------
        config: OsmanConfig
            Configuration params (url, ...) of the OpenSearch instance
        Raises
        ------
        AssertionError
            in case of malformed config.auth_method
        Exception
            re-raises exception when self.client.cluster.get_settings()
            is not succesful.
        """
        if not config:
            logging.info("No config provided, using a default one")
            config = OsmanConfig(host_url="http://opensearch-node:9200")

        assert isinstance(config, OsmanConfig)
        self.config = config

        os_params = {}
        if config.auth_method == "http":
            logging.info(
                "Initializing OpenSearch by 'http' auth method, "
                + "host: %s, port: %s",
                {config.opensearch_host},
                {config.opensearch_port},
            )

            os_params["hosts"] = [config.host_url]

        elif config.auth_method == "awsauth":
            logging.info(
                "Initializing OpenSearch by 'awsauth' auth method, "
                + "host: %s, port: %s",
                {config.opensearch_host},
                {config.opensearch_port},
            )

            os_params["http_auth"] = AWS4Auth(
                config.aws_access_key_id,
                config.aws_secret_access_key,
                config.aws_region,
                config.aws_service,
            )
            os_params["hosts"] = [
                {"host": config.opensearch_host, "port": config.opensearch_port}
            ]
        else:
            # We should never get here
            raise AssertionError()

        os_params["use_ssl"] = config.opensearch_ssl_enabled
        os_params["http_compress"] = True
        os_params["connection_class"] = RequestsHttpConnection
        self.client = OpenSearch(**os_params)

        # Test the connection
        logging.info("Getting cluster settings")
        try:
            self.client.cluster.get_settings()
        except Exception:
            logging.error("Getting cluster settings failed")
            raise

    def create_index(self, name: str, mapping: dict = None) -> dict:
        """
        Create an index.

        Parameters
        ----------
        name: str
            The name of the index
        mapping: dict
            Index mapping
        Returns
        -------
        dict
            Dictionary with response
        """
        return self.client.indices.create(index=name, body=mapping)

    def delete_index(self, name: str) -> dict:
        """
        Delete an index.

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
        Check whether an index exists.

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
        Search the index with provided search query.

        Parameters
        ----------
        name: str
            The name of the index
        search_query: dict
            Search query as dictionary {'query': {....}}
        Returns
        -------
        dict
            Dictionary with response
        """
        return self.client.search(body=search_query, index=name)

    def add_data_to_index(
        self,
        index_name: str,
        documents: list,
        id_key: str = None,
        refresh: bool = False,
    ) -> dict:
        """
        Bulk insert data to index.

        Parameters
        ----------
        index_name: str
            Name of the index
        documents: list
            Documents in the following format: [{document}, {document}, ...]
        id_key: str
            Key from the document used as id for indexing. If None uuid4
            is created as id.
        refresh: bool
            Should the shards in OS refresh automatically?
            True hurts the cluster performance
        Returns
        -------
        dict
            Dictionary with response
        Raises
        ------
        RuntimeError
            if the helpers.bul call fails.
        """
        logging.info("Creating data in index '%s'...", index_name)
        try:
            docs_inserted, _ = helpers.bulk(
                self.client,
                _bulk_json_data(
                    index_name=index_name, documents=documents, id_key=id_key
                ),
                refresh=refresh,
                stats_only=True,
            )
        except Exception as exc:
            logging.debug("Failed: '%s'", exc)
            raise RuntimeError("Bulk insert failed") from exc

        return {
            "acknowledged": True,
            "documents_inserted": docs_inserted,
            "index": index_name,
        }

    def upload_search_template(
        self, source: dict, name: str, index: str, params: dict
    ) -> dict:
        """
        Upload (or update) search template.

        Parameters
        ----------
        source: dict
            search template to upload
        name: str
            name of the search template
        index: str
            name of the index
        params: dict
            search template parameters {parameters: {validation parameters}
        Returns
        -------
        dict
            dictionary with response
        """
        query = json.dumps({"source": source, "params": params})

        # run search template against the test data
        result = self.client.search_template(body=query, index=index)

        hits_cnt = len(result["hits"]["hits"])

        assert hits_cnt >= 1

        # check if script already exists in os
        script_os_res = self.client.get_script(id=name, ignore=[400, 404])

        # if script ecists in os, compare it with the local script
        if script_os_res["found"]:

            diffs = _compare_scripts(
                json.dumps(source), script_os_res["script"]["source"]
            )
        else:
            diffs = source

        if diffs is None:
            return {"acknowledged": False}

        # upload search template
        res = self.client.put_script(
            id=name,
            body={
                "script": {
                    "lang": "mustache",
                    "source": source,
                }
            },
        )

        if diffs:
            res["differences"] = diffs
        logging.info("Template updated!")
        return res

    def delete_script(self, name: str) -> dict:
        """
        Delete search template or painless script.

        Parameters
        ----------
        name: str
            name of search template or painless script.
        Returns
        -------
        dict
            Dictionary with response
        """
        try:
            res = self.client.delete_script(id=name)
        except exceptions.NotFoundError:
            res = {"acknowledged": False}

        return res

    def upload_painless_script(self, source: dict, name: str) -> dict:
        """
        Upload (or update) painless script.

        Parameters
        ----------
        source: dict
            search template to upload
        name: str
            name of the search template
        Returns
        -------
        dict
            dictionary with response
        """
        # check if script already exists in os
        script_os_res = self.client.get_script(id=name, ignore=[400, 404])

        # if script ecists in os, compare it with the local script
        if script_os_res["found"]:

            diffs = _compare_scripts(
                json.dumps(source), script_os_res["script"]
            )
        else:
            diffs = source

        if diffs is None:
            return {"acknowledged": False}

        # upload script
        res = self.client.put_script(
            id=name,
            body={
                "script": {
                    "lang": "painless",
                    "source": source,
                }
            },
        )

        if diffs:
            res["differences"] = diffs
        logging.info("Template updated!")
        return res
