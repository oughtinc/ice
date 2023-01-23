from typing import Any
from typing import Literal
from typing import Optional

from pydantic import BaseModel
from rich.pretty import pprint
from structlog.stdlib import get_logger

from ice.evaluation.evaluate_recipe_result import RecipeResult
from ice.metrics.gold_standards import list_experiments
from ice.paper import get_full_document_id
from ice.paper import Paper
from ice.paper import Paragraph
from ice.recipe import Recipe
from ice.recipes.comparisons_qa import ComparisonsQA
from ice.recipes.experiment_arms import ExperimentArms
from ice.utils import map_async
from ice.utils import max_by_value

Experiment = str

log = get_logger()

DEFINITIONS_STRING = """
- Placebo-controlled study: A way of testing a treatment in which a separate control group receives a sham "placebo" treatment which is specifically designed to be indistinguishable from the real treatment but has no real effect.
- Open-label trial, or open trial: A type of clinical trial in which information is not withheld from trial participants. In particular, both the researchers and participants know which treatment is being administered.
- Double-blind study: A type of clinical trial in which neither the participants nor the researcher knows which treatment or intervention participants are receiving until the clinical trial is over.
""".strip()


class Component(BaseModel):
    name: str
    metadata: dict[str, Any] = {}


class ClassificationComponent(Component):
    value: tuple[str, float]
    type: Literal["classification"] = "classification"


def get_section_title(paragraph: Paragraph) -> str:
    if not paragraph.sections:
        return "Unknown section"
    return paragraph.sections[0].title


def parse_quotes(s: str) -> list[str]:
    if s.strip() == "n/a":
        return []
    return [clean_quote for line in s.split("\n") if (clean_quote := line.strip('" '))]


def format_paragraphs(paragraphs: list[Paragraph]) -> str:
    return "\n".join(f'"{paragraph}"' for paragraph in paragraphs)


def format_list(xs: list[str]) -> str:
    return "\n".join(f"- {x}" for x in xs)


def make_paragraph_placebo_classification_prompt(paragraph: Paragraph) -> str:
    return f"""Each of the paragraphs below is from a different paper. For each paragraph, classify whether a placebo was used in the paper.

Relevant definitions:
{DEFINITIONS_STRING}

###

Below is a paragraph from the "Methods" section of scientific paper A.

Paragraph from paper A: "Between the 26th and 29th of April 1998, all households in the intervention villages received a number of ITNs (insecticide-treated bed nets), according to the number of family members and were instructed explicitly about the correct use of the nets (Figure 2). More than 5000 ITN were distributed. The ITN (green colour, polyester, size 130 × 180 × 150 cm (11.6 m2 ) or 190 × 180 × 150 cm (14.5 m2 ), Siam-Dutch Co, Thailand) were already impregnated with deltamethrin (25 mg/m2 ) by the manufacturer. All households of the control villages received ITNs after the study was completed in May 1999."

Question: Based on the paragraph from paper A, did the paper use a placebo? Give your reasoning step by step, then answer with "Answer: Yes", "Answer: No", or "Answer: Unclear".

Reasoning: The paragraph from paper A doesn't explicitly talk about placebos. It's unclear whether bed nets that were not treated with insecticice were used as a placebo.

Answer: Unclear

###

Below is a paragraph from the "Randomization" section of scientific paper B.

Paragraph from paper B: To facilitate community-based treatment of malaria with the assigned regimen (artemether-lumefantrine or dihydroartemisinin-piperaquine), and to ensure that children received the correct regimen if they attended at health centres in the study area, ID cards were colour-coded according to intervention group and labelled with the regimen to be used for case management. The study was therefore open-label with respect to the regimen used for case management but blinded with respect to whether seasonal malaria chemoprevention was active or placebo (members of the research team from KNUST/CGHR and LSHTM were aware of the allocation, but those who administered the SMC, and mothers/children were blinded).

Question: Based on the paragraph from paper B, did the paper use a placebo? Give your reasoning step by step, then answer with "Answer: Yes", "Answer: No", or "Answer: Unclear".

Reasoning: The paragraph from paper B mentions that there was a placebo as alternative to seasonal malaria chemoprevention.

Answer: Yes

###

Below is a paragraph from the "Introduction" section of scientific paper C.

Paragraph from paper C: After a census of the village population, subjects in the target age group were screened for inclusion and exclusion criteria. Subjects who met inclusion and exclusion criteria were randomized either to receive two intermittent preventive treatments with standard recommended treatment doses of SP or no intermittent preventive treatment. Randomization codes were computer generated using simple randomization technique and treatment allocations were provided within sealed opaque envelopes.

Question: Based on the paragraph from paper C, did the paper use a placebo? Give your reasoning step by step, then answer with "Answer: Yes", "Answer: No", or "Answer: Unclear".

Reasoning: The paragraph from paper C says that the possible treatments were "two intermittent preventive treatments with standard recommended treatment doses of SP" and "no intermittent preventive treatment". The first group is the active treatment group. The second group seems to have no treatment, not a placebo treatment, so probably no placebo was used.

Answer: No

###

Below is a paragraph from the "Introduction" section of scientific paper D.

Paragraph from paper D: In India, the Integrated Child Development Service (ICDS) maintains a network of child-care centres, caring for children up to age 6 years and off ering the potential to deliver simple health interventions.

Question: Based on the paragraph from paper D, did the paper use a placebo? Give your reasoning step by step, then answer with "Answer: Yes", "Answer: No", or "Answer: Unclear".

Reasoning: The paragraph from paper D doesn't mention anything about placebos.

Answer: Unclear

###

Below is a paragraph from the "{get_section_title(paragraph)}" section of scientific paper E.

Paragraph from paper E: {paragraph}

Question: Based on the paragraph from paper E, did the paper use a placebo? Give your reasoning step by step, then answer with "Answer: Yes", "Answer: No", or "Answer: Unclear".

Answer:"""


