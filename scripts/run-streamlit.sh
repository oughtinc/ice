#! /usr/bin/env bash

set -eux -o pipefail

docker compose exec ice bash -c "export PYTHONPATH=/code && streamlit run streamlits/home.py --server.address 0.0.0.0 --server.port 9000"
