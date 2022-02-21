# Contributing to Medkit

Thank you for your interest in to Medkit! This page will guide you through the steps to follow in order to contribute code to the project.

## Contributing process

Medkit uses a mix of the [GitHub flow](https://docs.github.com/en/get-started/quickstart/github-flow) and the [Git flow](https://nvie.com/posts/a-successful-git-branching-model/) branching models. We have 2 permanents branches: `main` and `develop`. The `main` branch is the stable branch and will contain the releases, while `develop` contains the most up-to-date version of the code. Feature and bugfixes branches are created from `develop` and merged back into `develop`. Changes from `develop` are incorporated in `main` after running more exhaustive checks.

The Medkit contributing process is as follows:
- before creating a new branch, open an [issue](https://gitlab.inria.fr/heka/medkit/-/issues/) describing the bug or the feature you will be working on, unless there already is an existing issue.
- create a branch based on `develop` named with the following convention: `<issue-id>-<short-description>` (without the `#` character).
- start working by adding commits to this branch. Try to have clear [commit messages](https://cbea.ms/git-commit/). Do not forget to also write tests in the `tests/`directory if applicable (cf [Tests](#tests)).
- once you are done, check that your code follows our coding standards with `black`and `flake8` (cf [Linting and formatting](#linting-and-formatting)) and that all the tests pass with `pytest` (cf [Tests](#tests))
- push your local branch on the Gitlab repository and open a [merge request](https://gitlab.inria.fr/heka/medkit/-/merge_requests) (MR). Unit tests and linting/formatting checks will automatically be run on the MR and prevent it from being merged if they fail.
- wait for the review of the Medkit maintainers. They will make sure it aligns with the project goals and may ask for some changes.

Once this reviewing phase is over, the merge request will be integrated into `develop`, either with a merge, a squash & merge or a rebase, depending on the impact of the merge request and the state of its git history. The branch you worked on will then be deleted.

## Development environment

Before everything else, make sure you have the appropriate Python version running on your system (`python3 --version`). Medkit requires Python >= 3.8. Optionally, you may want to create and activate a virtual environment with Python's [built-in venv module](https://docs.python.org/3/library/venv.html) (commands will slightly differ on Windows):

```shell
python3 -m venv <path/to/venv>
source <path/to/venv>/bin/activate
```

or [conda](https://conda.io):

```shell
conda create --name medkit python=3.8
conda activate medkit
```

To set up a local dev environment:
- clone the Medkit repository locally:
  - SSH: `git clone git@gitlab.inria.fr:heka/medkit.git`
  - HTTPS: `git clone https://gitlab.inria.fr/heka/medkit`
- enter the repository root dir (`cd medkit/`) and install the required dev dependencies: `pip install -r requirements.txt`
- TODO: describe how to enable pre-commit hooks

To make sure everything is set up properly, you may run the tests by launching the `pytest` command in the repository root dir.

If you want to run the examples stored in the `examples/` directory, you may install the medkit package in editable mode by running `pip install -e .` in the repository root dir.

## Coding standards
### Code conventions

The Medkit codebase follows the [PEP8](https://www.python.org/dev/peps/pep-0008/) style guide for Python code, which defines several rules among which:
- use 4 spaces (not tabs) per indentation level.
- use `snake_case` for variable and functions, `CamelCase` for classes and `UPPER_SNAKE_CASE` for constants defined at module level.
- prefix non-public variables, methods, attributes and modules (ie .py files) with a leading underscore.
- avoid `import *`, prefer explicit import.
- use `"double-quoted"` strings rather than `'single-quoted'`.

Note that contrary to PEP8, the maximum line length in Medkit is not 79 characters but 88 (for better compatibility with the `black` formatter (cf [Linting and formatting](#linting-and-formatting)).

### Linting and formatting

To format the codebase consistently and enforce PEP8 compliance, we use [black](https://github.com/ambv/black) for code formatting and [flake8](https://github.com/ambv/black) for linting.

Running the command `black <path/to/file.py>` will auto-format the file. Running `flake8 <path/to/file.py>` will display potential infractions to PEP8. Editors such as [vscode](https://code.visualstudio.com/) can be configured to do this automatically when editing or saving a file.

Note that every time a merge request is opened or updated, `black` and `flake8` will automatically be run on the codebase and will prevent it from being merged if an error is detected.

TODO mention pre-commit hooks.

### Coding style

Some general guidelines to keep in mind:
- code and comments are written in english.
- use readable names for identifiers (variables, functions, etc). Avoid one-letter names and do not overuse abbreviations. Try to use nouns for classes and verbs for functions and methods.
- expose only what is necessary: mark internal function, variables, classes, modules as non-public with a leading underscore (for instance `_perform_internal_task()`).
- group related code into the same Python module (ie .py file), for instance a class and helper function, but avoid packing to many classes in the same module.
- avoid "magic" features such as `hasattr()`/`getattr()`/`setattr()`.
- use [property decorators](https://docs.python.org/3/library/functions.html#property), rater than `get_`/`set_`methods, to created read-only or computed attributes. Do not use them for complex or expensive logic.

## Tests

Medkit uses [pytest](https://docs.pytest.org/) for testing. Tests are stored in the `tests/` folder in the repository root directory, and they can be executed with the command `pytest`. All tests files and test functions must be prefixed with `test_`.  It is possible to run a specific test using `pytest path/to/test_file.py::test_func`.

Medkit doesn't explicit distinguish between unit test, integration tests, regression tests, etc. The structure in the `tests/` directory should roughly follow the structure of the `medkit/` source directory itself. For instance, the tests of the (hypothetical) `medkit/core/text/document.py` module should be in `tests/core/text/document.py`. This is not a hard rule, it might be necessary to create test modules in `tests/` that do not have a direct counter part in `medkit/` if we are extensively testing some specific feature and we want to keep these tests separately for clarity.

When fixing a bug, it is a good idea to introduce a test in order to:
- demonstrate the buggy behavior.
- make sure the fix actually fixing it (the test should fail before the fix and pass after).
- make sure the bug is not reintroduced later.

When introducing new feature, it is also a good idea to introduce tests in order to:
- demonstrate the typical usage of the new functions and classes.
- make sure they behave as intended in typical use cases.
- if applicable, make sure they behave correctly in specific edge cases.

Each test function should have a name like `test_<tested_module_or_class_or_func>[_<tested_behavior>]` Remember to use [parametrize](https://docs.pytest.org/parametrize.html) when possible, as well as [fixtures](https://docs.pytest.org/fixture.html).

## Documentation

TODO

