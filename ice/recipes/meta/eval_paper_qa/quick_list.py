import re
from collections.abc import Sequence

from ice.formatter.multi import format_multi
from ice.formatter.multi import stop
from ice.formatter.transform.value import numbered_list
from ice.recipe import recipe

PREAMBLE = "For each question, convert the part of the answer that answers the question into a numbered list."

EXAMPLES = [
    dict(
        question="What experiments were conducted in this paper?",
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
        question="Experiments are distinct from trial arms or groups; a single experiment might have multiple trial arms, like different interventions or controls. What experiment or experiments were conducted in this study? List them out, being mindful that there may just be one experiment or there could be more than one.",
        answer="""1. MIND#1, MIND#2, and MIND#3: three controlled experiments to study the effect of mindfulness on Software Engineering students’ conceptual modeling performance. 2. The experimental group practiced mindfulness while the control group was trained in public speaking as a placebo treatment. 3. The subjects were divided into two groups and all the subjects developed two conceptual models based on a transcript of an interview, one before and another one after the treatment. The results were compared in terms of conceptual modeling quality and productivity. 4. The statistically significant results of the series of experiments revealed that the subjects who practiced mindfulness developed slightly better conceptual models and they did it faster than the control group. 5. The practice of mindfulness improves the performance of Software Engineering students in conceptual modeling, especially their productivity. 6. However, more experimentation is needed in order to confirm the outcomes in other Software Engineering tasks and populations. 7. In the mindfulness workshops, the sessions were face– to–face, four days a week. All the sessions followed the same dynamics: the students and the researcher responsible for conducting the session met in a classroom; they all sat down, lights were turned off and curtains were drawn letting only some dim light in the room; when they all were in silence, an alarm was programmed; during the first five minutes, the subjects were guided in their body scan; then, during the remaining time, they were invited to focus solely on their breathing. Sometimes, the researcher asked “where is your mind now?” in order to re–focus them on breathing. In the event some students were late, they were instructed to enter the room making as less noise as possible and sit on one of the chairs that were intentionally left empty near the door. 8. In the public speaking workshops, the subjects were given some basic guidelines on how to prepare a talk, some notions on non–verbal communication and some seminal talks were commented. Later, they were invited to look for related videos on the Internet and to prepare a script for a public presentation on a topic of their interest. 9. The result of applying changes CH1 to CH3 in MIND#2 resulted in its differential settings consisting of a random assignment of subjects to groups""",
        separated=numbered_list(["MIND#1", "MIND#2", "MIND#3"]),
    ),
    dict(
        question="What were the trial arms of the ivermectin RCT?",
        answer="We conducted two experiments, one on the effectiveness of ivermectin and another on the effectiveness of Paxlovid. Each experiment had two trial arms: a control group and an intervention.",
        separated=numbered_list(["a control group", "an intervention group"]),
    ),
]

TEMPLATE = """
Question: {question}

Answer: {answer}

Convert the answer to a numbered list:

{separated}""".strip()


def make_quick_list_prompt(question: str, answer: str):
    examples = format_multi(
        TEMPLATE, EXAMPLES + [dict(question=question, answer=answer, separated=stop(""))]  # type: ignore[arg-type]
    )
    return "\n\n---\n\n".join([PREAMBLE] + list(examples))


def strip_enumeration_prefix(text: str) -> str:
    return re.sub(r"^\w*\s*\d+(\.|\))", "", text.strip()).strip()


async def quick_list(question: str, answer: str) -> Sequence[str]:
    prompt = make_quick_list_prompt(question, answer)
    completion = await recipe.agent().complete(prompt=prompt, stop="\n\n---")
    return [strip_enumeration_prefix(item) for item in completion.splitlines() if item]


recipe.main(quick_list)
