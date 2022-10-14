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

#### Local Open Search instance
Run:
`make run-opensearch`
This will run OpenSearch instance on port 9200 and OpenSearch Dashboards on port 5601 as described
in [docker-compose-opensearch.yml](docker-compose-opensearch.yml). In case of running docker
on localhost you can browse the Dashboards on [http://localhost:5061](http://localhost:5061) .

`make clean-all`
Deletes all docker containers matching name `opensearch` and docker volume `opensearch-data1`.

#### Docker

1. Launch the docker daemon.
2. Build the docker image with a proper tag:
`docker build -t strv-ds-opensearch-manager:latest .`
3. Run the docker container:
`docker run -it -p 8888:8888 -v $(pwd)/:/usr/src/app strv-ds-opensearch-manager:latest /bin/bash`

In order to run notebook inside the docker container, use the following command
(and ensure `notebook` is in your dependencies):
`jupyter notebook --ip 0.0.0.0 --no-browser --allow-root`

#### virtualenv

1. Create virtual environment called *venv*: `virtualenv --python=python3.8 venv`
2. Activate it: `. ./venv/bin/activate`
3. Install python package: `pip install -e .`

In order to deactivate the environment, run `deactivate` command.

You can also delete the environment as following: `rm -r ./venv/`

### <a name="versioning">:heavy_plus_sign: Versioning</a>

*TODO*

### <a name="contributors">:pencil: Contributors</a>

- [Jaroslav Bezdek](https://www.github.com/jardabezdek)
- [Niek Mereu](https://github.com/niekstrv)

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
