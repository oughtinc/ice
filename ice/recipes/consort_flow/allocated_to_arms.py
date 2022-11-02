from curses import window
from itertools import repeat
from typing import (
    Any,
    Awaitable,
    Callable,
    Iterable,
    Literal,
    Mapping,
    Sequence,
    Protocol,
)
from ice.metrics.gold_standards import GoldStandard, ModelType
from ice.recipe import Recipe, recipe
from ice.recipes.consort_flow.golds import (
    download_papers,
    get_consort_gs,
    selection_examples_for_paper,
)
from ice.recipes.consort_flow.quick_question_driven_eval import quick_eval
from ice.recipes.primer.paper_qa import answer_for_paper
from ice.recipes.program_search.nodes.answer.answer import simple_answer
from ice.recipes.program_search.nodes.augment_question.augment_question import (
    augment_question,
)
from ice.recipes.program_search.nodes.decontext.decontextualize import (
    PaperDecontext,
    autoregressive_decontext,
    local_decontext,
)
from ice.recipes.program_search.nodes.prune.prune import prune
from ice.recipes.program_search.nodes.select.select import (
    as_strings,
    windowed_select,
    select_metrics,
    aggregate_select_metrics,
)
from ice.paper import Paper
from ice.recipes.experiments_and_arms.golds import get_ea_gs
from ice.recipes.program_search.types import (
    Decontext,
    Selection,
    sentences,
    text_to_selection,
)
from ice.recipes.consort_flow.types import ConsortFlow, SampleSize


from ice.recipes.single_prompt import SinglePrompt
from ice.utils import map_async


QUESTION_SHORT_NAME = "adherence"

DEFAULT_ANSWER_CLASSIFICATION: None = None

AI_PROMPT: str = "\nAssistant:"

HUMAN_PROMPT: str = "\nHuman:"


class PaperQaMethod(Protocol):
    async def __call__(
        self,
        __paper: Paper,
        __question: str,
        __gold_support: Sequence[str] | None = None,
    ) -> tuple[str, Mapping[str, int | float]]:
        ...


async def not_mentioned(
    paper: Paper, question: str, gold: Sequence[str] | None = None
) -> tuple[str, Mapping[str, int | float]]:
    return "Not mentioned", {}


async def paper_qa_baseline(
    paper: Paper, question, gold: Sequence[str] | None = None
) -> tuple[str, Mapping[str, int | float]]:
    all_paras = [str(p) for p in paper.paragraphs]
    answer, predicted_paras = await answer_for_paper(paper, question, top_n=1)
    metrics = await select_metrics(all_paras, [p in predicted_paras for p in all_paras], gold or [])
    return answer, metrics


async def eval_method(
    method: PaperQaMethod,
    metrics_aggregator: Callable[[Sequence[Mapping]], Mapping],
    question_and_answer_func: Callable[
        [GoldStandard[ConsortFlow]], Iterable[tuple[str, str, Sequence[str]]]
    ],
    split: str,
    max_concurrency: int = 10,
):

    # TODO: make configurable
    papers = download_papers(split)[:5]

    async def run_eval(input_data: tuple[Paper, str, str, Sequence[str]]) -> tuple[bool, Mapping]:
        paper, question, gold_answer, gold_support = input_data
        generated, metrics = await method(paper, question, gold_support)
        return await quick_eval(
            question=question, gold=gold_answer, generated=generated
        ), metrics

    eval_data = []
    gold_supports: list[Sequence[str]] = []

    for paper in papers:
        gold = get_consort_gs(paper.document_id)
        if not gold:
            continue
        for question, gold_answer, gold_support in question_and_answer_func(gold):
            eval_data.append((paper, question, gold_answer, gold_support))
            gold_supports.append(gold_support)

    results = await map_async(eval_data, run_eval, max_concurrency=max_concurrency)
    scores = [r[0] for r in results]
    metrics = [r[1] for r in results]

    # only aggregate where there is gold support (somewhat arbitrary choice but more informative)
    metrics_under_support = [m for m, gs in zip(metrics, gold_supports) if gs]
    aggregated_metrics = metrics_aggregator(metrics_under_support)


    return sum(scores) / len(scores), scores, aggregated_metrics


def allocated_questions_and_answers(
    gold: GoldStandard[ConsortFlow],
) -> Iterable[tuple[str, str, Sequence[str]]]:
    if not gold.parsed_answer:
        return
    for exp in gold.parsed_answer.experiments:
        for arm in exp.arms or []:
            if not arm.allocated:
                continue
            question = f"The {exp.name} experiment included {len(exp.arms or [])} arms: {', '.join((arm.name for arm in exp.arms or []))}. How many participants were initially allocated to the {arm.name} arm of the {exp.name} experiment?"
            answer = (
                arm.allocated
                if isinstance(arm.allocated, str)
                else arm.allocated.n or "Unknown"
            )
            support = arm.allocated.quotes if arm.allocated and isinstance(arm.allocated, SampleSize) else []
            yield question, str(answer), support


