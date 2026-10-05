# This ensures that we can call `make <target>` even if `<target>` exists as a file or
# directory.
.PHONY: help install install-non-interactive install-uv install-pre-commit \
	install-dependencies test flower-data flower-clean-data flower-build \
	flower-up flower-down flower-run tree check format-markdown

# Set the PATH env var used by cargo and uv
export PATH := ${HOME}/.local/bin:${HOME}/.cargo/bin:$(PATH)

# Set the shell to bash, enabling the use of `source` statements
SHELL := /bin/bash

help:
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' makefile | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	@echo "Installing the 'gridfm_demo' project..."
	@$(MAKE) --quiet install-uv
	@$(MAKE) --quiet install-dependencies
	@echo "Installed the 'gridfm_demo' project! You can now activate your virtual environment with 'source .venv/bin/activate'."
	@echo "Note that this is a 'uv' project. Use 'uv add <package>' to install new dependencies and 'uv remove <package>' to remove them."

install-non-interactive:
	@$(MAKE) --quiet install-uv
	@$(MAKE) --quiet install-dependencies

install-uv:
	@if [ "$(shell which uv)" = "" ]; then \
		if [ "$(shell which rustup)" = "" ]; then \
			curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y; \
			echo "Installed Rust."; \
		fi; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
		echo "Installed uv."; \
    else \
		echo "Updating uv..."; \
		uv self update || true; \
	fi

install-pre-commit:
	@uv run pre-commit install
	@uv run pre-commit autoupdate

install-dependencies:
	@uv python install 3.12
	@uv sync --all-extras --all-groups --python 3.12

test:  ## Run tests
	@uv run pytest && uv run readme-cov

flower-data: data/federated_learning/client_0/case14_ieee/raw/bus_data.parquet data/federated_learning/client_1/case14_ieee/raw/bus_data.parquet

data/federated_learning/client_%/case14_ieee/raw/bus_data.parquet: src/federated_learning/config/datakit_client_%.yaml
	@uv run python src/federated_learning/scripts/generate_client_data.py --config $<

flower-clean-data:  ## Wipe generated client datasets
	@rm -rf data/federated_learning

flower-build:  ## Build the Flower Docker images (serverapp + clientapp)
	@docker compose -f src/federated_learning/docker-compose.yml build

flower-up: flower-data  ## Start the local Flower federation (SuperLink + 2 SuperNodes + apps)
	@docker compose -f src/federated_learning/docker-compose.yml up -d --build

flower-down:  ## Stop the local Flower federation
	@docker compose -f src/federated_learning/docker-compose.yml down

flower-run:  ## Submit the experiment to the running federation
	@uv run flwr run . local-deployment --stream

tree:  ## Print directory tree
	@tree -a --gitignore -I .git .

check:  ## Lint, format, and type-check the code
	@uv run pre-commit run --files $$(git ls-files --cached --others --exclude-standard)

format-markdown:
	## markdownlint-cli2 does not support wrapping lines at 88 characters, so we use Prettier to wrap lines at 88 characters and then use markdownlint-cli2 to fix any remaining issues.
	prettier --write --prose-wrap=always --print-width=88 *.md docs/**/*.md src/federated_learning/*.md
	markdownlint-cli2 --fix *.md docs/**/*.md src/federated_learning/*.md
