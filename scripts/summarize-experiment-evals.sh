#! /usr/bin/env bash
echo $@

docker compose exec ice python -m summarize_experiment_evals "$@"