async def eval_paper_qa_baseline():
    return await eval_method(
        paper_qa_baseline, aggregate_select_metrics, allocated_questions_and_answers, split="validation"
    )


async def eval_decontext_and_select():
    return await eval_method(
        DecontextAndSelect(mode="machine").decontext_and_select,
        aggregate_select_metrics,
        allocated_questions_and_answers,
        split="validation",
    )


async def eval_not_mentioned_baseline():
    return await eval_method(
        not_mentioned, aggregate_select_metrics, allocated_questions_and_answers, split="validation"
    )


def baseline(question: str):
    template = f"""
    {HUMAN_PROMPT} I'm trying to evaluate some RCTs. I've been told I should answer the question: "{question}". Can you help me with this?
    {AI_PROMPT} Yes, I can help you with this, if you provide text from the paper in question.
    {HUMAN_PROMPT} Here's the text of the paper I've been thinking about. Can you read it and identify what it says, if anything, to answer the question: "{question}"

    {{paper_text}}
    {AI_PROMPT} First, I'll identify all the parts of the paper that help answer the question. Then, I'll summarize the answer to the question."""

    class InitialSampleSimple(SinglePrompt):
        agent_str = "instruct"
        max_tokens = 3500
        qa_prompt_template: str = template
        question_short_name: str = QUESTION_SHORT_NAME
        default_answer_classification = DEFAULT_ANSWER_CLASSIFICATION

    return InitialSampleSimple


class DecontextAndSelect(Recipe):
    # async def decontext_prune_and_select(self, paper: Paper, question: str):
    #     sents = sentences(paper)
    #     texts = await windowed_select(
    #         question=question, texts=list(paper.sentences()), n=5, step=2
    #     )
    #     pruned = await prune(question=question, texts=list(texts), max_to_keep=8)
    #     best_new_question, all_new_questions = await augment_question(
    #         question=question, current_texts=pruned
    #     )
    #     pruned_selections = map(text_to_selection, pruned, repeat(sents))
    #     sentences_in_abstract = sum(
    #         [len(p.sentences) for p in paper.paragraphs if p.section_type == "abstract"]
    #     )
    #     abstract = sents[:sentences_in_abstract]
    #     all_decontexted: list[Decontext] = []
    #     for pruned_selection in pruned_selections:
    #         before_context, after_context = pruned_selection.context(5, 5)
    #         all_context = abstract + before_context + after_context
    #         decontexted = await local_decontext(
    #             all_context, pruned_selection, all_new_questions
    #         )
    #         all_decontexted.append(decontexted)
    #     answer = await simple_answer(question, [str(d) for d in all_decontexted])
    #     return answer

    async def decontext_and_select(
        self, paper: Paper, question: str, gold: Sequence[str] | None = None
    ):
        """Answer the question by first enriching the paper by adding context autoregressively,
        then selecting sentences needed to answer the question.

        Args:
            paper (Paper): Paper to answer the question about
            question (str): The question

        Returns:
            answer: str
        """
        decontexted = await (PaperDecontext(mode=self.mode).run(paper))
        examples = await selection_examples_for_paper(
            paper=paper, max_examples=8, limit_papers=8, decontextualize=False
        )

        texts = list(decontexted.sentences())

        selections = await windowed_select(
            question=question,
            texts=list(decontexted.sentences()),
            n=5,
            step=5,
            examples=examples,
        )
        metrics = await select_metrics(list(paper.sentences()), selections, gold or [])
        answer = await simple_answer(question, as_strings(selections, texts))
        return answer, metrics

    async def run(self, paper: Paper):
        """Identify the initial sample size for each trial arm, for each experiment.

        Return the gold standard (if it exists), along with the answer from a baseline end-to-end approach and a decompositional approach.

        Args:
            paper (Paper): Paper

        Returns:
            tuple[int | Literal["Unclear"] | None, str, str]: gold standard, baseline approach answer, decomposed answer
        """
        gs = get_consort_gs(paper.document_id)
        assert gs and gs.parsed_answer

        evals = []

        for question, gold_answer, gold_support in allocated_questions_and_answers(gs):

            baseline_answer = await (
                baseline(question)(mode=self.mode).run(paper=paper)
            )

            # answer = await self.decontext_prune_and_select(
            #     paper=paper, question=question
            # )
            answer, metrics = await self.decontext_and_select(paper=paper, question=question)

            decomp_correct = await quick_eval(
                question=question,
                gold=gold_answer,
                generated=answer,
            )
            evals.append(decomp_correct)
        return evals


# recipe.main(eval_paper_qa_baseline)
recipe.main(eval_decontext_and_select)
# recipe.main(eval_not_mentioned_baseline)
