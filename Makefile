docs-clean:
	jb clean docs
	rm -rf docs/api-gen/_autosummary

docs: docs-clean
	jb build docs
