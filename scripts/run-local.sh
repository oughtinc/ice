#! /usr/bin/env bash

set -eu -o pipefail

if docker help compose &>/dev/null; then
  docker="docker compose"
else
  docker="docker-compose"
fi

files=""
variant=""
args=""

if [ -n "${STREAMLIT:-}" ]; then
  variant="streamlit"
fi

if [ -n "${TORCH:-}" ]; then
  if [ -n "${STREAMLIT:-}" ]; then
    echo "Cannot specify both STREAMLIT and TORCH"
    exit 1
  fi
  variant="torch"
fi

if [ -n "${variant}" ]; then
  files="${files} -f docker-compose.${variant}.yml"
  if [ -n "${BUILD:-}" ]; then
    files="${files} -f docker-compose.build-${variant}.yml"
  fi
elif [ -n "${BUILD:-}" ]; then
  files="${files} -f docker-compose.build.yml"
fi

if [ -n "${BUILD:-}" ]; then
  args="${args} --build"
fi

$docker -f docker-compose.yml $files up $args "$@"
