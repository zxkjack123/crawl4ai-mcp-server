COMPOSE_FILE := docker/docker-compose.yml
ENV_FILE ?= .env
ENV_FILE_FLAG := $(if $(wildcard $(ENV_FILE)),--env-file $(ENV_FILE),)
COMPOSE := docker compose $(ENV_FILE_FLAG) --file $(COMPOSE_FILE)
SERVICE := crawl4ai-http
HOST_PORT := 18080

.PHONY: docker-build docker-up docker-down docker-logs docker-ps docker-health docker-restart

## Build the HTTP bridge image
docker-build:
	$(COMPOSE) build $(SERVICE)

## Start the HTTP bridge in detached mode
docker-up:
	$(COMPOSE) up -d $(SERVICE)

## Stop the service and remove containers
docker-down:
	$(COMPOSE) down --remove-orphans

## Tail container logs
docker-logs:
	$(COMPOSE) logs -f $(SERVICE)

## Show compose service status
docker-ps:
	$(COMPOSE) ps

## Health check against the exposed host port
docker-health:
	curl -fsS http://localhost:$(HOST_PORT)/health | python3 -m json.tool

## Restart the container (down + up)
docker-restart: docker-down docker-up
