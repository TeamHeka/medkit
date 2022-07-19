# Installation

The medkit package supports a version of python >= 3.7.

When developing new medkit components, we have to ensure it.
That's why pre-defined conda environments are based on python 3.7.

For medkit usage, you may define your own environmnent with a version of
python >= 3.7.

## Install a development version

Clone the Medkit repository locally:
  - SSH: `git clone git@gitlab.inria.fr:heka/medkit.git`
  - HTTPS: `git clone https://gitlab.inria.fr/heka/medkit`

```{note}
If you do not have rights to see the project, please contact HeKA team.
```
If you want to use a pre-defined environment with python 3.7, you may set up it
with [mamba](https://mamba.readthedocs.io/en/latest/user_guide/mamba.html):

```shell
cd medkit
mamba env create -f environment.yml
conda activate medkit
```

Otherwise, you may also create your own environment and install all
dependencies using `pip install -r requirements.txt`.

To make sure everything is set up properly, you may run the tests :

```
# For unit/small tests
pytest -v tests/unit

# For large tests
pytest -v tests/large
```

Then, if you want to install medkit, you may use:
```
pip install -e .
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

We recommend to install the medkit package in a virtual or conda environment.