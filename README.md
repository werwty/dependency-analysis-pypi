# 774-project

TLDR: Let's model the entire python package dependency graph and do *some* TBD analysis.

### Getting Started

Setting up the environment may require installing some or all of the following dependencies:

- [Python 3.7](https://www.python.org/downloads/release/python-370/)
- [Docker](https://www.docker.com/products/container-runtime#/download)
- [docker-compose](https://docs.docker.com/compose/install/)
- [poetry](https://python-poetry.org/docs/#installation)

#### Docker Compose

We use docker-compose to manage our development containers. To get started run:
```
sudo systemctl start docker
docker-compose up
```

The dgraph UI is available at http://localhost:8000/

The jupyter notebook is available at http://127.0.0.1:8888/


#### Python virtual environment

Poetry is used to manage the python virtual environment.

The first time you set this up, use poetry to install the needed dependencies:

```
poetry install
```

To activate the virtual environment run:

```
poetry shell
```
