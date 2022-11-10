import json
import pytest
import logging

from osman import Osman, OsmanConfig
from tests.osman.opensearch.utils import index_handler, get_ids_from_response

index_mapping = "tests/osman/opensearch/index_mapping.json"
sample_data = "tests/osman/opensearch/sample_data.json"


with open(index_mapping) as json_file:
    mapping = json.load(json_file)

with open(sample_data) as json_file:
     data = json.load(json_file)

@pytest.mark.parametrize("index_handler", [mapping], indirect=True)
def test_data_insert(index_handler):

    # Get instance of OpenSearchHelper connected to OpenSearch
    config = OsmanConfig(host_url="http://opensearch-node:9200")
    o = Osman(config)

    index_name = index_handler

    # Put refresh to True for immediate results
    o.add_data_to_index(index_name, sample_data, refresh=True)

    # Check that documents in OS are the same as in json
    input_ids = set([document["id"] for document in data])

    # Obtain documents back from OS and compare their id's to
    # local
    search_results = o.search_index(index_name, {})

    search_ids = get_ids_from_response(search_results)

    ids_difference = input_ids.difference(search_ids)

    assert len(ids_difference) == 0

    # assert all documents in OS are the same as local
    for document in data:
        id = document["id"]
        os_document = [
            doc["_source"] for doc in search_results["hits"]["hits"]
            if doc["_source"]["id"] == id
        ][0]

        assert document == os_document