def make_placebo_classification_from_arms_prompt(
    paper: Paper, arms: list[str], descriptions: list[str]
) -> str:
    arms_str = ""
    for i, (arm, description) in enumerate(zip(arms, descriptions)):
        arms_str += f"Arm {i+1} of paper D: {arm}\n"
        arms_str += f"Description of arm {i+1} of paper D: {description}\n\n"
    prompt = f"""For each paper, classify whether the paper used a placebo or not.

Take into account that a Placebo-controlled study is a way of testing a treatment in which a separate control group receives a sham "placebo" treatment which is specifically designed to be indistinguishable from the real treatment but has no real effect.

An open-label trial, or open trial is a type of clinical trial in which information is not withheld from trial participants. In particular, both the researchers and participants know which treatment is being administered.

Err on the side of caution: If you are unsure, answer "Unclear".

###

Paper A

First paragraph of paper A: In this study we investigate the effects of a single dose of oral zinc, and of oral calcium carbonate, on the risk of developing a type of complex polyomaviruses (CPV) that is associated with a high risk of death.

Arm 1 of paper A: Oral zinc supplement

Arm 2 of paper A: Oral calcium carbonate

Arm 3 of paper A: Placebo for oral zinc supplement

Question: Did paper A use a placebo? Give your reasoning, then answer with "Yes", "No", or "Unclear".

Reasoning: Arm 3 of paper A explicitly states that it is a placebo, so the answer is "Yes".

Answer: Yes

###

Paper B

First paragraph of paper B: It is suggested that a low intake of fish and/or n-3 PUFA is associated with depressed mood. However, results from epidemiologic studies are mixed, and randomized trials have mainly been performed in depressed patients, yielding conflicting results.

Arm 1 of paper B: 1800 mg/d EPA+DHA
Description of arm 1 of paper B: The participants received a capsule.

Arm 2 of paper B: No treatment
Description of arm 2 of paper B: The participants did not receive anything.

Question: Did paper B use a placebo? Give your reasoning, then answer with "Yes", "No", or "Unclear".

Reasoning: The description of arm 2 of paper B says that the participants did not receive anything, which implies that they also did not receive a placebo, so the answer is that paper B did not use a placebo.

Answer: No

###

Paper C

First paragraph of paper C: OBJECTIVE To assess the impact of zinc supplementation on nutritional and biochemical parameters among children aged 12 to 59 months. METHODS
A blinded randomized clinical trial was carried out with 58 children aged 12 to 59 months included in the Programa Governamental de Combate a Carências Nutricionais (National Child Nutritional Program), which provided them with 2 kg of iron-fortified milk. The supplementation group (n = 28) received 10 mg/day of zinc sulfate for four months, and the control group (n = 30) received placebo.

Arm 1 of paper C: Control group
Description of arm 1 of paper C: n = 30 participants

Arm 2 of paper C: Supplementation group (n = 28)
Description of arm 2 of paper C: Receiving 10 mg/day of zinc sulfate

Question: Did paper C use a placebo? Give your reasoning, then answer with "Yes", "No", or "Unclear".

Reasoning: Arm 1 of paper C does not include any information besides the number of participants and the fact that it is a control group, so we don't know if it is a placebo arm or not.

Answer: Unclear

###

Paper D

First paragraph of paper D: {paper.nonempty_paragraphs()[0]}

{arms_str}Question: Did paper D use a placebo? Give your reasoning, then answer with "Yes", "No", or "Unclear".

Answer:"""
    return prompt


