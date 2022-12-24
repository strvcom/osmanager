"""Test Osman class initialization."""
import json
import logging
import os
from dataclasses import dataclass

import pytest
from parameterized import parameterized

from osman import Osman, OsmanConfig


@dataclass
class OpenSearchLocalConfig(object):
    """Config holder for local OpenSearch instance."""

    url = "http://opensearch-node:9200"
    auth_method = "http"
    host = "opensearch-node"
    port = 9200
    ssl_enabled = False


# Index mapping for testing documents
INDEX_MAPPING = {
    "mappings": {
        "properties": {
            "age": {"type": "integer"},
            "id": {"type": "integer"},
            "name": {"type": "text"},
            "container": {"type": "integer"},
        }
    }
}

# Osman instance
OS_MAN = Osman(OsmanConfig(host_url=OpenSearchLocalConfig.url))

# Parameters for index_handler fixture
INDEX_HANDLER_FIXTURE_PARAMS = {
    "argnames": "index_handler",
    "argvalues": [{"mapping": INDEX_MAPPING, "os_man": OS_MAN}],
    "indirect": True,
}


def test_creating_osman_instance_with_no_config():
    """Test Osman client with no configuration."""
    os_man = Osman()
    assert os_man.config
    assert os_man.config.host_url == OpenSearchLocalConfig.url


def test_osman_instance_with_default_config():
    """Test Osman client with configuration from url."""
    os_man = Osman(OsmanConfig(host_url=OpenSearchLocalConfig.url))
    assert os_man.config
    assert os_man.config.host_url == OpenSearchLocalConfig.url


@parameterized.expand(
    [
        (
            "test local instance",
            {
                "auth_method": OpenSearchLocalConfig.auth_method,
                "opensearch_host": OpenSearchLocalConfig.host,
                "opensearch_port": OpenSearchLocalConfig.port,
                "opensearch_ssl_enabled": OpenSearchLocalConfig.ssl_enabled,
            },
        )
    ]
)
def test_connection_to_local_opensearch(_, local_config: dict):
    """Test connection to a local Opensearch instance."""
    os_man = Osman(OsmanConfig(**local_config))
    assert os_man.config
    assert os_man.client


def test_init_and_connectig_from_environment(monkeypatch):
    """Connectig Osman to Opensearch configured by environment variables."""
    # The environment variables were deleted in conftest.py, restore it
    for variable, value in pytest.OSMAN_ENV_VARS_SAVED.items():
        monkeypatch.setenv(variable, value)

    env_auth_method = os.environ.get("AUTH_METHOD")
    logging.info("Testing auth method:'%s'", env_auth_method)
    if not env_auth_method:
        logging.warning(
            "No auth method provided by the environment,"
            + " passing without testing"
        )
        return

    logging.info("Testing Osman initialized by environment variables")
    config = OsmanConfig(host_url="http://example.com")

    # Overwrite config attributes from the environment
    config._reload_defaults_from_env()  # noqa: WPS437

    logging.info(
        "OpenSearch host from env config: '%s'", {config.opensearch_host}
    )
    os_man = Osman(config)
    assert os_man.config
    assert os_man.client
    assert os_man.config.auth_method == env_auth_method
    assert os_man.config.opensearch_host == os.environ["OPENSEARCH_HOST"]


def get_ids_from_response(response):
    """Extract id's from OpenSearch response dict (index search)."""
    if "hits" not in response:
        logging.error("Missing `hits` in response")
        return None

    if "hits" not in response["hits"]:
        logging.error("Missing `hits` in response['hits']")
        return None

    if not len(response["hits"]["hits"]):
        logging.warning("No search results")
        return []

    if "id" not in response["hits"]["hits"][0]["_source"]:
        logging.error("Missing `post_id` in documents")
        return None

    return [document["_source"]["id"] for document in response["hits"]["hits"]]


def test_index_manipulation(random_index_name):
    """Test create_index/index_exists/delete_index."""
    logging.info("Testing with index name '%s'", random_index_name)

    os_man = OS_MAN
    res = os_man.create_index(name=random_index_name)
    assert res
    assert res["acknowledged"]
    assert res["shards_acknowledged"]
    assert res["index"] == random_index_name

    assert os_man.index_exists(random_index_name)

    res = os_man.delete_index(name=random_index_name)
    assert res
    assert res["acknowledged"]


@pytest.mark.parametrize(**INDEX_HANDLER_FIXTURE_PARAMS)
def test_index_exists(index_handler):
    """
    Test index_exists methods.

    Parameters
    ----------
    index_handler
        index_handler fixture, returning the name of the index for testing
    """
    os_man = OS_MAN
    index_name = index_handler
    assert os_man.index_exists(index_name)


