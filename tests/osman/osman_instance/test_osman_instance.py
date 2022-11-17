"""
Test Osman class instance methods
"""
import logging
import pytest

from osman import Osman, OsmanConfig

# Index mapping for testing documents
INDEX_MAPPING = {
    "mappings": {
        "properties": {
            "age": {"type": "integer"},
            "id": {"type": "integer"},
            "name": {"type": "text"}
        }
    }
}

# Osman instance
OS_MAN = Osman(OsmanConfig(host_url="http://opensearch-node:9200"))

# Parameters for index_handler fixture
INDEX_HANDLER_FIXTURE_PARAMS = {
    "argnames": "index_handler",
    "argvalues": [{"mapping": INDEX_MAPPING, "os_man": OS_MAN}],
    "indirect": True,
}

def get_ids_from_response(response):
    """
    Extract id's from OpenSearch response dict (index search)
    """

    if "hits" not in response:
        logging.error("Missing `hits` in response")
        return None

    if "hits" not in response["hits"]:
        logging.error("Missing `hits` in response['hits']")
        return None

    if len(response["hits"]["hits"]) == 0:
        logging.warning("Empty response")
        return []

    if "id" not in response["hits"]["hits"][0]["_source"]:
        logging.error("Missing `post_id` in documents")
        return None

    return [document["_source"]["id"] for document in response["hits"]["hits"]]


def test_index_manipulation(random_index_name):
    """
    Test create_index/index_exists/delete_index
    """
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
    Test index_exists methods
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
        {"age": 10, "id": 10, "name": "carlos"}
        ],
        [
            # Empty document list
        ],
    ]
)
def test_data_insert(index_handler, documents: list):
    """
    Test inserting data

    Parameters
    ----------
    index_handler
        index_handler fixture, returning the name of the index for testing
    documents: list
        list of documents [{document}, {document}, ...]
    """

    os_man = OS_MAN

    index_name = index_handler

    # Put refresh to True for immediate results
    os_man.add_data_to_index(index_name=index_name, documents=documents,
        refresh=True
    )

    # Check that documents in OpenSearch are the same as in documents
    input_ids = {document["id"] for document in documents}

    # Obtain documents back from OS and compare their id's to
    # local
    search_results = os_man.search_index(index_name, {})

    search_ids = get_ids_from_response(search_results)

    ids_difference = input_ids.difference(search_ids)

    assert len(ids_difference) == 0

    # assert all documents in OS are the same as local
    for document in documents:
        doc_id = document["id"]
        os_document = [
            doc["_source"] for doc in search_results["hits"]["hits"]
            if doc["_source"]["id"] == doc_id
          ][0]

        assert document == os_document
