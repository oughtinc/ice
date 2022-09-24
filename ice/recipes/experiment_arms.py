from structlog.stdlib import get_logger

from ice.paper import Paper
from ice.recipe import Recipe
from ice.recipes.comparisons_qa import ComparisonsQA
from ice.utils import map_async

Experiment = str

log = get_logger()


class ExperimentArms(Recipe):
    async def get_arms(self, paper: Paper) -> list[Experiment]:
        qa_recipe = ComparisonsQA(mode=self.mode)
        arms_result = await qa_recipe.run(
            paper=paper,
            question_short="""What were the trial arms (subgroups of participants) of the experiment?""",
            question_long="""What were the trial arms (subgroups of participants) of the experiment? List one per line.""",
            answer_prefix="Answer: The trial arms were:\n-",
        )
        arms = [line.strip("- ") for line in arms_result.split("\n")]
        return arms

    async def describe_arm(
        self, paper: Paper, arms: list[Experiment], arm_to_describe: Experiment
    ) -> str:
        qa_recipe = ComparisonsQA(mode=self.mode)
        if len(arms) == 1:
            qa_result = await qa_recipe.run(
                paper=paper,
                question_short=f"""What was the setup of the "{arm_to_describe}" trial arm?""",
                question_long=f"""What was the setup of the "{arm_to_describe}" trial arm? Describe the intervention in a few sentences.""",
                answer_prefix="Answer:",
                num_paragraphs=2,
            )
        else:
            arm_strings = ", ".join(arms)
            qa_result = await qa_recipe.run(
                paper=paper,
                question_short=f"""What was the setup of the "{arm_to_describe}" trial arm?""",
                question_long=f"""In the study there were {len(arms)} trial arms, {arm_strings}. What was the setup of the "{arm_to_describe}" trial arm? Describe the intervention in a few sentences.""",
                answer_prefix="Answer:",
                num_paragraphs=2,
            )
        return qa_result

    async def get_arm_descriptions(
        self, paper: Paper, arms: list[Experiment]
    ) -> list[str]:
        arm_descriptions = await map_async(
            arms,
            lambda arm_to_describe: self.describe_arm(paper, arms, arm_to_describe),
            max_concurrency=self.max_concurrency(),
        )
        return arm_descriptions

    async def run(self, paper: Paper):
        arms = await self.get_arms(paper)

        arm_descriptions = await self.get_arm_descriptions(paper, arms)

        return arms, arm_descriptions
