#! /usr/bin/env bash

set -eux -o pipefail

uvicorn ice.web:app --host 0.0.0.0 --port 8000 --reload
