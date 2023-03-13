from typing import Optional

from pydantic import BaseModel
from structlog.stdlib import get_logger

from ice.recipe import Recipe
from ice.utils import max_by_value

log = get_logger()


def make_compare_results_prompt(
    *, question: str, model_result: str, gold_result: str
) -> str:
    return f"""Compare the following results from a machine learning model to a gold standard. What (if any) information is in the gold standard but not in the model result? Does the model result capture all important information from the gold standard? Yes or No.

###

Question A: What was the placebo in this study?

Gold standard result A: Placebo gelatin capsules made of starch, talcum, kaolin, sucrose, and colouring. They were made by the same manufacturer as the active capsules and could not be distinguished from the active capsules by sight

Model result A: The placebo was made by the same manufacturer as the active capsules.

What (if any) information is in gold standard A but not in model result A?
- The specific composition of the placebo gelatin capsules (starch, talcum, kaolin, sucrose, and colouring)
- The fact that the placebo capsules could not be distinguished from the active capsules by sight

###

Question B: What was the image processing method?

Gold standard result B: The images were cleaned and aligned using common methods. The brain activity was measured using a statistical model that compared different types of stimuli (faces, houses, chairs, words, numbers, and a blank screen).

Model result B: The images were preprocessed using a standard pipeline that included skull stripping, motion correction, spatial normalization, and smoothing. The functional data were analyzed using a general linear model (GLM) with six task conditions (face, house, chair, word, number, and fixation) as regressors of interest and six motion parameters as nuisance regressors.

What (if any) information is in gold standard B but not in model result B? None

###

Question C: What was the test battery?

Gold standard result C: The participants completed a battery of neuropsychological tests that assessed memory, attention, executive function, language, and visuospatial skills. The scores were adjusted for age and education. They were expressed as standard deviations from the average.

Model result C: The participants took a series of tests that measured different aspects of their cognitive abilities, such as remembering words, repeating numbers, switching tasks, naming objects, and drawing a clock.

What (if any) information is in gold standard C but not in model result C?
- The analysis of test scores (adjusted for age and education, expressed as standard deviations from the average)

###

Question D: What was the study design?

Gold standard result D: The study used a randomized controlled trial design with four groups: a group that learned mindfulness techniques, a group that learned cognitive strategies, a group that learned both, and a group that received no treatment. The interventions lasted for eight weeks and consisted of meditation, yoga, cognitive exercises, and coping skills.

Model result D: The participants were randomly assigned to one of four groups: a mindfulness-based stress reduction (MBSR) group, a cognitive-behavioral therapy (CBT) group, a combination of MBSR and CBT (MBSR+CBT) group, or a wait-list control group. The MBSR group received eight weekly sessions of mindfulness meditation and yoga, the CBT group received eight weekly sessions of cognitive restructuring and coping skills training, and the MBSR+CBT group received both interventions.

What (if any) information is in gold standard D but not in model result D? None

###

Question E: {question.strip()}

Gold standard result E: {gold_result.strip()}

Model result E: {model_result.strip()}

What (if any) information is in gold standard E but not in model result E?"""


