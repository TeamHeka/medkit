from setuptools import setup, find_packages

setup(
    name="Medkit",
    version="0.0.0.dev0",
    description="A Python library for a learning health system",
    url="https://gitlab.inria.fr/heka/medkit/",
    license="MIT",
    packages=find_packages(include=["medkit", "medkit.*"]),
    package_data={"": ["*.yml", "*.tsv"]},
    python_requires=">=3.8",
    install_requires=["pyaml", "PyRuSH", "smart_open"],
    extras_require={
        "dev": ["black", "flake8", "pytest", "pytest-cov"],
    },
)
