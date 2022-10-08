from ice.evaluation.evaluate_recipe_result import RecipeResult
from ice.metrics.gold_standards import list_experiments
from ice.paper import get_full_document_id
from ice.paper import Paper
from ice.recipe import Recipe
from ice.utils import window_by_tokens

QUESTION_SHORT_NAME = "adherence"


def get_paper_text(paper: Paper) -> str:
    return "\n\n".join(str(p) for p in paper.paragraphs)


def generate_qa_prompt_instruct(paper_text: str) -> str:
    return f"""
Summarize the adherence rate of this research paper based on the following excerpt. If the adherence rate is not mentioned in this excerpt, say "not mentioned".

BEGIN PAPER EXCERPT

{paper_text}

END PAPER EXCERPT

One possible summary of the adherence rate based on the above excerpt is:""".strip()


def create_recipe_result(paper_id: str, experiment: str, answer: str) -> RecipeResult:
    return RecipeResult(
        document_id=paper_id,
        question_short_name=QUESTION_SHORT_NAME,
        experiment=experiment,
        classifications=[
            None,
            None,
        ],
        answer=answer,
        result=answer,
        excerpts=[],
    )


class FunnelSimple(Recipe):
    agent_str = "instruct"

    async def run(self, paper: Paper):
        full_paper_text = get_paper_text(paper)

        descriptions = []
        # Ask the agent to answer the prompt
        for chunk in window_by_tokens(full_paper_text, max_tokens=5000):
            description = await self.agent(self.agent_str).complete(
                prompt=generate_qa_prompt_instruct(chunk),
                max_tokens=500,
            )
            descriptions.append(description)

        # Save results for each experiment
        paper_id = get_full_document_id(paper.document_id)
        experiments: list[str] = list_experiments(document_id=paper_id)
        recipe_results = [
            create_recipe_result(paper_id, experiment, "\n---\n".join(descriptions))
            for experiment in experiments
        ]
        self.maybe_add_to_results(recipe_results)

        return "\n\n---\n\n".join(descriptions)
