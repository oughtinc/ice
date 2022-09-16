#! /usr/bin/env bash

set -eu -o pipefail

START_FRONTEND=false scripts/run-local.sh

docker compose exec backend python -m main "$@"
