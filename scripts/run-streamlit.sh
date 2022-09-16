#! /usr/bin/env bash

set -eux -o pipefail

START_FRONTEND=false ./scripts/run-local.sh

docker compose exec -- backend /bin/bash -c "export PYTHONPATH=/code && streamlit run streamlits/home.py --server.address 0.0.0.0 --server.port 9000"
