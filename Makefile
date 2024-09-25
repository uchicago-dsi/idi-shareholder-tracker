# Command shortcuts for building and running Docker Compose services

# Change current working directory
mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
current_dir := $(notdir $(patsubst %/,%,$(dir $(mkfile_path))))
current_abs_path := $(subst Makefile,,$(mkfile_path))
$(shell cd $(current_abs_path) > /dev/null)

# Export environment variables used by all targets
.EXPORT_ALL_VARIABLES:
DOCKER_PLATFORM := $(shell . ./set_arch.sh)
COMPOSE_PROJECT := "shareholder-tracker"

# Build Docker images and run containers in different modes
run-backend:
	docker compose -p $(COMPOSE_PROJECT) up --build