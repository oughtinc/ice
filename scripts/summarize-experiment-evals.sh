#! /usr/bin/env bash
echo $@

docker compose exec ice python -m ice.evaluation.summarize_experiment_evals "$@"
