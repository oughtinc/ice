from typing import Optional

from ice.evaluation.evaluate_recipe_result import RecipeResult
from ice.metrics.gold_standards import list_experiments
from ice.paper import get_full_document_id
from ice.paper import Paper
from ice.recipe import Recipe
from ice.utils import truncate_by_tokens


def get_paper_text(paper: Paper) -> str:
    return "\n\n".join(str(p) for p in paper.paragraphs)


def create_recipe_result(
    paper_id: str,
    experiment: str,
    answer: str,
    question_short_name: str,
    default_answer_classification: Optional[str],
) -> RecipeResult:
    return RecipeResult(
        document_id=paper_id,
        question_short_name=question_short_name,
        experiment=experiment,
        classifications=[
            default_answer_classification,
            default_answer_classification,
        ],
        answer=answer,
        result=answer,
        excerpts=[],
    )


class SinglePrompt(Recipe):
    agent_str: str
    max_tokens: int
    qa_prompt_template: str
    question_short_name: str
    default_answer_classification: Optional[str]

    async def run(self, paper: Paper):
        # Get the full paper text and truncate it
        full_paper_text = get_paper_text(paper)
        paper_text = truncate_by_tokens(full_paper_text, max_tokens=self.max_tokens)

        # Generate the QA prompt
        qa_prompt = self.qa_prompt_template.format(paper_text=paper_text)

        # Ask the agent to answer the prompt
        answer = await self.agent(self.agent_str).complete(
            prompt=qa_prompt, max_tokens=300
        )

        # Save results for each experiment
        paper_id = get_full_document_id(paper.document_id)
        experiments: list[str] = list_experiments(document_id=paper_id)
        recipe_results = [
            create_recipe_result(
                paper_id,
                experiment,
                answer,
                self.question_short_name,
                self.default_answer_classification,
            )
            for experiment in experiments
        ]
        self.maybe_add_to_results(recipe_results)

        return answer
