docs-clean:
	jb clean docs
	rm -rf docs/api-gen/_autosummary

docs: docs-clean
	jb build docs

format:
	pre-commit run black-format --hook-stage manual --all-files

linting:
	pre-commit run --all-files
