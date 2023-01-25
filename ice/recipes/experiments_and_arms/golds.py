from collections.abc import Sequence
from typing import Optional

from ice.metrics.gold_standards import get_gold_standard
from ice.metrics.gold_standards import GoldStandard
from ice.recipes.experiments_and_arms.types import ExperimentsArms


def get_ea_gs(document_id: str) -> Optional[GoldStandard[ExperimentsArms]]:
    return get_gold_standard(
        document_id=document_id,
        question_short_name="experiments_arms",
        model_type=ExperimentsArms,
    )


def list_gs_experiments(document_id: str) -> Optional[Sequence[str]]:
    gs = get_ea_gs(document_id)
    if gs is None or gs.parsed_answer is None:
        return None
    return [experiment.name for experiment in gs.parsed_answer.experiments]


def count_gs_experiments(document_id: str) -> Optional[int]:
    experiments = list_gs_experiments(document_id)
    return len(experiments) if experiments is not None else None
