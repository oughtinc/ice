import importlib
import json

from collections.abc import Callable
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from ruamel.yaml import YAML
from structlog.stdlib import get_logger

from ice.evaluation.evaluation_report import latest_commit_hash
from ice.metrics.qasper import token_f1_score
from ice.recipe import recipe
from ice.recipes.meta.eval_paper_qa.types import AnswerEvalMethod
from ice.recipes.meta.eval_paper_qa.types import AnswerType_contra
from ice.recipes.meta.eval_paper_qa.types import ClassificationEvalMethod
from ice.recipes.meta.eval_paper_qa.types import PaperQaGoldStandard
from ice.recipes.meta.eval_paper_qa.types import PaperQaMethod
from ice.recipes.meta.eval_paper_qa.types import SequenceGenerationEvaluation
from ice.recipes.meta.eval_text_classification import BinaryClassificationMetrics
from ice.settings import OUGHT_ICE_DIR
from ice.trace import trace
from ice.utils import map_async

yaml = YAML(typ="safe")
log = get_logger()


async def eval_paper_qa_method(
    method: PaperQaMethod[AnswerType_contra],
    paper_qa_generator: Callable[[str], Iterable[PaperQaGoldStandard]],
    answer_eval_method: AnswerEvalMethod[AnswerType_contra],
    classification_eval_method: ClassificationEvalMethod,
    split: str,
    max_concurrency: int = 10,
):
    @trace
    async def run_and_eval_method(
        qa_details: PaperQaGoldStandard,
    ) -> SequenceGenerationEvaluation[AnswerType_contra]:
        answer = await method(
            qa_details.paper, qa_details.question, qa_details.gold_support
        )
        correct, detail = await answer_eval_method(
            question=qa_details.question,
            ground_truth=qa_details.gold_answer,
            prediction=answer.answer,
        )
        metrics = await classification_eval_method(
            candidates=answer.support_candidates,
            predictions=answer.support_labels,
            ground_truth=qa_details.gold_support,
            scores=answer.support_scores,
        )
        answer_for_f1 = answer.answer
        if isinstance(answer_for_f1, str):
            generation_f1 = token_f1_score(
                prediction=answer_for_f1, ground_truth=qa_details.gold_answer
            )
        else:
            generation_f1 = 0.0
        return SequenceGenerationEvaluation(
            question=qa_details.question,
            document_id=qa_details.paper.document_id,
            correct=correct,
            detail=detail,
            metrics=metrics,
            generated_answer=answer.answer,
            gold_answer=qa_details.gold_answer,
            support=[
                text
                for lab, text in zip(answer.support_labels, answer.support_candidates)
                if lab
            ],
            generation_f1_score=generation_f1,
        )

    paper_qa_details = list(paper_qa_generator(split))

    results = await map_async(
        paper_qa_details, run_and_eval_method, max_concurrency=max_concurrency
    )

    scores = [r.correct for r in results]
    metrics = [r.metrics for r in results]
    f1 = [r.generation_f1_score for r in results]

    # only aggregate where there is gold support (somewhat arbitrary choice but more informative)
    metrics_under_support = [
        m for m, qa_details in zip(metrics, paper_qa_details) if qa_details.gold_support
    ]
    aggregated_metrics = BinaryClassificationMetrics.aggregate(metrics_under_support)

    return (
        sum(scores) / len(scores) if scores else 0,
        results,
        aggregated_metrics,
        sum(f1) / len(f1) if f1 else 0.0,
    )


def load_object(location: str) -> Any:
    parent_module, _, child_name = location.rpartition(".")
    module = importlib.import_module(parent_module)
    child = getattr(module, child_name)
    return child


class _PaperQaArgs(BaseModel):
    split: str
    paper_qa_generator: str  # Callable[[str], Iterable[PaperQaGoldStandard]]
    method: str
    answer_eval_method: str
    classification_eval_method: str


class PaperQaEvalConfig(BaseModel):
    name: str
    results_json: str | None = None
    pr_curve: str | None = None
    args: _PaperQaArgs


def ensure_dir(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


async def run_from_config(config: PaperQaEvalConfig) -> dict:
    score, results, agg_metrics, f1 = await eval_paper_qa_method(
        method=load_object(config.args.method),
        split=config.args.split,
        answer_eval_method=load_object(config.args.answer_eval_method),
        classification_eval_method=load_object(config.args.classification_eval_method),
        paper_qa_generator=load_object(config.args.paper_qa_generator),
    )
    metrics = agg_metrics.as_dict()
    results_line = dict(
        config=config.dict(),
        ice_commit=latest_commit_hash(),
        score=score,
        results=[r.as_dict() for r in results],
        metrics=metrics,
        pr_thresholds=agg_metrics.pr_thresholds(),
        generation_f1_score=f1,
    )
    if config.results_json:
        with ensure_dir(OUGHT_ICE_DIR / config.results_json).open("w") as r:
            r.writelines([json.dumps(results_line, indent=2, sort_keys=True)])
    if config.pr_curve:
        agg_metrics.save_pr_curve(OUGHT_ICE_DIR / config.pr_curve)
    return results_line


async def eval_from_config(config_path: str):
    configs = yaml.load(Path(config_path))

    parsed = [PaperQaEvalConfig.parse_obj(configs[0])]
    for prev_idx, config in enumerate(configs[1:]):
        prev_args = parsed[prev_idx].args.dict()
        config["args"] = prev_args | config["args"]
        parsed.append(PaperQaEvalConfig.parse_obj(config))

    return await map_async(parsed, run_from_config, max_concurrency=1)


recipe.main(eval_from_config)
