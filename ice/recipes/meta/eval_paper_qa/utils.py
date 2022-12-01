from collections.abc import Callable
from collections.abc import Sequence

from ice.cache import diskcache
from ice.metrics.rouge import matches
from ice.paper import Paper
from ice.recipes.meta.eval_paper_qa.types import PaperQaGoldStandard


@diskcache()
async def identify_gs_str(
    candidates: Sequence[str], gs_quotes: Sequence[str], lcs_threshold: float = 0.7
) -> Sequence[str]:
    positive_selections = set[str]()
    for gs_quote in gs_quotes:
        gs_matches = await matches(
            hypotheses=candidates, references=[gs_quote], lcs_threshold=lcs_threshold
        )
        for candidate in gs_matches:
            positive_selections.add(candidate)
    return [cand for cand in candidates if cand in positive_selections]


async def convert_demonstration_example(
    example: PaperQaGoldStandard,
    paper_division_func: Callable[[Paper], Sequence[str]],
) -> PaperQaGoldStandard:
    paper_parts = paper_division_func(example.paper)
    return PaperQaGoldStandard(
        paper=example.paper,
        question=example.question,
        gold_answer=example.gold_answer,
        short_gold_answer=example.short_gold_answer,
        gold_support=(await identify_gs_str(paper_parts, example.gold_support)),
    )
