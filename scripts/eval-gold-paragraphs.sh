# ! /usr/bin/env bash

START_FRONTEND=false ./scripts/run-local.sh

docker compose exec -- backend python -m eval_gold_paragraphs $@
