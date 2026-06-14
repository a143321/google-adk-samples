.PHONY: install playground test lint deploy

install:
	uvx google-agents-cli install

playground:
	uvx google-agents-cli playground

test:
	uv run pytest

lint:
	uv run ruff check .

deploy:
	uvx google-agents-cli deploy --no-confirm-project