@pytest.mark.parametrize(**INDEX_HANDLER_FIXTURE_PARAMS)
@pytest.mark.parametrize(
    "documents",
    [
        [
            {"age": 10, "id": 123, "name": "james"},
            {"age": 23, "id": 456, "name": "lordos"},
            {"age": 45, "id": 49, "name": "fred"},
            {"age": 10, "id": 10, "name": "carlos"},
        ],
        [
            # Empty document list
        ],
    ],
)
@pytest.mark.parametrize("id_key", ["id", None])
def test_data_insert(index_handler, documents: list, id_key: str):
    """
    Test inserting data.

    Parameters
    ----------
    index_handler
        index_handler fixture, returning the name of the index for testing
    documents: list
        list of documents [{document}, {document}, ...]
    id_key: str
        key in the document used for indexing
    """
    # Put refresh to True for immediate results
    OS_MAN.add_data_to_index(
        index_name=index_handler,
        documents=documents,
        id_key=id_key,
        refresh=True,
    )

    # Obtain documents back from OS and compare their id's to
    # local
    search_results = OS_MAN.search_index(index_handler, {})

    search_ids = get_ids_from_response(search_results)

    # Check that documents in OpenSearch are the same as in documents
    ids_difference = set(search_ids).difference(
        {document["id"] for document in documents}
    )

    assert not len(ids_difference)

    # assert all documents in OS are the same as local
    for document in documents:
        os_document = [
            doc["_source"]
            for doc in search_results["hits"]["hits"]
            if doc["_source"]["id"] == document["id"]
        ][0]

        assert document == os_document


@pytest.mark.parametrize(**INDEX_HANDLER_FIXTURE_PARAMS)
@pytest.mark.parametrize(
    "documents",
    [
        [
            {"age": 10, "id": 123, "name": "james"},
            {"age": 23, "id": 456, "name": "lordos"},
            {"age": 45, "id": 49, "name": "fred"},
            {"age": 10, "id": 10, "name": "carlos"},
        ]
    ],
)
@pytest.mark.parametrize(
    "config",
    [
        {
            "name": "test-template",
            "params": {"from": 0, "size": 100, "age": 10},
        }
    ],
)
@pytest.mark.parametrize("source", [{"query": {"match": {"age": "{{age}}"}}}])
class TestTemplates(object):
    def test_search_template_upload(
        self,
        index_handler,
        documents: list,
        config: dict,
        source: dict,
    ):
        """
        Test uploading search template.

        Parameters
        ----------
        index_handler
            index_handler fixture, returning the name of the index for testing
        documents: list
            list of documents [{document}, {document}, ...]
        config: dict
            search template config {name: template_name, parameters: {validation parameters}}
        source: dict
            search template to upload
        """
        os_man = OS_MAN

        index_name = index_handler

        config.update({"index": index_name})

        # Put refresh to True for immediate results
        os_man.add_data_to_index(
            index_name=index_name,
            documents=documents,
            id_key="id",
            refresh=True,
        )

        res = os_man.upload_search_template(
            source, config["name"], index_name, config["params"]
        )

        assert res
        assert res["acknowledged"]

        # delete script so it doesnt linger around
        os_man.client.delete_script(config["name"])

    @pytest.mark.parametrize(
        "template_name, expected_ack",
        [("test-template", True), ("wrong-template-name", False)],
    )
    def test_search_template_delete(
        self,
        index_handler,
        documents: list,
        config: dict,
        source: dict,
        template_name: str,
        expected_ack: bool,
    ):
        """
        Test deleting search template.

        Parameters
        ----------
        index_handler
            index_handler fixture, returning the name of the index for testing
        documents: list
            list of documents [{document}, {document}, ...]
        config: dict
            search template config {name: template_name, parameters: {validation parameters}}
        source: dict
            search template to upload
        template_name: str
            name of the template to be inserted
        """
        os_man = OS_MAN
        index_name = index_handler

        config["index"] = index_name

        # Put refresh to True for immediate results
        os_man.add_data_to_index(
            index_name=index_name,
            documents=documents,
            id_key="id",
            refresh=True,
        )

        os_man.upload_search_template(
            source, config["name"], index_name, config["params"]
        )

        res = os_man.delete_script(template_name)

        assert res
        assert res["acknowledged"] is expected_ack

        assert (
            os_man.client.get_script(id=template_name, ignore=[400, 404])[
                "found"
            ]
            is False
        )

    @pytest.mark.parametrize(
        "local_source, expected_ack, expected_differences",
        [
            ({"query": {"match": {"age": "{{age}}"}}}, False, []),
            (
                {
                    "query": {
                        "bool": {"must_not": [{"match": {"age": "{{age}}"}}]}
                    }
                },
                True,
                ["[root['query']['match']]", "[root['query']['bool']]"],
            ),
        ],
    )
    def test_template_comparison(
        self,
        index_handler,
        documents: list,
        config: dict,
        source: dict,
        local_source: dict,
        expected_ack: bool,
        expected_differences: list,
    ):
        """
        Test update of search template (comparison local vs os).

        Parameters
        ----------
        index_handler
            index_handler fixture, returning the name of the index for testing
        documents: list
            list of documents [{document}, {document}, ...]
        config: dict
            search template config {name: template_name, parameters: {validation parameters}}
        source: dict
            source to upload
        local_source: dict
            second source to update 'source' with
        expected_ack: bool
            expected response when updating 'source'
        expected_differences: list
            expected differences when updating 'source'
        """
        os_man = OS_MAN
        index_name = index_handler

        config.update({"index": index_name})

        # Put refresh to True for immediate results
        os_man.add_data_to_index(
            index_name=index_name,
            documents=documents,
            id_key="id",
            refresh=True,
        )

        os_man.upload_search_template(
            source, config["name"], index_name, config["params"]
        )

        res = os_man.upload_search_template(
            local_source, config["name"], index_name, config["params"]
        )

        assert res["acknowledged"] == expected_ack

        # when differences are present, test if correct
        if "differences" in res:

            assert (
                str(res.get("differences", {}).get("dictionary_item_added"))
                == expected_differences[0]
            )
            assert (
                str(res.get("differences", {}).get("dictionary_item_removed"))
                == expected_differences[1]
            )


