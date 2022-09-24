#! /usr/bin/env bash

set -eu -o pipefail

docker compose exec ice python -m main "$@"
