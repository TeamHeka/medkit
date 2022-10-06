# Installation

The medkit package supports a version of python >= 3.7.

## Install an official version

Releases are published on <https://github.com/TeamHeka/medkit/releases>.

To install medkit, download the package in release assets and install the package.
For example:

```
# Install medkit with required dependencies
python -m pip install 'medkit-0.3.1.tar.gz

# Install medkit with extra optional dependencies
python -m pip install 'medkit-0.3.1.tar.gz[optional]'
```

```{note}
We recommend to install the medkit package in a virtual or conda environment.
```

## Install a development version

If you want to contribute, clone the `medkit` repository locally:
  - SSH: `git clone  git@github.com:TeamHeka/medkit.git`
  - HTTPS: `git clone https://github.com/TeamHeka/medkit.git`

[Poetry](https://python-poetry.org) is used for managing dependencies and
packaging medkit.

```shell
cd medkit
poetry install
```

If you want to also install the extras dependencies, you may use:
```shell
poetry install --all-extras
```

For documentation:
```shell
poetry install --with docs
```

Then, a `.venv` folder is created at the root of the project. To activate the
virtual environment:
```shell
source .venv/bin/activate
```

To make sure everything is set up properly, you may run the tests :

```
# For unit/small tests
pytest -v tests/unit

# For large tests
pytest -v tests/large
```
## Troubleshooting

Sometimes, for documentation and/or testing, you may need some additional packages:

```
sudo apt-get install -y gcc g++ libsndfile1 graphviz
```
You may also refer to CI file (e.g., .gitlab-ci.yml) for up-to-date information.
