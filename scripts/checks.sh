#! /usr/bin/env bash

set -eux -o pipefail

BUILD=1 DETACH=1 scripts/run-local.sh
docker compose exec ice poetry run pre-commit run --all-files
docker compose exec ice poetry run pytest --cov . -x
