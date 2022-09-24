#! /usr/bin/env bash

set -ex -o pipefail

# https://superuser.com/questions/403263/how-to-pass-bash-script-arguments-to-a-subshell
extra_pytest_args="$(printf "${1+ %q}" "$@")" # Note: this will have a leading space before the first arg

# Run tests
docker compose exec ice poetry run pytest -v -ra --strict-markers$extra_pytest_args
