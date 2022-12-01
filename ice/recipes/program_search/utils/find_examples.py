from collections.abc import Mapping
from collections.abc import Sequence
from enum import Enum
from typing import TypeVar

from ice.metrics.base import Sample
from ice.metrics.nubia import Nubia
from ice.metrics.nubia import NubiaResponse
from ice.metrics.rouge import matches
from ice.metrics.rouge import rouge_texts
from ice.metrics.rouge import RougeResult
from ice.recipe import recipe
from ice.recipes.program_search.types import Selection


async def nubia_texts(
    hypotheses: Sequence[str], references: Sequence[str]
) -> Mapping[str, NubiaResponse]:
    scores = await Nubia().compute([Sample(left=hypotheses, right=references)])
    return {hyp: score for hyp, score in zip(hypotheses, scores[0])}


class SimilarityMethod(str, Enum):
    lcs = "rouge_l"
    r_1 = "rouge_1"
    r_2 = "rouge_2"
    r_3 = "rouge_3"


async def most_to_least_similar(
    hypotheses: Sequence[str],
    references: Sequence[str],
    by: SimilarityMethod = SimilarityMethod.lcs,
) -> Mapping[str, RougeResult]:
    scores = await rouge_texts(hypotheses=hypotheses, references=references)
    keys = sorted(
        hypotheses, key=lambda h: getattr(scores[h], by.value).r, reverse=True
    )
    return {key: scores[key] for key in keys}


async def best_distractor(hypotheses: Sequence[str], references: Sequence[str]) -> str:
    """The best distractor is the hypothesis with the highest rouge-L recall but rouge-3 == 0
    Where there is no rouge-3 == 0, return the lowest rouge-3

    Args:
        hypotheses (Sequence[str]): _description_
        references (Sequence[str]): _description_
    """
    sorted_by_lcs = await most_to_least_similar(
        hypotheses=hypotheses, references=references, by=SimilarityMethod.lcs
    )
    try:
        return next(
            filter(lambda key: sorted_by_lcs[key].rouge_3.r == 0, sorted_by_lcs)
        )
    except StopIteration:
        return min(sorted_by_lcs, key=lambda key: sorted_by_lcs[key].rouge_3.r)


async def rouge_distractor_scores(
    hypotheses: Sequence[str], references: Sequence[str], lcs_threshold: float = 0.7
) -> Mapping[str, float]:
    """Naive distractor scores: This is 0 where rouge lcs recall >= lcs_threshold or rouge-3 !=0 and otherwise rouge lcs threshold
    The idea is to find hyptheses with lots of overlap that are not actually saying the same thing.

    Semantic versions of this score should be considered instead.

    Args:
        hypotheses (Sequence[str]): _description_
        references (Sequence[str]): _description_

    Returns:
        Mapping[str, float]: _description_
    """
    # TODO: replace with model-based approach
    scores = await rouge_texts(hypotheses=hypotheses, references=references)
    return {
        text: (
            lambda s: s.rouge_l.r
            if s.rouge_l.r < lcs_threshold and s.rouge_3.r == 0
            else 0
        )(score)
        for text, score in scores.items()
    }


SelectionT_co = TypeVar("SelectionT_co", bound=Selection, covariant=True)


async def mark_gs(
    selections: Sequence[SelectionT_co],
    gs_quotes: Sequence[str],
    lcs_threshold: float = 0.7,
) -> Sequence[SelectionT_co]:
    selection_dict = {selection.original: selection for selection in selections}
    for gs_quote in gs_quotes:
        gs_matches = await matches(
            hypotheses=list(selection_dict.keys()),
            references=[gs_quote],
            lcs_threshold=lcs_threshold,
        )
        for selection in gs_matches:
            selection_dict[selection] = type(selection_dict[selection]).parse_obj(
                selection_dict[selection].dict(by_alias=True) | dict(is_gs=True)
            )
    return list(selection_dict.values())


recipe.main(mark_gs)
