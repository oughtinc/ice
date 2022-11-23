# ! /usr/bin/env bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ICE_DIR=${SCRIPT_DIR}/../
ELICIT_NEXT_DIR=$1

mkdir -p ${ICE_DIR}/data/in_app_qa_results

cd ${ELICIT_NEXT_DIR}
os=$(uname -s | tr '[:upper:]' '[:lower:]')
docker compose -f docker-compose.yaml -f docker-compose.$os.yaml up -d
docker compose exec api bash -c 'LOG_LEVEL=warn TOKENIZERS_PARALLELISM=false poetry run python -m api.eval.main' > ${ICE_DIR}/data/in_app_qa_results/qa_eval_output.csv

cd ${ICE_DIR}
python -m ice.evaluation.summarize_experiment_evals data/in_app_qa_results/qa_eval_output.csv
