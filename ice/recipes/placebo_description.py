from typing import Optional

from ice.evaluation.evaluate_recipe_result import RecipeResult
from ice.metrics.gold_standards import get_gold_standard
from ice.metrics.gold_standards import list_experiments
from ice.paper import get_full_document_id
from ice.paper import Paper
from ice.recipe import Recipe
from ice.recipes.evaluate_result import EvaluateResult
from ice.trace import recorder
from ice.utils import truncate_by_tokens

QUESTION_SHORT_NAME = "placebo"

DEFAULT_ANSWER_CLASSIFICATION = "Placebo"


def get_paper_text(paper: Paper) -> str:
    return "\n\n".join(str(p) for p in paper.paragraphs)


def create_recipe_result(paper_id: str, experiment: str, answer: str) -> RecipeResult:
    return RecipeResult(
        document_id=paper_id,
        question_short_name=QUESTION_SHORT_NAME,
        experiment=experiment,
        classifications=[
            DEFAULT_ANSWER_CLASSIFICATION,
            DEFAULT_ANSWER_CLASSIFICATION,
        ],
        answer=answer,
        result=answer,
        excerpts=[],
    )


def get_gold_placebo(paper_id: str, experiment: str) -> Optional[str]:
    """
    Return the gold standard placebo description for the given paper and experiment.
    """
    gold_standard = get_gold_standard(
        document_id=paper_id, question_short_name="placebo", experiment=experiment
    )
    if gold_standard is None:
        return None
    return gold_standard.answer


class PlaceboDescription(Recipe):
    agent_str: str

    def make_prompt(self, paper: Paper, experiment: str) -> str:
        raise NotImplementedError()

    async def get_gold_experiments(self, paper: Paper) -> list[str]:
        paper_id = get_full_document_id(paper.document_id)
        experiments: list[str] = list_experiments(document_id=paper_id)
        return experiments

    async def placebo_for_experiment(
        self, paper: Paper, experiment: str, record=recorder
    ) -> str:
        # Generate the QA prompt
        qa_prompt = self.make_prompt(paper, experiment)

        # Ask the agent to answer the prompt
        placebo_description = await self.agent(self.agent_str).complete(
            prompt=qa_prompt, max_tokens=300
        )

        # Save to trace
        evaluation = await EvaluateResult(mode=self.mode).run(
            gold_result=get_gold_placebo(paper.document_id, experiment),
            model_result=placebo_description,
            question=f'What was the placebo for the "{experiment}" experiment?',
        )
        record(evaluation=evaluation)

        return placebo_description

    async def run(self, paper: Paper, record=recorder):
        # Get the list of experiments (for now from gold standards)
        experiments = await self.get_gold_experiments(paper)

        results = {}
        for experiment in experiments:
            gold_placebo = get_gold_placebo(paper.document_id, experiment)
            if not gold_placebo or gold_placebo in (
                "No placebo",
                "Not mentioned",
                "Unclear",
            ):
                continue

            placebo = await self.placebo_for_experiment(paper, experiment)

            # Save results for each experiment
            recipe_results = [
                create_recipe_result(paper.document_id, experiment, placebo)
            ]
            self.maybe_add_to_results(recipe_results)

            results[experiment] = placebo

        return results


class PlaceboDescriptionInstruct(PlaceboDescription):
    name = "PlaceboDescriptionInstruct"
    agent_str = "instruct"

    def make_prompt(self, paper: Paper, experiment: str) -> str:
        paper_text = truncate_by_tokens(str(paper), max_tokens=3500)
        return f"""Text of a research paper:

{paper_text}

Question: In this paper, what was the placebo in the "{experiment}" experiment?

Answer:"""
