# Installation

The medkit package supports a version of python >= 3.7.

## Install an official version

Releases are published on <https://gitlab.inria.fr/heka/medkit/-/releases>.

To install medkit, download the package in release assets and install the package.
For example:

```
# Install medkit with required dependencies
python -m pip install 'MedKit-0.2.0.tar.gz'

# Install medkit with extra dev dependencies
python -m pip install 'MedKit-0.2.0.tar.gz[dev]'

# Install medkit with extra optional dependencies
python -m pip install 'MedKit-0.2.0.tar.gz[optional]'
```

```{note}
We recommend to install the medkit package in a virtual or conda environment.
```

## Install a development version

If you want to contribute, clone the `medkit` repository locally:
  - SSH: `git clone git@gitlab.inria.fr:heka/medkit.git`
  - HTTPS: `git clone https://gitlab.inria.fr/heka/medkit`

```{note}
If you do not have rights to see the project, please contact HeKA team.
```
[Poetry](https://python-poetry.org) is used for managing dependencies and
packaging medkit.

```shell
cd medkit
poetry install
```

If you want to also install the extras dependencies, you may use:
```shell
poetry install -E optional -E hf-translators
```

For documentation:
```shell
poetry install -E docs
```

Then, a `.venv` folder is created at the root of the project. To activate the
virtual environment:
```shell
source ./.venv/bin/activate
```

To make sure everything is set up properly, you may run the tests :

```
# For unit/small tests
pytest -v tests/unit

# For large tests
pytest -v tests/large
```