def make_placebo_arm_index_prompt(
    paper: Paper, arms: list[str], descriptions: list[str]
) -> tuple[str, list[str]]:
    arms_str = ""
    for i, (arm, description) in enumerate(zip(arms, descriptions)):
        arms_str += f"Arm {i+1} of paper D: {arm}\n"
        arms_str += f"Description of arm {i+1} of paper D: {description}\n\n"

    choices = [str(i + 1) for i in range(len(arms))] + ["Unclear"]
    choices_str = ", ".join([f'"{i}"' for i in choices])

    prompt = f"""For each paper, find out which experimental arm of the paper was a placebo.

###

Paper A

First paragraph of paper A: In this study we investigate the effects of a single dose of oral zinc, and of oral calcium carbonate, on the risk of developing a type of complex polyomaviruses (CPV) that is associated with a high risk of death.

Arm 1 of paper A: Oral zinc supplement

Arm 2 of paper A: Oral calcium carbonate with zinc placebo

Arm 3 of paper A: Placebo for oral zinc supplement

Question: Did paper A use a placebo? Give your reasoning, then answer with "Yes", "No", or "Unclear".

Answer: Yes

Question: Which arm(s) of paper A used a placebo? Answer with one or more of "1", "2", "3", "Unclear".

Answer: 2, 3

###

Paper D

First paragraph of paper D: {paper.nonempty_paragraphs()[0]}

{arms_str}Question: Did paper D use a placebo? Give your reasoning, then answer with "Yes", "No", or "Unclear".

Answer: Yes

Question: Which arm(s) of paper D used a placebo? Answer with one or more of {choices_str}.

Answer:"""
    return prompt, choices


