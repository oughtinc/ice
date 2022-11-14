from collections.abc import Sequence

from ice.formatter.multi import format_multi
from ice.formatter.multi import stop
from ice.formatter.transform.value import numbered_list

INSTRUCTIONS = """For each pair of lists, can each item in list A be paired with a corresponding item in list B that is substantially similar to it? If so, explain why. If not, explain why not."""

EXAMPLE_TEMPLATE = """
List A:

{ground_truth_items}

List B:

{predicted_items}

Let's think it over. {reasoning}

Final answer: {final_answer}
""".strip()

YES_ANSWER = (
    "Yes, each item in list A can be paired with a corresponding item in list B."
)
NO_ANSWER = "No, it is not the case that each item in list A can be paired with a corresponding item in list B."

EXAMPLES = [
    dict(
        ground_truth_items=numbered_list(
            [
                "SALT-1: multicenter, randomized, double-blind, placebo-controlled trial of tolvaptan for hyponatremia",
                "SALT-2: multicenter, randomized, double-blind, placebo-controlled trial of tolvaptan for hyponatremia",
            ]
        ),
        predicted_items=numbered_list(
            [
                "a study of tolvaptan",
                "a study of the effect of discontinuation of the study drug",
            ]
        ),
        reasoning="""The items in List A only differ by SALT-1 versus SALT-2, but the items in List B do not share this difference. Therefore, we cannot match the items in List A up with the items in List B.""",
        final_answer=NO_ANSWER,
    ),
    dict(
        ground_truth_items=numbered_list(
            [
                "preintervention cases: a stepped wedge cluster RCT to examine the effect of the SSC on in-hospital complications",
                "postintervention cases: a stepped wedge cluster RCT to examine the effect of the SSC on in-hospital complications",
            ]
        ),
        predicted_items=numbered_list(
            [
                "study of the SSC before surgery",
                "study of the SSC after surgery",
            ]
        ),
        reasoning="""The items in List A differ by mentioning preintervention and postintervention, and they are both about studies of the effect of the SSC. \
The items in List B differ in being before (pre) or after (post) surgery, and are both about studies of the SSC. Therefore, we can match the \
"preintervention cases" item in List A to the "before surgery" item in List B, and the "postintervention cases" item in List A to the \
"after surgery" item in List B.""",
        final_answer=YES_ANSWER,
    ),
]


def matching_prompt(items_a: Sequence[str], items_b: Sequence[str]) -> str:
    examples = EXAMPLES + [
        dict(ground_truth_items=items_a, predicted_items=items_b, reasoning=stop(""))
    ]
    formatted_examples = format_multi(EXAMPLE_TEMPLATE, examples)  # type: ignore[arg-type]
    return "\n\n".join([INSTRUCTIONS, "\n\n---\n\n".join(formatted_examples)])


MATCHING_STOP_SEQUENCES = [
    ", the items in list A can be matched with the items in list B.",
    "the items in list A cannot be matched with the items in list B.",
]


def reasoning_and_answer_from_completion(completion: str) -> tuple[str, bool]:
    reasoning_part, answer_part = completion.split("Final answer: ")
    yes_answer = "Yes" in answer_part
    return reasoning_part.strip(), yes_answer
