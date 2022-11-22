#! /usr/bin/env bash

set -eu -o pipefail

uvicorn ice.routes.app:app --port 8935 --reload
