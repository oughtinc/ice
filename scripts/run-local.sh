#! /usr/bin/env bash

set -eu -o pipefail

if docker compose -h >/dev/null; then
  docker="docker compose"
else
  docker="docker-compose"
fi

if command -v nvidia-smi &>/dev/null; then
  extra="-f docker-compose-nvidia.yaml"
else
  extra=""
fi

CI=${CI:-false}

if [ "$CI" = true ]; then
    ci_args="--no-recreate --quiet-pull"
else
    ci_args=""
fi

$docker -f docker-compose.yaml $extra up -d $ci_args

START_FRONTEND=${START_FRONTEND:-true}

if [ "$START_FRONTEND" = true ]; then
  pushd ui
    npm run dev
  popd
fi
