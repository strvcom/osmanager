SHELL = /bin/bash

PROJ_NAME = strv-ds-opensearch-manager

RUN_OPENSEARCH = docker-run-opensearch
RUN_DEV_ENV = dev-env
CLEAN_ALL = docker-clean-all
CLEAN_CONTAINERS = docker-clean-containers
CLEAN_VOLUMES = docker-clean-volumes

.PHONY: help $(RUN_OPENSEARCH) $(CLEAN_ALL) $(CLEAN_CONTAINERS)
.PHONY: $(CLEAN_VOLUMES)
BUILD_DIR = ./build

define HELP_MSG
Help:
    Typical workflow scenario is (see also target descriptions bellow):

    1. Open terminal, run 'make ${RUN_OPENSEARCH}' .
    2. Open another terminal, run 'make ${RUN_DEV_ENV}' .
    3. Develop and build some great stuff.
    4. Close both terminals, run 'make $(CLEAN_ALL)', get some sleep.

    For other scenarios, run 'make <target>' where <target> is:
    - '${RUN_OPENSEARCH}' -- run OpenSearch containers.
    - '${RUN_DEV_ENV}' -- run /bin/bash in a develompent environment from Dockerfile.
    - '$(CLEAN_CONTAINERS)' -- clean docker containers.
    - '$(CLEAN_VOLUMES)' -- clean OpenSearch docker volumes, the containers
       have to be removed first.
    - '$(CLEAN_ALL)' -- clean all, docker containers and volumes.
endef
# Note: This export is here only to pass a multi-line variable to shell
# to prevent problems with multiline Makefile variable expansion.
export HELP_MSG
help:
	@echo "$$HELP_MSG"

$(RUN_OPENSEARCH):
	docker-compose up

# When the Dockerfile or .env changes rebuild the dev image before running
REBUILD_DEV_TARGET = $(BUILD_DIR)/rebuild-dev-env
$(RUN_DEV_ENV): $(REBUILD_DEV_TARGET)
	docker-compose run --rm dev-env

$(REBUILD_DEV_TARGET): $(BUILD_DIR) Dockerfile .env
	docker-compose build dev-env
	touch $(REBUILD_DEV_TARGET)

# If there is no .env file, create an empty one
.env:
	touch .env

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

# Clean docker containers and volumes
# TODO clever docker images removal
$(CLEAN_ALL): $(CLEAN_CONTAINERS) $(CLEAN_VOLUMES)

$(CLEAN_CONTAINERS):
	rm $(REBUILD_DEV_TARGET)
	docker-compose rm

$(CLEAN_VOLUMES):
	docker volume rm `docker volume ls -f name=$(PROJ_NAME)_opensearch-data --format "{{.Name}}"`
