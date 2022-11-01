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
