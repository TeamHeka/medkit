# Installation

## Install a development version

Clone the Medkit repository locally:
  - SSH: `git clone git@gitlab.inria.fr:heka/medkit.git`
  - HTTPS: `git clone https://gitlab.inria.fr/heka/medkit`

```{note}
If you do not have rights to see the project, please contact HeKA team.
```

Set up your environment with [mamba](https://mamba.readthedocs.io/en/latest/user_guide/mamba.html):

```shell
cd medkit
mamba env create -f environment.yml
conda activate medkit
```

To make sure everything is set up properly, you may run the tests :

```
# For unit/small tests
pytest -v tests/unit

# For large tests
pytest -v tests/large
```

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