from typing import Literal, Sequence
from ice.recipe import Recipe
from ice.recipes.program_search.nodes.answer.answer import simple_answer
from ice.recipes.program_search.nodes.decontext.decontextualize import (
    PaperDecontext,
    autoregressive_decontext,
)
from ice.recipes.program_search.nodes.select.select import windowed_select
from ice.paper import Paper
from ice.recipes.experiments_and_arms.golds import get_ea_gs
from ice.recipes.program_search.types import Selection, sentences


from ice.recipes.single_prompt import SinglePrompt


QUESTION_SHORT_NAME = "adherence"

DEFAULT_ANSWER_CLASSIFICATION: None = None

AI_PROMPT: str = "\nAssistant:"

HUMAN_PROMPT: str = "\nHuman:"


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


def paper_to_gold_standards(
    paper: Paper,
) -> Sequence[tuple[str, Sequence[Selection], Sequence[str]]]:
    gs = get_ea_gs(paper.document_id)
    texts = sentences(paper)
    if not gs or not gs.parsed_answer:
        return []

    return [
        (
            f"The {exp.name} experiment included {len(exp.arms)} arms: {', '.join((arm.name for arm in exp.arms))}. How many participants were initially allocated to the {arm.name} arm of the {exp.name} experiment?",
            texts,
            gs.quotes,
        )
        for exp in gs.parsed_answer.experiments
        for arm in exp.arms
    ]

async def gold_standard_examples(papers: Sequence[Paper]):
    pass


class DecontextAndSelect(Recipe):
    async def decontext_and_select(self, paper: Paper, question: str):
        """Answer the question by first enriching the paper by adding context autoregressively,
        then selecting sentences needed to answer the question.

        Args:
            paper (Paper): Paper to answer the question about
            question (str): The question

        Returns:
            answer: str
        """
        decontexted = await (PaperDecontext(mode=self.mode).run(paper))

        texts = await windowed_select(
            question=question,
            texts=list(decontexted.sentences()),
            n=5,
            step=2,
        )
        answer = await simple_answer(question, texts)
        return answer

    async def run(
        self, paper: Paper
    ) -> Sequence[tuple[int | Literal["Unclear"] | None, str, str] | None]:
        """Identify the initial sample size for each trial arm, for each experiment.

        Return the gold standard (if it exists), along with the answer from a baseline end-to-end approach and a decompositional approach.

        Args:
            paper (Paper): Paper

        Returns:
            tuple[int | Literal["Unclear"] | None, str, str]: gold standard, baseline approach answer, decomposed answer
        """
        gs = get_ea_gs(paper.document_id)
        assert gs and gs.parsed_answer

        answers: list[tuple[int | Literal["Unclear"] | None, str, str]] = []

        for exp in gs.parsed_answer.experiments:
            for arm in exp.arms:
                question = f"The {exp.name} experiment included {len(exp.arms)} arms: {', '.join((arm.name for arm in exp.arms))}. How many participants were initially allocated to the {arm.name} arm of the {exp.name} experiment?"

                baseline_answer = await (
                    baseline(question)(mode=self.mode).run(paper=paper)
                )

                answer = await self.decontext_and_select(paper=paper, question=question)

                gold_answer = arm.sample.size if arm and arm.sample else None
                answers.append((gold_answer, baseline_answer, answer))

        return answers
