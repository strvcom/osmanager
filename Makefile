DEV_TARGET = run-opensearch
.PHONY: all $(DEV_TARGET) clean-all clean-containers clean-volumes

all:
	@echo "Run 'make ""${DEV_TARGET}""' to run the OpenSearch containers."

$(DEV_TARGET):
	docker-compose -f docker-compose-opensearch.yml up

clean-all: clean-containers clean-volumes

# TODO FIXME
# Replace "opensearch" and "opensearch-data1" by some variable
clean-containers:
	docker container rm `docker ps -a -q --filter 'name=opensearch'`

clean-volumes:
	docker volume rm `docker volume ls -f name=opensearch-data1 --format "{{.Name}}"`


