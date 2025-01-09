## :rocket: osman

[STRV](https://www.strv.com/) repository with useful functions to ease (y)our
work with OpenSearch.

> *osman* stands for OpenSearch MANager.

## :mag: Content

- [Installation](#installation)
- [Usage](#usage)
- [Contribution](#contribution)
    - [Local environment setup](#local-env-setup)
    - [Testing](#testing)
    - [Local lintering](#local-lintering)
    - [Versioning](#versioning)
    - [Contributers](#contributors)
- [OpenSearch](#opensearch)
- [Specs](#specs)

## <a name="installation">:computer: Installation</a>

1. Create a new virtual environment.
2. Run `pip install osmanager`.

## <a name="usage">:hammer: Usage</a>

**Create an Osman instance**

The [environment variables](#testing) are read by `OsmanConfig`.

```
from osman import Osman, OsmanConfig

os_man = Osman(OsmanConfig())
```

Environment variables can be overridden.

```
os_man = Osman(OsmanConfig(host_url=<OpenSearch_host_url>))
```

**Create an index**
```
mapping = {
  "mappings": {
    "properties": {
      "age": {"type": "integer"},
      "id": {"type": "integer"},
      "name": {"type": "text"},
    }
  }
}

settings = {
  "settings": {
    "number_of_shards": 3
  }
}

os_man.create_index(
  name=<index_name>, mapping=mapping, settings=settings
)
```

**Upload a search template**
```
source = {
  "query": {
    "match": {
      "age": "{{age}}"
    }
  }
}

params = {
  "age": 10
}

os_man.upload_search_template(
            source=source, name=<template_name>, index=<index_name>, params=params
)
```

**Upload a painless script**
```
source = "doc['first.keyword'].value + ' ' + doc['last.keyword'].value"

os_man.upload_painless_script(source=source, name=<script_name>)
```

**Delete a search template or a painless script**

Removes either a painless script or a search template.

```
os_man.delete_script(name=<script_or_template_name>)
```

**Debug a painless script**

Executes a certain painless script with provided data and parameters. It then checks if the expected result is returned. The `context_type` must be provided and is either `score` or `filter`. This refers to the score or filter queries as is described [here](https://opensearch.org/docs/1.2/opensearch/query-dsl/bool/).

```
context_type = "score"

documents = {"id": 1, "container": [1, 2, 3]}

expected_result = 0

os_man.debug_painless_script(
  source=<source>,
  index=<index_name>,
  params=<params>,
  context_type=context_type,
  documents=documents,
  expected_result=expected_result
)
```

**Debug a search template**

Executes a certain search template against an index with defined parameters. It then checks if the expected indices are returned.

```
expected_ids = ["123", "10"]

os_man.debug_search_template(
  source=source, name=<template_name>, index=<index_name>, params=params, expected_ids=expected_ids
)
```

**Reindex**

Reindex an existing index with a new mapping and/or settings.
In order to reindex, this function adds a suffix [1, 2] to the index name.
Afterwards, the index should be referenced by its alias rather than its name.

For example:

An index with the name *test-index* is reindexed. Its name becomes *test-index-1*.  When reindexed again, its name will become *test-index-2*. Hence, it should be referenced by its unchanging alias *test-index*.

```
os_man.reindex(
  name=<index_name>, mapping=<new_mapping>, settings=<new_settings>
)
```

**Text Embeddings**

For using text embeddings, ML must be enabled in the index settings. The following example shows how to enable ML in the index settings.

```
cluster_settings = {
    "transient": {
        "plugins.ml_commons.model_access_control_enabled": True,
        "plugins.ml_commons.allow_registering_model_via_url": True,
        "plugins.ml_commons.only_run_on_ml_node": False,
    },
    "persistent": {
        "plugins": {
            "ml_commons": {
                "only_run_on_ml_node": "false",
                "model_access_control_enabled": "true",
                "native_memory_threshold": "99"
            }
        }
    }
}
os_man.update_cluster_settings(cluster_settings)
```

Create a model group:

```
POST /_plugins/_ml/model_groups/_register
{
  "name": "model-group",
  "description": "A model group",

}
```

To create a model, the following example shows how to create a model with the given parameters.

```
model_payload = {
    "name": "example-model",
    "version": "1.0.0",
    "model_format": "TORCH_SCRIPT"
    "model_group_id": "model-group",
}
os_man.send_post_request(
    "/_plugins/_ml/models/_register",
    model_payload
)
```
A task_id is returned after creating a model. This task_id can be used to check the status of the model.

```
task_id = "task_id"
endpoint = f"/_plugins/_ml/tasks/{task_id}"

os_man.send_get_request(endpoint)
```

To deploy a model, obtain the model_id from the response of the model creation. The following example shows how to deploy a model with the given model_id.

```
model_id = "model_id"
endpoint = f"/_plugins/_ml/models/{model_id}/_deploy"
payload = {}
os_man.send_post_request(endpoint, payload)
```

To create an NLP ingest pipeline:

```
pipeline_id = "nlp-ingest-pipeline"
endpoint = f"/_ingest/pipeline/{pipeline_id}"

# Define the payload for the ingest pipeline
pipeline_payload = {
    "description": "An NLP ingest pipeline",
    "processors": [
        {
            "text_embedding": {
                "model_id": "model_id",
                "field_map": {
                    "content": "passage_embedding"
                }
            }
        }
    ]
}

os_man.send_put_request(endpoint, pipeline_payload)
```

Create a search template with text embeddings:

```
source = {
    "size": 500,
    "query": {
        "neural": {
            "passage_embedding": {
                "query_text": "{{query_text}}",
                "model_id": "{{model_id}}",
                "k": "{{k}}"
                }
            }
        }
    }

params = {
    "query_text": "This is a sample query",
    "model_id": "model_id",
    "k": "number_of_nearest_neighbors"
}

os_man.upload_search_template(
    source=source,
    name="search_template_name",
    index="index_name",
    params=params
)
```

## <a name="contribution">:construction_worker_man: Contribution</a>

### <a name="local-env-setup">:wrench: Local environment setup</a>

Launch the docker daemon in advance of the following steps. You can develop the code using
virtualenv but the local OpenSearch instance requires docker.

#### Local OpenSearch instance and docker development environment

Command `make help` shows a brief description of possible targets. A typical workflow scenario is:
1. Run `make docker-run-opensearch` to launch OpenSearch instance
on port 9200 and OpenSearch Dashboards on port 5601, as described in
[docker-compose-opensearch.yml](docker-compose-opensearch.yml).
1. Run `make dev-env` to get a bash shell in the development environment defined
in [Dockerfile](Dockerfile). Under Linux set the user/group in advance in `.env`, see bellow.
1. Develop.
1. Run `make docker-clean-all` to clean unused containers and volumes.

Note the following:
- Under Linux you may encounter a problem that a user in the docker guest container
  doesn't have permissions to write to the local directory. This leads to problems with
  `pytest` unable to create cache directories. The solution is to have the followig
  variables in `.env` file:
  ```
    DEV_USER_ID=1000
    DEV_GROUP_ID=1000
  ```
  Substitute 1000 by `uid` and `gid` (introduction in
  [this article](https://www.redhat.com/sysadmin/user-account-gid-uid))
  of the user on a host machine. The ids can be obtained by running `id` command.
  See [explanation](https://jtreminio.com/blog/running-docker-containers-as-current-host-user/)
  for why we do that. With Docker under MacOS or Windows you won't need this.

- You can browse the Dashboards from the web browser. In case
of running Docker on localhost you can browse the Dashboards on
[http://localhost:5061](http://localhost:5061).
- All indexed data and dashboards are persistent in a docker volume,
i.e. when you stop the OpenSearch containers the data are **not** lost.

In order to run notebook inside the docker container, use the following command
(and ensure `notebook` is in your dependencies):
`jupyter notebook --ip 0.0.0.0 --no-browser --allow-root`

#### virtualenv

1. Create virtual environment called *venv*: `virtualenv --python=python3.8 venv`
1. Activate it: `. ./venv/bin/activate`
1. Install python package: `pip install -e .`

In order to deactivate the environment, run `deactivate` command.

You can also delete the environment as following: `rm -r ./venv/`

### <a name="testing">:traffic_light: Testing

Run `pytest` in your devel environment to run all tests.

The `OsmanConfig` class can be initialized from the environment by the following variables:

| Variable | Default value | Type| Description |
|----------|---------------|-----|-------------|
| AUTH_METHOD             | `http` | string |`http` for username/password authentication, <br />`awsauth`for authentication with AWS user credentials |
| OPENSEARCH_HOST         | None | string | address of OpenSearch host|
| OPENSEARCH_PORT         | 443  | int | port number |
| OPENSEARCH_SSL_ENABLED  | True | bool | use SSL? |
| OPENSEARCH_USER         | None | string | username, for `http` AUTH_METHOD |
| OPENSEARCH_SECRET       | None | string | password, for `http` AUTH_METHOD |
| AWS_ACCESS_KEY_ID       | None | string | access key id for `awsauth` AUTH_METHOD, see [AWS4Auth](https://pypi.org/project/requests-aws4auth/) |
| AWS_SECRET_ACCESS_KEY   | None | string | secret key for `awsauth` AUTH_METHOD|
| AWS_REGION              | `us-east-1` | string | AWS region for `awsauth` AUTH_METHOD|
| AWS_SERVICE             | `es` | string | AWS service for `awsauth` AUTH_METHOD|

You can add these variables to your `.env` file, `make dev-env` will pass
them to the devel Docker image. There is a test in [test_osman.py](tests/osman/test_osman.py) creating `Osman` instance
using environment variables so you can use any OpenSearch instance for testing.

### <a name="local-lintering">:broom: Local lintering

For running linters from GitHub actions locally, you need to do the following.

1. Install [`pre-commit`](https://pypi.org/project/pre-commit/) library.
1. From root project directory, run: `pre-commit run --all-files`

### <a name="versioning">:heavy_plus_sign: Versioning</a>
For information on semantic versioning, see [semver.org](https://semver.org/).

Given a version number MAJOR.MINOR.PATCH, increment the:

- MAJOR version when you make incompatible API changes
- MINOR version when you add functionality in a backwards compatible manner
- PATCH version when you make backwards compatible bug fixes

When incrementing the MAJOR version, reset the MINOR and PATCH versions to 0.
When incrementing the MINOR version, reset the PATCH version to 0.

When a version is released, a tag should be created in the format `vMAJOR.MINOR.PATCH`.

A new version is not automatically released upon merging into master. Follow the steps below to create a new release:

1. Add the tag to the current branch like this:

```
git tag -a v1.0.0 -m "Release version 1.0.0"
```
2. Push the tag to the remote repository:

```
git push origin --tags
```

### <a name="contributors">:pencil: Contributors</a>

- [Jaroslav Bezdek](https://www.github.com/jardabezdek)
- [Niek Mereu](https://github.com/niekstrv)
- [Vladimír Kadlec](https://github.com/vladimirkadlec-strv)

## <a name="opensearch">:scroll: OpenSearch</a>
This section contains a brief overview of OpenSearch. This section is by no means complete or exhaustive. However, it contains a few tips and tricks that might be useful for the development of your OpenSearch project. For more information, visit the [OpenSearch documentation](https://opensearch.org/docs/latest/index/).

### <a name="analyzers">:clipboard: Analyzers</a>
Analyzers are used to process text fields during indexing and search time. Analyzers are composed of one or more tokenizer and zero or more token filters. The tokenizer breaks the text into individual terms and the token filters potentially remove them from the analyzed field. Fields can have more than one field type, so different analyzers can be utilised for different situations.

This section contains a small overview of the analyzers available in OpenSearch. For analyzers in general, see [Analyzers in OpenSearch](https://opensearch.org/docs/latest/opensearch/analyzers/).

- **Standard**
  - Standard analyzers are used to index and search for complete words. Standard analyzers are composed of a tokenizer and a token filter. The standard analyzer uses the standard tokenizer. The standard tokenizer breaks text into terms on word boundaries. The standard analyzer also uses the lowercase token filter. The lowercase token filter converts all tokens to lowercase.
  - The standard tokenizer breaks down words on word boundaries. It breaks words down on whitespaces, as well as many special characters.
  - The Standard analyzer might not be useful for fields like Email addresses. An email address like "123@strv-2.com" is broken down into "123", "strv", "2", "com".
- **Whitespace**
  - Whitespace analyzers are used to index and search for complete words. Whitespace analyzers are composed of a tokenizer and a token filter. The whitespace analyzer uses the whitespace tokenizer.
  - Because the Whitespace analyzer does not break words on special characters, it is more suitable for data like Email addresses or URLs.
- **N-gram**
  - N-gram analyzers are used to index and search for partial words. N-gram analyzers are composed of a tokenizer and a token filter. The tokenizer breaks the text into individual terms and the token filter creates n-grams for each term. N-gram analyzers are used to index and search for partial words.
  - N-gram analyzers should not be used for large text fields. This is because n-grams can be very large and can consume a lot of disk space.
  - Words lose their meaning when they are broken into n-grams. For example, the word "search" is broken into "se", "ea", "ar", "rc", "ch". This means that a search for "sea" will match the word "search".
  - N-gram analyzers could be useful when adressing a "username" field. This is because usernames are of limited length and users should probably be found by just searching for the middle part of their name. For example "xSuperUser" should be found by using "sup".

| Not analysed | Standard | Whitespace     | N-gram |
| :---       |    :----:   |          :---: | ---: |
| 123@strv-2.com   | [123, strv, 2, com]  | [123@strv-2.com]   | [1, 12, 2, 23, 3...] |
| How's it going?   | [How, s, it, going]       | [How's, it, going?]     | [H, Ho, o, ow, w...]|
xUser-123   | [xUser, 123]       | [xUser-123]     | [x, xu, u, us, s...]|

### <a name="field types">:card_index: Field Types</a>

This section contains a small overview of the field types that are available in OpenSearch. For field types that are not discussed here, please refer to the [official documentation](https://opensearch.org/docs/opensearch/rest-api/create-index/).

- **Keyword**
  - Keyword fields are used to store data that is not meant to be analyzed. Keyword fields are not analyzed and support exact value searches.
  - Keyword fields are not used for full-text search.
  - Keyword fields are for example useful for "id" fields.

- **Text**
  - Text fields are used to store textual data, such as the body of an email or the description of a product in an e-commerce store. Text fields are analyzed and support full-text search.
  - Text fields are used when exact value searches are not wanted.


## <a name="specs">:books: Specs</a>

#### Requirements

##### Library

The goal is to extend [opensearch-py library](https://pypi.org/project/opensearch-py/) features that we found useful.

- Connect to opensearch using url (user/pass) or service account
- Upload & remove search template
- Upload & remove function
- Create & drop index with mapping
- Load json file with template source element
- Load json file with function
- Load json file with mapping
- Run local search template with sample parameters to see if all work (without upload)
- Run local function with sample parameters (without upload)
- Run local index with sample doc with given data types (without upload)
- Check local file vs opensearch file and show differences
  - search template
  - function
  - index mapping

##### Application

The goal is to allow teams manage opensearch instances easily with templated project setup.

- Have yaml config, yaml list of files
- Create sample json structure for all files
- Sync things based on yaml file:
  - sync between local json files and yaml list
  - sync between local yaml list and opensearch
- Split everything between envs: have yaml file with env definitions
- **Nice to have** lint template?
  - vscode default json linter fails to lint template due to parameters syntax: {{#bla}}

#### Tasks

Tasks are kept in github project [Osman](https://github.com/orgs/strvcom/projects/14/views/2)
