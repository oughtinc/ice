import itertools
from collections.abc import Sequence
from typing import Optional

from pydantic import BaseModel
from tqdm import tqdm

from ice.metrics.gold_standards import get_gold_standard
from ice.metrics.gold_standards import get_gold_standards
from ice.metrics.gold_standards import GoldStandard
from ice.metrics.gold_standards import GoldStandardSplit
from ice.paper import Paper
from ice.recipes.consort_flow.types import ConsortFlow
from ice.recipes.consort_flow.types import SampleSize
from ice.recipes.program_search.nodes.decontext.decontextualize import paper_decontext
from ice.recipes.program_search.nodes.select.dynamic import best_negative_example
from ice.recipes.program_search.nodes.select.dynamic import first_positive_example
from ice.recipes.program_search.nodes.select.dynamic import make_examples
from ice.recipes.program_search.nodes.select.dynamic import SelectionExample
from ice.recipes.program_search.nodes.select.prompts import render_selection_example
from ice.recipes.program_search.nodes.select.prompts import RenderableSelectionExample
from ice.recipes.program_search.types import Selection
from ice.recipes.program_search.types import sentences
from ice.settings import settings
from ice.utils import map_async


def get_consort_gs(document_id: str) -> Optional[GoldStandard[ConsortFlow]]:
    return get_gold_standard(
        document_id=document_id,
        question_short_name="consort_flow",
        model_type=ConsortFlow,
    )


def consort_gs_split(
    split: GoldStandardSplit, question_short_name: str
) -> Sequence[GoldStandard[ConsortFlow]]:
    golds = get_gold_standards(
        question_short_name=question_short_name, model_type=ConsortFlow
    )
    return [gs for gs in golds if gs.split == split]


def paper_to_allocation_gold_standards(
    paper: Paper,
) -> Sequence[tuple[str, Sequence[Selection], Sequence[str]]]:
    gs = get_consort_gs(paper.document_id)
    texts = sentences(paper)
    if not gs or not gs.parsed_answer:
        return []

    return [
        (
            f"The {exp.name} experiment included {len(exp.arms or [])} arms: {', '.join((arm.name for arm in exp.arms or []))}. How many participants were initially allocated to the {arm.name} arm of the {exp.name} experiment?",
            texts,
            arm.allocated.quotes
            if arm.allocated and isinstance(arm.allocated, SampleSize)
            else [],
        )
        for exp in gs.parsed_answer.experiments
        for arm in (exp.arms or [])
    ]


# def paper_to_experiments_gold_standard(paper: Paper) -> Sequence[tuple[str, Sequence[Selection], Sequence[str]]]:
#     gs = get_ea_gs(paper.document_id)
#     texts = sentences(paper)
#     if not gs or not gs.parsed_answer:
#         return []


class GoldStandardExample(BaseModel):
    question: str
    texts: Sequence[Selection]
    gs_quotes: Sequence[str]


def gold_standard_examples(
    papers: Sequence[Paper],
) -> Sequence[GoldStandardExample]:
    return [
        GoldStandardExample(question=question, texts=texts, gs_quotes=gs_quotes)
        for result in tqdm(
            map(paper_to_allocation_gold_standards, papers),
            desc="Creating gold standard examples",
            total=len(papers),
        )
        for question, texts, gs_quotes in result
    ]


def download_papers(
    split: str = "validation", question_short_name: str = "consort_flow"
):
    paper_dir = settings.PAPER_DIR
    doc_ids = {p.document_id for p in consort_gs_split(split, question_short_name)}  # type: ignore[arg-type]
    paper_files = [f for f in paper_dir.iterdir() if f.name in doc_ids]
    return [
        Paper.load(f)
        for f in tqdm(paper_files, desc="Loading papers for gold standards")
    ]


async def gold_standard_examples_except(
    document_ids_to_exclude: Sequence[str],
    require_quotes: bool = True,
    limit: Optional[int] = None,
    decontextualize: bool = False,
) -> Sequence[GoldStandardExample]:
    blocklist_ids = set(document_ids_to_exclude)
    papers = [p for p in download_papers() if p.document_id not in blocklist_ids]
    papers = papers[: (limit or len(papers))]
    if decontextualize:
        papers = [(await paper_decontext(p)) for p in papers]
    gses = gold_standard_examples(papers)
    return [gse for gse in gses if gse.gs_quotes or not require_quotes]


async def select_examples(
    examples: Sequence[GoldStandardExample], *, n: int, step: int, max_existing: int
) -> Sequence[tuple[str, SelectionExample]]:
    async def make_examples_for_paper(
        paper: GoldStandardExample,
    ) -> Sequence[tuple[str, SelectionExample]]:
        all_examples = await make_examples(
            texts=paper.texts,
            gs_quotes=paper.gs_quotes,
            n=n,
            step=step,
            max_existing=max_existing,
        )
        first_positive = first_positive_example(all_examples)
        best_negative = best_negative_example(all_examples)
        found_examples = filter(None, (first_positive, best_negative))
        return [(paper.question, found_example) for found_example in found_examples]

    all_examples = await map_async(examples, make_examples_for_paper)
    return list(itertools.chain.from_iterable(all_examples))


def narrow_examples(
    examples: Sequence[tuple[str, SelectionExample]], max_examples: int
):
    # TODO: Get much fancier about selectiong examples that make good prompts
    example_types: set[str] = set()
    examples_to_keep: list[tuple[str, SelectionExample]] = []
    for question, example in examples:
        if len(examples_to_keep) == max_examples:
            break
        example_type = (
            f"{example.selection[0].p.document_id}-{bool(example.positive_idxs)}"
        )
        if example_type in example_types:
            continue
        example_types.add(example_type)
        examples_to_keep.append((question, example))

    return examples_to_keep


async def selection_examples_for_paper(
    paper: Paper,
    max_examples: int = 5,
    limit_papers: Optional[int] = None,
    decontextualize: bool = False,
) -> list[RenderableSelectionExample]:
    golds = await gold_standard_examples_except(
        [paper.document_id], limit=limit_papers, decontextualize=decontextualize
    )
    examples = await select_examples(golds, n=5, step=5, max_existing=3)
    return [
        render_selection_example(question=question, example=example)
        for question, example in narrow_examples(examples, max_examples=max_examples)
    ]
