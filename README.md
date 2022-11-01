## :rocket: osman

[STRV](https://www.strv.com/) repository with useful functions to ease (y)our
work with OpenSearch.

> *osman* stands for OpenSearch MANager.

## :mag: Content

- [Installation](#installation)
- [Contribution](#contribution)
    - [Local environment setup](#local-env-setup)
    - [Versioning](#versioning)
    - [Contributers](#contributors)
- [Specs](#specs)

## <a name="installation">:computer: Installation</a>

*TODO*

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
in [Dockerfile](Dockerfile).
1. Develop.
1. Run `make docker-clean-all` to clean unused containers and volumes.

Note the following:
- You can browse the Dashboards from the web browser. In case
of running Docker on localhost you can browse the Dashboards on
[http://localhost:5061](http://localhost:5061).
- All indexed data and dashboards are persistent in a docker volume,
i.e. when you stop the OpenSearch containers the data are **not** lost.

In order to run notebook inside the docker container, use the following command
(and ensure `notebook` is in your dependencies):
`jupyter notebook --ip 0.0.0.0 --no-browser --allow-root`

#### Connecting to an OpenSearch cluster
Two methods are supported to connect to OpenSearch. To connect to OS using user credentials, the following environment variables need to be defined:

| Variable | Standard Value | Note |
|----------|----------------|------|
| OPENSEARCH_HOST   | None       | address of remote OS host|
| AUTH_METHOD | None | `user` for authentication with AWS user credentials |
| AWS_USER | None       | AWS username   |
| AWS_SECRET| None| AWS user secret / password  |

To connect to OS using a secret access key, the following environment variables need to be defined:

| Variable | Standard Value | Note |
|----------|----------------|------|
| OPENSEARCH_HOST   | None       | address of remote OS host|
| AUTH_METHOD | None | `secret` for authentication with AWS user credentials |
| AWS_ACCESS_KEY_ID        | None |     |
| AWS_SECRET_ACCESS_KEY           | None      |                                                          |
| AWS_REGION | us-east-1 |         |
| AWS_SERVICE | es | |

#### virtualenv

1. Create virtual environment called *venv*: `virtualenv --python=python3.8 venv`
1. Activate it: `. ./venv/bin/activate`
1. Install python package: `pip install -e .`

In order to deactivate the environment, run `deactivate` command.

You can also delete the environment as following: `rm -r ./venv/`

### <a name="versioning">:heavy_plus_sign: Versioning</a>

*TODO*

### <a name="contributors">:pencil: Contributors</a>

- [Jaroslav Bezdek](https://www.github.com/jardabezdek)
- [Niek Mereu](https://github.com/niekstrv)
- [Vladimír Kadlec](https://github.com/vladimirkadlec-strv)

### <a name="specs">:books: Specs</a>

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
