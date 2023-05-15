docs-clean:
	jb clean docs
	rm -rf docs/api-gen/_autosummary
	rm -rf docs/_build

docs: docs-clean
	jb build docs

format:
	pre-commit run black-format --hook-stage manual --all-files

linting:
	pre-commit run --all-files
