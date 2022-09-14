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

## <a name="installation">:computer: Installation</a>

*TODO*

## <a name="contribution">:construction_worker_man: Contribution</a>

### <a name="local-env-setup">:wrench: Local environment setup</a>

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
