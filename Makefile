SHELL = /bin/bash
D_RUN_TARGET = docker-run-opensearch
CLEAN_ALL_TARGET = docker-clean-all
CLEAN_CONTAINERS_TARGET = docker-clean-containers
CLEAN_VOLUMES_TARGET = docker-clean-volumes
.PHONY: help $(DEV_TARGET) $(CLEAN_ALL_TARGET) $(CLEAN_CONTAINERS_TARGET)
.PHONY: $(CLEAN_VOLUMES_TARGET)

define HELP_MSG
Help: Run 'make <target>' where <target> is:
    - '${D_RUN_TARGET}' -- run OpenSearch containers.
    - '$(CLEAN_CONTAINERS_TARGET)' -- clean OpenSearch docker containers.
    - '$(CLEAN_VOLUMES_TARGET)' -- clean OpenSearch docker volumes, the containers
       have to be removed first.
    - '$(CLEAN_ALL_TARGET)' -- clean all OpenSearch docker data.
endef
# Note: This export is here only to pass a multi-line variable to shell
# to prevent problems with multiline Makefile variable expansion.
export HELP_MSG
help:
	@echo "$$HELP_MSG"

$(D_RUN_TARGET):
	docker-compose -f docker-compose-opensearch.yml up

$(CLEAN_ALL_TARGET): $(CLEAN_CONTAINERS_TARGET) $(CLEAN_VOLUMES_TARGET)

# TODO replace "opensearch" string by more specific variant
$(CLEAN_CONTAINERS_TARGET):
	docker container rm `docker ps -a -q --filter 'name=opensearch'`

PROJ_NAME = strv-ds-opensearch-manager
$(CLEAN_VOLUMES_TARGET):
	docker volume rm `docker volume ls -f name=$(PROJ_NAME)_opensearch-data --format "{{.Name}}"`
