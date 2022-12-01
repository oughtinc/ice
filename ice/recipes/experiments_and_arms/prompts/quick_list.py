from ice.formatter.multi import format_multi
from ice.formatter.multi import stop
from ice.formatter.transform.value import numbered_list

PREAMBLE = "Convert the following model outputs into numbered lists:"

EXAMPLES = [
    dict(
        answer="The six experiments conducted in this paper were 1) an asset index experiment, 2) a consumption support experiment in Ethiopia and Peru, 3) a consumption support experiment in general, 4) an output production experiment, 5) an asset transfer experiment, and 6) a non-farm micro-enterprise experiment.",
        separated=numbered_list(
            [
                "An asset index experiment",
                "A consumption support experiment in Ethiopia and Peru",
                "A consumption support experiment in general",
                "An output production experiment",
                "An asset transfer experiment",
                "A non-farm micro-enterprise experiment",
            ]
        ),
    ),
    dict(
        answer="The one experiment conducted in this paper was a study of different quality control procedures for data collection. This study looked at how different quality control procedures may affect study outcomes, and the impact of quality control procedures on study outcomes.",
        separated=numbered_list(
            ["A study of different quality control procedures for data collection"]
        ),
    ),
    dict(
        answer=numbered_list(["a control group", "an intervention group"]),
        separated=numbered_list(["a control group", "an intervention group"]),
    ),
]

TEMPLATE = """Answer: {answer}

Convert to a numbered list:

{separated}"""


def make_quick_list_prompt(answer: str):
    examples = format_multi(
        TEMPLATE, EXAMPLES + [dict(answer=answer, separated=stop(""))]  # type: ignore[arg-type]
    )
    return "\n\n".join([PREAMBLE] + list(examples))
