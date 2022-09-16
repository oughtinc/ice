#! /usr/bin/env bash

set -eux -o pipefail

START_FRONTEND=false ./scripts/run-local.sh

docker compose exec -- backend poetry run pre-commit run --all-files
docker compose exec -- backend poetry run pytest --cov . -x
