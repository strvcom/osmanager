import json
import pytest
import logging

from osman import Osman, OsmanConfig
from typing import Union
from parameterized import parameterized
from tests.osman.opensearch.utils import index_handler, get_ids_from_response

INDEX_MAPPING = {
    "mappings": {
      "properties": {
        "age": {"type": "integer"},
        "id": {"type": "integer"},
        "name": {"type": "text"}
      }
    }
  }


@pytest.mark.parametrize("index_handler", [INDEX_MAPPING], indirect=True)
@pytest.mark.parametrize(
  "documents",
  [
    [
      {"age": 10, "id": 123, "name": "james"},
      {"age": 23, "id": 456, "name": "lordos"},
      {"age": 45, "id": 49, "name": "fred"},
      {"age": 10, "id": 10, "name": "carlos"}
    ]
  ]
)
@pytest.mark.parametrize(
  "documents_filepath",
  [None, "tests/osman/opensearch/sample_data.json"]
)
def test_data_insert(
  index_handler,
  documents: Union[None, list],
  documents_filepath: Union[None, str]
  ):

    # Get instance of OpenSearchHelper connected to OpenSearch
    config = OsmanConfig(host_url="http://opensearch-node:9200")
    o = Osman(config)

    index_name = index_handler

    # Put refresh to True for immediate results
    o.add_data_to_index(
      name=index_name,
      documents=documents,
      documents_filepath=documents_filepath,
      refresh=True
    )

    # if loaded from disk directly, load in memory to test
    if documents is None:
        with open(documents_filepath) as json_file:
            documents = json.load(json_file)

    # Check that documents in OS are the same as in json
    input_ids = set([document["id"] for document in documents])

    # Obtain documents back from OS and compare their id's to
    # local
    search_results = o.search_index(index_name, {})

    search_ids = get_ids_from_response(search_results)

    ids_difference = input_ids.difference(search_ids)

    assert len(ids_difference) == 0

    # assert all documents in OS are the same as local
    for document in documents:
        id = document["id"]
        os_document = [
            doc["_source"] for doc in search_results["hits"]["hits"]
            if doc["_source"]["id"] == id
          ][0]

        assert document == os_document
