from collections.abc import Sequence
from typing import Optional
from typing import Union

from ice.formatter.multi import format_multi
from ice.formatter.multi import stop
from ice.formatter.multi import StopSentinel
from ice.formatter.transform.value import numbered_list
from ice.formatter.transform.value import ValueTransform

QUESTION_FREE_EXAMPLES: list[dict[str, Union[str, StopSentinel]]] = [
    dict(
        context="Lisa loves to play practical jokes.",
        passage="But sometimes she goes too far.",
        rewrite="But sometimes she [Lisa] goes too far.",
    ),
    dict(
        context="The Super Bowl XLI halftime show took place on February 4, 2007.",
        passage="It was headlined by Prince.",
        rewrite="It [The Super Bowl XLI halftime show] was headlined by Prince.",
    ),
    dict(
        context="More than one fifth of the world’s population lives on less than Purchasing Power Parity (PPP) US$1.25 a day, and there is an emerging international consensus that this share should (and can) be driven close to zero by 2030 (1, 2).",
        passage="Reaching this objective will require enabling the poorest families, who are often the most marginalized within their villages, to shift from insecure and fragile sources of income to more sustainable income-generating activities.",
        rewrite="Reaching this objective [driving the share of the world’s population that lives on less than Purchaing Power Parity (PPP) US$1.25 a day from more than one fifth of the to zero by 2030] will require enabling the poorest families, who are often the most marginalized within their villages, to shift from insecure and fragile sources of income to more sustainable income-generating activities.",
    ),
    dict(
        context='We present results from randomized control trials (RCTs) in six countries of a particular approach to foster self-employment activities amongst the very poor. Originally designed and implemented by BRAC, a large Bangladeshi NGO that runs several country-wide programs, the “Graduation” program provides a holistic set of services, including the grant of a productive asset, to the poorest households in a village (referred to by BRAC as the “ultra-poor”). The beneficiaries [of the Graduation program, the poorest housholds in a village, or the "ultra-poor"] are identified through a participatory process in a village meeting, followed by a verification visit by the organization’s [the implmenter of the "Graduation" program] staff. Selected beneficiaries [among the poorest housholds in a village, or the "ultra-poor"] are then given a productive asset [by the implementer of the "Graduation Program"] that they choose from a list, training and support for the asset they have chosen, as well as general life skills coaching, weekly consumption support for some fixed period, and typically access to savings accounts and health information or services.',
        passage="These different activities (plus regular interactions with the households over the course of a year) are designed to complement each other in helping households to start a productive self-employment activity.",
        rewrite='These different activities [training and support for the assest they have chosen and received, general life skills coaching, weekly consumption support, and typically access to savings accounts and health information or services] (plus regular interactions with the households over the course of a year) are designed to complement each other in helping households [beneficiaries selected for the "Graduation" program from among the poorest housholds in a village, or the "ultra-poor"] to start a productive self-employment activity.',
    ),
]

QUESTION_GUIDED_EXAMPLES: list[
    dict[str, Union[str, ValueTransform[Sequence[str]], StopSentinel]]
] = [
    dict(
        questions=numbered_list(["What were Prince's biggest concerts?"]),
        context="The Super Bowl XLI halftime show took place on February 4, 2007.",
        passage="It was headlined by Prince.",
        rewrite="It [The Super Bowl XLI halftime show] was headlined by Prince.",
    ),
    dict(
        questions=numbered_list(["What were the aims of the study?"]),
        context="More than one fifth of the world’s population lives on less than Purchasing Power Parity (PPP) US$1.25 a day, and there is an emerging international consensus that this share should (and can) be driven close to zero by 2030 (1, 2).",
        passage="Reaching this objective will require enabling the poorest families, who are often the most marginalized within their villages, to shift from insecure and fragile sources of income to more sustainable income-generating activities.",
        rewrite="Reaching this objective [driving the share of the world’s population that lives on less than Purchaing Power Parity (PPP) US$1.25 a day from more than one fifth of the to zero by 2030] will require enabling the poorest families, who are often the most marginalized within their villages, to shift from insecure and fragile sources of income to more sustainable income-generating activities.",
    ),
    dict(
        questions=numbered_list(
            ["Who funded the study?", "What were the limitations of the RCT findings?"]
        ),
        context='We present results from randomized control trials (RCTs) in six countries of a particular approach to foster self-employment activities amongst the very poor. Originally designed and implemented by BRAC, a large Bangladeshi NGO that runs several country-wide programs, the “Graduation” program provides a holistic set of services, including the grant of a productive asset, to the poorest households in a village (referred to by BRAC as the “ultra-poor”). The beneficiaries [of the Graduation program, the poorest housholds in a village, or the "ultra-poor"] are identified through a participatory process in a village meeting, followed by a verification visit by the organization’s [the implmenter of the "Graduation" program] staff. Selected beneficiaries [among the poorest housholds in a village, or the "ultra-poor"] are then given a productive asset [by the implementer of the "Graduation Program"] that they choose from a list, training and support for the asset they have chosen, as well as general life skills coaching, weekly consumption support for some fixed period, and typically access to savings accounts and health information or services.',
        passage="These different activities (plus regular interactions with the households over the course of a year) are designed to complement each other in helping households to start a productive self-employment activity.",
        rewrite="These different activities (plus regular interactions with the households over the course of a year) are designed to complement each other in helping households to start a productive self-employment activity.",
    ),
]
QUESTION_FREE_PREFIX = "Instructions: Enrich each Passage with the Context."
QUESTION_GUIDED_PREFIX = "Instructions: Enrich each Passage with the Context, carrying forward all and only information that can help answer the questions."

QUESTION_FREE_EXAMPLE_TEMPLATE = """Context: {context}
Passage: {passage}
Rewrite: {rewrite}
""".strip()

QUESTION_GUIDED_EXAMPLE_TEMPLATE = """

Questions:

{questions}

Context: {context}
Passage: {passage}
Rewrite: {rewrite}""".strip()


def decontext_prompt(
    context: str, passage: str, questions: Optional[Sequence[str]] = None
) -> str:
    last_example: dict[str, Union[str, StopSentinel, ValueTransform]] = dict(
        context=context, passage=passage, rewrite=stop("")
    )
    if questions:
        last_example["questions"] = numbered_list(questions)
    examples = format_multi(
        QUESTION_GUIDED_EXAMPLE_TEMPLATE
        if questions
        else QUESTION_FREE_EXAMPLE_TEMPLATE,
        QUESTION_GUIDED_EXAMPLES + [last_example]
        if questions
        else QUESTION_FREE_EXAMPLES + [last_example],
    )
    return "\n\n".join(
        (
            QUESTION_GUIDED_PREFIX if questions else QUESTION_FREE_PREFIX,
            "\n\n---\n\n".join(examples),
        )
    )
