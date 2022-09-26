#! /usr/bin/env bash

set -eux -o pipefail

BUILD=1 DETACH=1 scripts/run-local.sh
docker compose exec ice pytest --cov . -x