class PlaceboTree(Recipe):
    do_not_test = True

    async def run(self, *, paper: Paper):
        arms_recipe = ExperimentArms(mode=self.mode)
        arms, arm_descriptions = await arms_recipe.run(paper=paper)  # type: ignore[call-arg]

        placebo_class, placebo_description_draft = await self.classify_placebo(
            paper, arms, arm_descriptions
        )

        if placebo_class == "Placebo":
            placebo_description = await self.describe_placebo(
                paper, placebo_description_draft
            )
        else:
            placebo_description = placebo_class

        # Save results
        experiments: list[str] = list_experiments(
            document_id=get_full_document_id(paper.document_id)
        )
        for experiment in experiments:
            coarse_placebo_class = (
                "Placebo"
                if placebo_class == "Placebo"
                else "No placebo or placebo not mentioned"
            )
            recipe_result = RecipeResult(
                document_id=paper.document_id,
                question_short_name="placebo",
                experiment=experiment,
                classifications=[
                    placebo_class,
                    coarse_placebo_class,
                ],
                answer=placebo_description,
                result=placebo_description,
                excerpts=[],
            )
            self.maybe_add_to_results([recipe_result])

        return placebo_class, placebo_description

    async def classify_placebo(
        self, paper: Paper, arms: list[str], arm_descriptions: list[str]
    ) -> tuple[str, Optional[str]]:
        """
        Classify whether the paper used a placebo by combining the results from
        classifying the arms and the paragraphs.
        """
        arm_cls, placebo_arm_indices = await self.classify_placebo_from_arms(
            paper, arms, arm_descriptions
        )

        if arm_cls == "Placebo":
            placebo_description_draft = "\n".join(
                f"{arms[i]}: {arm_descriptions[i]}" for i in placebo_arm_indices
            )
            return arm_cls, placebo_description_draft

        par_cls, par_prob = await self.classify_placebo_from_paragraphs(paper)
        combined_cls = self.combine_placebo_classifications(par_cls, par_prob, arm_cls)
        return combined_cls, None

    async def classify_placebo_from_arms(
        self, paper: Paper, arms: list[str], descriptions: list[str]
    ) -> tuple[str, list[int]]:
        """
        Classify whether the paper used a placebo by asking two questions:
        - Does the paper say that a placebo was used in the experiment?
        - If yes, which arm(s) received the placebo and were they indistinguishable from the other groups?
        """
        prompt = make_placebo_classification_from_arms_prompt(paper, arms, descriptions)
        classification = await self._classify(
            name="placebo_classification_from_arms",
            prompt=prompt,
            choices=[" Yes", " No", " Unclear"],
        )
        response_str = classification.value[0]
        if response_str.strip() == "No":
            return "No placebo", []
        elif response_str.strip() == "Unclear":
            return "Unclear", []

        assert response_str.strip() == "Yes", response_str

        arm_index_prompt, choices = make_placebo_arm_index_prompt(
            paper, arms, descriptions
        )

        arm = await self._classify(
            name="placebo_classification_from_arms_index",
            prompt=arm_index_prompt,
            choices=[f" {choice}" for choice in choices],
        )

        try:
            arm_indices = [int(x) - 1 for x in arm.value[0].strip().split(",")]
        except ValueError:
            return "Unclear", []

        distinguishability_prompt = f"""{arm_index_prompt} {arm.value[0]}

Followup-question: Are the placebo arms indistinguishable from the other groups for the participants? Give your reasoning, then answer with "Indistinguishable" or "Not indistinguishable".

Answer:"""

        distinguishability = await self._classify(
            name="placebo_classification_from_arms_distinguishable",
            prompt=distinguishability_prompt,
            choices=[" Indistinguishable", " Not indistinguishable"],
        )
        distinguishability_str = distinguishability.value[0]
        if distinguishability_str.strip() == "Indistinguishable":
            return "Placebo", arm_indices
        else:
            return "Unclear", []

    async def classify_placebo_from_paragraphs(
        self,
        paper: Paper,
    ) -> tuple[str, float]:
        """
        Classify whether the paper used a placebo by classifying each paragraph
        and aggregating the results.
        """
        paragraph_classifications = await self.classify_all_paragraphs(paper)
        return self.aggregate_paragraph_placebo_classifications(
            paragraph_classifications=paragraph_classifications,
        )

    async def classify_all_paragraphs(
        self, paper: Paper
    ) -> list[ClassificationComponent]:
        """
        Classify each non-empty paragraph of the paper as either "Yes", "No", or "Unclear"
        for whether it says that a placebo was used in the experiment.
        """
        paragraph_classifications = await map_async(
            paper.nonempty_paragraphs(),
            lambda paragraph: self.classify_paragraph_placebo(paragraph),
            max_concurrency=self.max_concurrency(),
            show_progress_bar=True,
        )
        return paragraph_classifications

    async def classify_paragraph_placebo(
        self, paragraph: Paragraph
    ) -> ClassificationComponent:
        """
        Classify a single paragraph as either "Yes", "No", or "Unclear"
        for whether it says that a placebo was used in the experiment.
        """
        prompt = make_paragraph_placebo_classification_prompt(paragraph)
        component = await self._classify(
            name="placebo_classification",
            prompt=prompt,
            choices=["Yes", "No", "Unclear"],
        )
        cls, prob = component.value
        if cls != "Yes":
            return component
        if "placebo" in str(paragraph).lower():
            return ClassificationComponent(
                name="placebo_classification",
                value=("Yes", 1.0),
                metadata={
                    "explanations": (component.metadata["explanations"] or "")
                    + "\nExplicitly mentions placebo"
                },
            )
        return ClassificationComponent(
            name="placebo_classification",
            value=("Yes", 0.5),
            metadata={
                "explanations": (component.metadata["explanations"] or "")
                + "\nImplicitly mentions placebo"
            },
        )

    def aggregate_paragraph_placebo_classifications(
        self,
        paragraph_classifications: list[ClassificationComponent],
    ) -> tuple[str, float]:
        """
        Aggregate the paragraph-wise placebo classification results
        into an overall classification of whether the paper used a
        placebo.
        """

        def class_prob(clf: ClassificationComponent) -> float:
            cls, prob = clf.value
            return prob

        def is_unclear(clf: ClassificationComponent) -> bool:
            cls, prob = clf.value
            return cls == "Unclear"

        pros = []
        cons = []
        for placebo_classification in paragraph_classifications:
            cls, _ = placebo_classification.value
            if cls == "Yes":
                pros.append(placebo_classification)
            elif cls == "No":
                cons.append(placebo_classification)
        if pros and not cons:
            answer = "Placebo"
            prob = max(class_prob(clf) for clf in pros)
        elif cons and not pros:
            answer = "No placebo"
            prob = 0.5
        elif not pros and not cons:
            answer = "Not mentioned"
            prob = 0.5
        else:  # pros and cons
            pprint([clf for clf in paragraph_classifications if not is_unclear(clf)])
            answer = "Unclear"
            prob = 0.5
        return answer, prob

    def combine_placebo_classifications(
        self, par_cls: str, par_prob: float, arm_cls: str
    ) -> str:
        # TODO: Be more systematic about probability aggregation
        if par_prob == 1.0:
            return par_cls
        if (par_cls, arm_cls) in [
            ("Placebo", "Unclear"),
            ("Unclear", "Placebo"),
            ("Not mentioned", "Placebo"),
        ]:
            return "Placebo"
        elif (par_cls, arm_cls) in [
            ("Placebo", "No placebo"),
            ("No placebo", "Placebo"),
            ("Unclear", "No placebo"),
        ]:
            return "Unclear"
        elif (par_cls, arm_cls) in [
            ("Not mentioned", "Unclear"),
        ]:
            return "Not mentioned"
        elif (par_cls, arm_cls) in [
            ("No placebo", "Unclear"),
            ("Not mentioned", "No placebo"),
        ]:
            return "No placebo"
        else:
            assert par_cls == arm_cls
            return par_cls

    async def describe_placebo(
        self, paper: Paper, description_draft: Optional[str]
    ) -> str:
        """
        Describe the placebo or placebos used in the study, either by using the draft
        from the arm classification or by asking a QA question.
        """

        if description_draft is not None:
            return description_draft

        qa_recipe = ComparisonsQA(mode=self.mode)
        qa_result = await qa_recipe.run(
            paper=paper,
            question_short="""What was the placebo?""",
            question_long="""What was the placebo, or what were the placebos used in the study? Describe in a few sentences.""",
            answer_prefix="Answer:",
            num_paragraphs=3,
        )
        return qa_result

    async def _classify(
        self,
        *,
        name: str,
        prompt: str,
        choices: list[str],
        unknown_choice: str = "Unclear",
        unknown_threshold: float = 0.8,
        verbose: bool = False,
        agent_name: str = "instruct-reasoning-crowd",
    ) -> ClassificationComponent:
        answer_probs, explanations = await self.agent(
            agent_name="instruct-reasoning-crowd"
        ).classify(
            prompt=prompt,
            choices=tuple(choices),
            verbose=verbose,
        )
        answer, probability = max_by_value(answer_probs)
        if probability < unknown_threshold:
            answer = unknown_choice
            probability = 0.9
        return ClassificationComponent(
            name=name,
            value=(answer, probability),
            metadata={"explanations": explanations},
        )
