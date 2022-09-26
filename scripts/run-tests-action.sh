#! /usr/bin/env bash

set -eux -o pipefail

docker compose -f docker-compose.yml -f docker-compose.build.yml -f docker-compose.action.yml up -d
docker compose exec ice pytest --cov . -x
