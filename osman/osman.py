"""Osman -- OpenSearch Manager."""
import json
import logging
import uuid
from typing import Union

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

    diff = deepdiff.DeepDiff(script_os, script_local)
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
        os_params["timeout"] = config.timeout
        os_params["max_retries"] = config.max_retries
        os_params["retry_on_timeout"] = config.retry_on_timeout
        self.client = OpenSearch(**os_params)

        # Test the connection
        logging.info("Getting cluster settings")
        try:
            self.client.cluster.get_settings()
        except Exception:
            logging.error("Getting cluster settings failed")
            raise

    def create_index(
        self,
        name: str,
        mapping: dict = None,
        settings: dict = None,
    ) -> dict:
        """
        Create an index.

        Parameters
        ----------
        name: str
            The name of the index
        mapping: dict
            Index mapping
        settings: dict
            Index settings

        Returns
        -------
        dict
            Dictionary with response
        """
        if mapping is None:
            mapping = {"mappings": {}}
        if settings is None:
            settings = {"settings": {}}

        body = {
            "settings": settings["settings"],
            "mappings": mapping["mappings"],
        }

        return self.client.indices.create(
            index=name, body=body, ignore=[400, 404]
        )

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
        return self.client.indices.delete(index=name, ignore=[400, 404])

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

    def reindex(
        self,
        name: str,
        mapping: dict = None,
        settings: dict = None,
    ) -> dict:
        """
        Reindex with a new index mapping.

        When reindexing, a suffix [1, 2] is added to the index name.
        An index should always be referenced by its name without the suffix
        (alias).

        Parameters
        ----------
        name: str
            the name of the index
        mapping: dict
            index mapping
        settings: dict
            index settings

        Returns
        -------
        dict
            Dictionary with response
        """
        if not mapping and not settings:
            logging.warning("Mapping and settings cannot both be empty")
            return {"acknowledged": False}

        # only reindex when the index already exists
        if self.index_exists(name) is False:
            logging.warning("The index does not exist")
            return {"acknowledged": False}

        # reindexing requires suffix alternation
        suffix_to_create, suffix_to_delete = 1, 2

        os_mapping = self.client.indices.get_mapping(name).get(name)
        diffs = _compare_scripts(json.dumps(mapping), json.dumps(os_mapping))

        if diffs is None:
            logging.warning(
                "No difference betweeen OS and local source. Terminating reindexing.."
            )
            return {"acknowledged": False}

        # check which version is currently in OS (1 or 2)
        if self.index_exists(name=f"{name}-{suffix_to_create}"):
            suffix_to_delete, suffix_to_create = (
                suffix_to_create,
                suffix_to_delete,
            )

        index_to_create = f"{name}-{suffix_to_create}"
        index_to_delete = f"{name}-{suffix_to_delete}"

        # create the new index
        self.create_index(
            name=index_to_create, mapping=mapping, settings=settings
        )

        # move all the documents from the old index to the new index
        # if it fails, ensure to delete the newly created index and
        # stick to the old one
        try:
            self.client.reindex(
                {"source": {"index": name}, "dest": {"index": index_to_create}},
                wait_for_completion=True,
            )

        except exceptions.RequestError:
            self.delete_index(name=index_to_create)
            return {
                "acknowledged": False,
                "name": index_to_create,
                "alias": name,
            }

        # delete the old index
        self.delete_index(name=index_to_delete)

        # delete if index without suffix exists
        if self.index_exists(name=f"{name}"):
            self.delete_index(name=f"{name}")

        # create alias so we can call the index without the suffix
        self.client.indices.put_alias(index_to_create, name)

        # extract new settings
        os_settings = (
            self.client.indices.get_settings(name)
            .get(index_to_create, {})
            .get("settings")
        )

        return {
            "acknowledged": True,
            "name": index_to_create,
            "alias": name,
            "mapping_differences": diffs,
            "settings": os_settings,
        }

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

        # if script exists in os, compare it with the local script
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

    def debug_search_template(
        self,
        source: dict,
        index: str,
        params: dict,
        expected_ids: list = None,
    ) -> list:
        """
        Debug a search template before uploading.

        Verifies that returned id's are the same as expected.

        Parameters
        ----------
        source: dict
            search template to test
        index: str
            name of the index
        params: dict
            search template parameters {parameters: {validation parameters}
        expected_ids: list
            expected ids to be returned by search template
            optional because this check is not useful when data is large

        Returns
        -------
        list
            ids as a result from testing of search template
        """
        query = json.dumps({"source": source, "params": params})

        # run search template against the test data
        results = self.client.search_template(body=query, index=index)

        hits = results["hits"]["hits"]

        hits_cnt = len(hits)

        assert hits_cnt >= 1

        ids = [hit.get("_id") for hit in hits]

        if expected_ids is not None:
            assert set(ids) == set(expected_ids)

        return hits

    def delete_script(self, name: str) -> dict:
        """
        Delete script.

        Parameters
        ----------
        name: str
            name of script

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

        # create body to insert into OS
        body = {
            "lang": "painless",
            "source": source,
        }

        # if script ecists in os, compare it with the local script
        if script_os_res["found"]:
            diffs = _compare_scripts(
                json.dumps(body), json.dumps(script_os_res["script"])
            )
        else:
            diffs = source

        if diffs is None:
            return {"acknowledged": False}

        # upload script
        res = self.client.put_script(id=name, body={"script": body})

        if diffs:
            res["differences"] = diffs
        logging.info("Template updated!")
        return res

    def update_cluster_settings(self, settings: dict) -> dict:
        """
        Update cluster settings.

        Parameters
        ----------
        settings: dict
            A dictionary containing the cluster settings to update. This can include
            'persistent' and 'transient' settings.

        Returns
        -------
        dict
            Dictionary with the response from the OpenSearch cluster.

        Raises
        ------
        RuntimeError
            If the update fails or OpenSearch returns an error.
        """
        try:  # noqa: WPS229
            response = self.client.cluster.put_settings(body=settings)
            logging.info("Cluster settings updated successfully.")
            return response
        except exceptions.OpenSearchException as e:
            logging.error("Failed to update cluster settings: %s", e)
            raise RuntimeError(f"Failed to update cluster settings: {e}") from e

    def debug_painless_script(
        self,
        source: dict,
        index: str,
        params: dict,
        context_type: str,
        document: dict,
        expected_result: Union[int, float, bool],
    ) -> dict:
        """
        Debug a painless script before uploading.

        Verifies that the painless script returns what is expected.

        Parameters
        ----------
        source: dict
            painless script to upload
        index: str
            index name
        params: dict
            parameters to pass to painless script
        context_type: str
            context type of the painless script, should be in {'filter', 'score'}
        document: dict
            document to test the script on
        expected_result: Union[int, float, bool]
            expected return from painless script

        Returns
        -------
        dict
            dictionary with response
        """
        if context_type == "score":
            if not isinstance(expected_result, (float, int)):
                logging.warning(
                    "context_type 'score' requires 'expected_result' float or int"
                )
                return {"acknowledged": False}
        elif context_type == "filter":
            if not isinstance(expected_result, (bool)):
                logging.warning(
                    "context_type 'filter' requires 'expected_result' bool"
                )
                return {"acknowledged": False}
        else:
            logging.warning("context_type must be 'filter' or 'score'")
            return {"acknowledged": False}

        # create a json to test painless functionality
        body = json.dumps(
            {
                "script": {"source": source, "params": params["params"]},
                "context": context_type,
                "context_setup": {
                    "index": index,
                    "document": document,
                },
            }
        )

        # send API request to test validity of painless script
        try:
            res = self.client.scripts_painless_execute(body=body)
        except exceptions.RequestError:
            logging.error("Painless script execution failed")
            return {"acknowledged": False}

        if "result" in res:
            res["acknowledged"] = True

        assert res["result"] == expected_result

        return res

    def send_post_request(self, endpoint: str, payload: dict) -> dict:
        """
        Send a POST request to a specified endpoint in OpenSearch.

        Parameters
        ----------
        endpoint : str
            The API endpoint to which the POST request will be sent.
        payload : dict
            The payload for the POST request, structured as a dictionary.

        Returns
        -------
        dict
            Dictionary containing the response from the OpenSearch server.

        Raises
        ------
        RuntimeError
            If the POST request fails or OpenSearch returns an error.
        """
        try:  # noqa: WPS229
            response = self.client.transport.perform_request(
                "POST", endpoint, body=json.dumps(payload)
            )
            logging.info(f"POST request to {endpoint} successful.")
            return response
        except exceptions.OpenSearchException as e:
            logging.error(f"Failed to send POST request to {endpoint}: {e}")
            raise RuntimeError(
                f"Failed to send POST request to {endpoint}: {e}"
            ) from e

    def send_get_request(self, endpoint: str) -> dict:
        """
        Send a GET request to a specified endpoint in OpenSearch.

        Parameters
        ----------
        endpoint : str
            The API endpoint to which the GET request will be sent.

        Returns
        -------
        dict
            Dictionary containing the response from the OpenSearch server.

        Raises
        ------
        RuntimeError
            If the GET request fails or OpenSearch returns an error.
        """
        try:  # noqa: WPS229
            response = self.client.transport.perform_request("GET", endpoint)
            logging.info(f"GET request to {endpoint} successful.")
            return response
        except exceptions.OpenSearchException as e:
            logging.error(f"Failed to send GET request to {endpoint}: {e}")
            raise RuntimeError(
                f"Failed to send GET request to {endpoint}: {e}"
            ) from e

    def send_put_request(self, endpoint: str, payload: dict) -> dict:
        """
        Send a PUT request to a specified endpoint in OpenSearch.

        Parameters
        ----------
        endpoint : str
            The API endpoint to which the PUT request will be sent.
        payload : dict
            The payload for the PUT request, structured as a dictionary.

        Returns
        -------
        dict
            Dictionary containing the response from the OpenSearch server.

        Raises
        ------
        RuntimeError
            If the PUT request fails or OpenSearch returns an error.
        """
        try:  # noqa: WPS229
            json_payload = json.dumps(payload)
            response = self.client.transport.perform_request(
                "PUT", endpoint, body=json_payload
            )
            logging.info(f"PUT request to {endpoint} successful.")
            return response
        except exceptions.OpenSearchException as e:
            logging.error(f"Failed to send PUT request to {endpoint}: {e}")
            raise RuntimeError(
                f"Failed to send PUT request to {endpoint}: {e}"
            ) from e
