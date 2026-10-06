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
	prettier --write --prose-wrap=always --print-width=88 *.md docs/**/*.md federations/*.md
	markdownlint-cli2 --fix *.md docs/**/*.md federations/*.md

tree:  ## Print directory tree
	@tree -a --gitignore -I .git .

FEDERATION ?= case14_2clients
EXPERIMENT ?= fedavg
FEDERATION_DIR := federations/$(FEDERATION)
COMPOSE := docker compose -f $(FEDERATION_DIR)/compose.yml
FEDERATION_CLIENT_DIRS := $(patsubst $(FEDERATION_DIR)/datakit_config/%.yaml,\
	$(FEDERATION_DIR)/data/%,$(wildcard $(FEDERATION_DIR)/datakit_config/client_*.yaml))

flower-data: $(FEDERATION_CLIENT_DIRS)

$(FEDERATION_DIR)/data/client_%: $(FEDERATION_DIR)/datakit_config/client_%.yaml
	@uv run python scripts/generate_data.py --config $<

flower-build:  ## Build the Flower Docker images (serverapp + clientapp)
	@$(COMPOSE) build

flower-up: flower-data  ## Start the federation FEDERATION
	@mkdir -p outputs
	@$(COMPOSE) up -d --build

flower-run:  ## Submit EXPERIMENT to the running federation
	@uv run flwr run . local-deployment \
		--run-config "experiment='$(EXPERIMENT)'" --stream

flower-down:  ## Stop the federation FEDERATION
	@$(COMPOSE) down

flower-clean-data:  ## Wipe the generated client datasets of FEDERATION
	@rm -rf $(FEDERATION_DIR)/data
