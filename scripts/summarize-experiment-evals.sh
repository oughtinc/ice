#! /usr/bin/env bash
echo $@

START_FRONTEND=false ./scripts/run-local.sh

docker compose exec -- backend python -m summarize_experiment_evals "$@"