def make_classificaiton_prompt(
    *, question: str, missing_info: str, model_result: str, gold_result: str
) -> str:
    return f"""Compare the following results from a machine learning model to a gold standard. What (if any) information is in the gold standard but not in the model result? Does the model result capture all important information from the gold standard? Yes or No.

###

Question A: What was the placebo in this study?

Gold standard result A: Placebo gelatin capsules made of starch, talcum, kaolin, sucrose, and colouring. They were made by the same manufacturer as the active capsules and could not be distinguished from the active capsules by sight

Model result A: The placebo was made by the same manufacturer as the active capsules.

What (if any) information is in gold standard A but not in model result A?
- The specific composition of the placebo gelatin capsules (starch, talcum, kaolin, sucrose, and colouring)
- The fact that the placebo capsules could not be distinguished from the active capsules by sight

Does model result A capture all important information from gold standard A? No

###

Question B: What was the image processing method?

Gold standard result B: The images were cleaned and aligned using common methods. The brain activity was measured using a statistical model that compared different types of stimuli (faces, houses, chairs, words, numbers, and a blank screen).

Model result B: The images were preprocessed using a standard pipeline that included skull stripping, motion correction, spatial normalization, and smoothing. The functional data were analyzed using a general linear model (GLM) with six task conditions (face, house, chair, word, number, and fixation) as regressors of interest and six motion parameters as nuisance regressors.

What (if any) information is in gold standard B but not in model result B? None

Does model result B capture all important information from gold standard B? Yes

###

Question C: What was the test battery?

Gold standard result C: The participants completed a battery of neuropsychological tests that assessed memory, attention, executive function, language, and visuospatial skills. The scores were adjusted for age and education. They were expressed as standard deviations from the average.

Model result C: The participants took a series of tests that measured different aspects of their cognitive abilities, such as remembering words, repeating numbers, switching tasks, naming objects, and drawing a clock.

What (if any) information is in gold standard C but not in model result C?
- The analysis of test scores (adjusted for age and education, expressed as standard deviations from the average)

Does model result C capture all important information from gold standard C? No

###

Question D: What was the study design?

Gold standard result D: The study used a randomized controlled trial design with four groups: a group that learned mindfulness techniques, a group that learned cognitive strategies, a group that learned both, and a group that received no treatment. The interventions lasted for eight weeks and consisted of meditation, yoga, cognitive exercises, and coping skills.

Model result D: The participants were randomly assigned to one of four groups: a mindfulness-based stress reduction (MBSR) group, a cognitive-behavioral therapy (CBT) group, a combination of MBSR and CBT (MBSR+CBT) group, or a wait-list control group. The MBSR group received eight weekly sessions of mindfulness meditation and yoga, the CBT group received eight weekly sessions of cognitive restructuring and coping skills training, and the MBSR+CBT group received both interventions.

What (if any) information is in gold standard D but not in model result D? None

Does model result D capture all important information from gold standard D? Yes

###

Question E: {question}

Gold standard result E: {gold_result.strip()}

Model result E: {model_result.strip()}

What (if any) information is in gold standard E but not in model result E? {missing_info}

Does model result E capture all important information from gold standard E?"""


class ResultComparison(BaseModel):
    missing_info: Optional[str] = None
    is_complete: bool
    p_complete: float


class EvaluateResult(Recipe):
    async def run(
        self,
        model_result: Optional[str] = None,
        gold_result: Optional[str] = None,
        question: Optional[str] = None,
    ) -> ResultComparison:
        if self.mode == "test":
            model_results, gold_results, question = self.test_data()
            model_result = model_results[0]
            gold_result = gold_results[0]
        else:
            assert model_result is not None
            assert gold_result is not None
            assert question is not None

        missing_info_prompt = make_compare_results_prompt(
            question=question, model_result=model_result, gold_result=gold_result
        )
        missing_info = await self.agent().complete(
            prompt=missing_info_prompt,
            max_tokens=200,
        )
        classification_prompt = make_classificaiton_prompt(
            question=question,
            missing_info=missing_info,
            model_result=model_result,
            gold_result=gold_result,
        )
        choice_probs, _ = await self.agent("instruct").classify(
            prompt=classification_prompt, choices=(" Yes", " No")
        )

        choice, score = max_by_value(choice_probs)

        choice = choice.strip()

        if choice == "Yes":
            return ResultComparison(
                is_complete=True,
                p_complete=score,
                missing_info=missing_info,
            )
        elif choice == "No":
            return ResultComparison(
                is_complete=False,
                p_complete=1 - score,
                missing_info=missing_info,
            )
        else:
            raise ValueError(f"Unknown choice: {choice}")

    def test_data(self, n: int = 1) -> tuple[list[str], list[str], str]:
        if n > 3:
            raise ValueError("n must be <= 3")
        model_results = [
            "Placebo gelatin capsules made of starch, talcum, kaolin, sucrose, and colouring. They were made by the same manufacturer as the active capsules and could not be distinguished from the active capsules by sight",
            "The placebo consisted of chloroquine, proguanil, iron and folic acid tablets that had no active substances in them. They were identical in appearance and taste to the active tablets and were produced by the same company.",
            "The placebo was a fake treatment that looked like the real one but did not have any effect. It was made of chloroquine, proguanil, iron and folic acid tablets that had no active ingredients. The same company that made the real tablets also made the placebo tablets.",
        ]
        gold_results = [
            "The placebo is the treatment given to the control group that is designed to be indistinguishable from the real treatment but has no real effect. So in this case, the placebo for Group 5 would be chloroquine, proguanil, iron and folic acid pills that look identical to the real pills but contain no active ingredients. So the subjects would think they are taking the real treatment but are actually taking inactive pills.",
            "The placebo was chloroquine, proguanil, iron and folic acid tablets that had no active substances in them. It was identical in appearance and taste to the active tablets and were produced by the same company.",
            "Placebo gelatin capsules made of starch, talcum, kaolin, sucrose, and colouring. They were made by the same manufacturer as the active capsules and could not be distinguished from the active capsules by sight",
        ]
        question = "What was the placebo in the study?"
        return model_results[:n], gold_results[:n], question
