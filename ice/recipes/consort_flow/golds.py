from typing import Literal
from ice.metrics.gold_standards import (
    GoldStandard,
    GoldStandardSplit,
    get_gold_standard,
    get_gold_standards,
)
from ice.recipes.consort_flow.types import ConsortFlow


def get_consort_gs(document_id: str) -> GoldStandard[ConsortFlow] | None:
    return get_gold_standard(
        document_id=document_id,
        question_short_name="consort_flow",
        model_type=ConsortFlow,
    )


def consort_gs_split(split: GoldStandardSplit):
    golds = get_gold_standards(
        question_short_name="consort_flow", model_type=ConsortFlow
    )
    return [gs for gs in golds if gs.split == split]