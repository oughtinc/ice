import math
from ice.formatter.multi import format_multi, stop
from ice.apis.openai import openai_complete

EXAMPLES = [
    dict(
        question="What was the sample size of the Tumaini arm of the Tumaini pilot RCT experiment?",
        gold=30,
        generated="The Tumaini arm of the Tumaini pilot RCT experiment had 30 participants.",
        evaluation="Correct",
    ),
    dict(
        question="What was the attrition rate of the control arm of the Ghana experiment?",
        gold="Not mentioned",
        generated="There is not enough information to answer the question.",
        evaluation="Correct",
    ),
    dict(
        question="What were the trial arms of the diapazetram experiment?",
        gold="Control, diapazetram",
        generated="The trial arms were the playing group and the not playing group",
        evaluation="Incorrect",
    ),
]

INSTRUCTIONS = """For each question, identify whether the student's answer was "Correct" or "Incorrect"."""

EXAMPLE_FORMAT = """
Question: {question}
Correct Answer: {gold}
Student's Answer: {generated}
Correct/Incorrect: {evaluation}
""".strip()


def make_quick_eval_prompt(question: str, gold: str | int, generated: str):
    examples = format_multi(
        EXAMPLE_FORMAT,
        EXAMPLES  # type: ignore[arg-type]
        + [
            dict(
                question=question,
                gold=gold,
                generated=generated,
                evaluation=stop(""),
            )
        ],
    )
    return "\n\n".join((INSTRUCTIONS, "\n\n---\n\n".join(examples)))


def correct_or_incorrect(top_logprobs: dict[str, float]) -> bool:
    correct = [
        math.exp(lp)
        for tok, lp in top_logprobs.items()
        if tok.strip().lower().startswith("c")
    ]
    incorrect = [
        math.exp(lp)
        for tok, lp in top_logprobs.items()
        if tok.strip().lower().startswith("i")
    ]
    if not correct and not incorrect:
        raise ValueError("Ill-formatted completion encountered")
    if not correct:
        return False
    elif not incorrect:
        return True
    return sum(correct) > sum(incorrect)


async def quick_eval(question: str, gold: str | int, generated: str) -> bool:
    prompt = make_quick_eval_prompt(question=question, gold=gold, generated=generated)
    response = await openai_complete(prompt=prompt, max_tokens=1, logprobs=5)
    return correct_or_incorrect(response["choices"][0]["logprobs"]["top_logprobs"][-1])
