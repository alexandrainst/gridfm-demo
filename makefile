# This ensures that we can call `make <target>` even if `<target>` exists as a file or
# directory.
.PHONY: help install install-dependencies install-pre-commit test check \
	format-markdown tree flower-data flower-build flower-up flower-run flower-down \
	flower-clean-data

help:
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' makefile | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	@echo "Installing the 'gridfm_demo' project..."
	@$(MAKE) --quiet install-dependencies
	@echo "Installed the 'gridfm_demo' project! You can now activate your virtual environment with 'source .venv/bin/activate'."
	@echo "Note that this is a 'uv' project. Use 'uv add <package>' to install new dependencies and 'uv remove <package>' to remove them."

install-dependencies:
	@uv sync --all-extras --all-groups

install-pre-commit:
	@uv run pre-commit install
	@uv run pre-commit autoupdate

test:  ## Run tests
	@uv run pytest && uv run readme-cov

check:  ## Lint, format, and type-check the code
	@uv run pre-commit run --files $$(git ls-files --cached --others --exclude-standard)

format-markdown:
	## markdownlint-cli2 does not support wrapping lines at 88 characters, so we use Prettier to wrap lines at 88 characters and then use markdownlint-cli2 to fix any remaining issues.
	prettier --write --prose-wrap=always --print-width=88 *.md docs/**/*.md src/federated_learning/*.md
	markdownlint-cli2 --fix *.md docs/**/*.md src/federated_learning/*.md

tree:  ## Print directory tree
	@tree -a --gitignore -I .git .

flower-data: data/federated_learning/client_0/case14_ieee/raw/bus_data.parquet data/federated_learning/client_1/case14_ieee/raw/bus_data.parquet

data/federated_learning/client_%/case14_ieee/raw/bus_data.parquet: src/federated_learning/config/datakit_client_%.yaml
	@uv run python src/federated_learning/scripts/generate_client_data.py --config $<

flower-build:  ## Build the Flower Docker images (serverapp + clientapp)
	@docker compose -f src/federated_learning/docker-compose.yml build

flower-up: flower-data  ## Start the local Flower federation (SuperLink + 2 SuperNodes + apps)
	@docker compose -f src/federated_learning/docker-compose.yml up -d --build

flower-run:  ## Submit the experiment to the running federation
	@uv run flwr run . local-deployment --stream

flower-down:  ## Stop the local Flower federation
	@docker compose -f src/federated_learning/docker-compose.yml down

flower-clean-data:  ## Wipe generated client datasets
	@rm -rf data/federated_learning