@pytest.mark.parametrize(**INDEX_HANDLER_FIXTURE_PARAMS)
@pytest.mark.parametrize(
    "documents",
    [[{"id": 1, "container": [1, 2, 3]}]],
)
@pytest.mark.parametrize(
    "source , params, context_type, expected",
    [
        (
            """
            int multiplier = params.multiplier;
            int total = 0;
            for (int i = 0; i < doc['container'].length; ++i) {
                total += doc['container'][i] * multiplier;
            }
            return total;
            """,
            {"params": {"multiplier": 2}},
            "score",
            12,
        ),
        (
            """
            int multiplier = params.multiplier;
            int total = 0;
            for (int i = 0; i < doc['container'].length; ++i) {
                total += doc['container'][i] * multiplier;
            }
            if (total > 7) {
                return true;
            } else {
                return false;
            }
            """,
            {"params": {"multiplier": 1}},
            "filter",
            0,
        ),
        (
            """
            int multiplier = params.multiplier;
            int total = 0;
            for (int i = 0; i < doc['container'].length; ++i) {
                total += doc['container'][i] * multiplier;
            }
            if (total > 7) {
                return true;
            } else {
                return false;
            }
            """,
            {"params": {"multiplier": 3}},
            "filter",
            1,
        ),
    ],
)
class TestPainlessScripts(object):
    def test_painless_script_upload(
        self,
        index_handler,
        documents: list,
        source: dict,
        params: dict,
        context_type: str,
        expected: int,
    ):
        """
        Test uploading search template.

        Parameters
        ----------
        index_handler
            index_handler fixture, returning the name of the index for testing
        documents: list
            list of documents [{document}, {document}, ...]
        source: dict
            search template to upload
        params: dict
            parameters to pass to painless script
        context_type: str
            context type of the painless script, should be in {'filter', 'score'}
        expected: int
            expected return from painless script
        """
        os_man = OS_MAN
        index_name = index_handler

        script_name = "test_script"

        # create a json to test painless functionality
        body_painless_test = json.dumps(
            {
                "script": {"source": source, "params": params["params"]},
                "context": context_type,
                "context_setup": {
                    "index": index_name,
                    "document": documents[0],
                },
            }
        )

        # send API request to test validity of painless script
        res_painless = os_man.client.scripts_painless_execute(
            body=body_painless_test
        )

        logging.info(res_painless["result"])

        assert res_painless["result"] == expected

        # Put refresh to True for immediate results
        os_man.add_data_to_index(
            index_name=index_name,
            documents=documents,
            id_key="id",
            refresh=True,
        )

        res = os_man.upload_painless_script(source, script_name)

        assert res
        assert res["acknowledged"]

        # delete script so it doesnt linger around
        os_man.delete_script(script_name)
