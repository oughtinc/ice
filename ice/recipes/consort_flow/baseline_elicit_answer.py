import re
from collections.abc import Sequence
from typing import Optional

from structlog import get_logger

from ice.apis.openai import openai_complete
from ice.recipes.program_search.nodes.answer.types import Demonstration


log = get_logger()


_NA_PHRASE = "not mentioned in the excerpt"
COMBINED_NA_PHRASE = f"The answer to the question is {_NA_PHRASE}"

# Instruct sometimes says "mentioned in the excerpt"
# That's not a useful output, so we want to consider it a non-answer
_NA_MATCH_PHRASE = "mentioned in the excerpt"


async def answer_like_elicit_qa(
    *,
    question: str,
    passage: str,
) -> str:
    prompt = elicit_qa_prompt(
        qa_question=question,
        excerpt=passage,
    )

    response = await openai_complete(prompt, stop=None)

    choices = response.get("choices")

    response_text = choices[0]["text"].strip()
    answer = _process_instruct_answer(response_text)

    if answer is None:
        return "Not mentioned"

    return answer


def convert_to_non_answer(example: Demonstration) -> Demonstration:
    return Demonstration(
        question=example.question, texts=example.texts, answer=COMBINED_NA_PHRASE
    )


def make_few_shot_examples(
    examples: Sequence[Demonstration],
) -> Sequence[tuple[str, str]]:
    return [
        (
            elicit_qa_prompt(
                qa_question=e.question, excerpt="\n\n".join((t for t in e.texts))
            ),
            "".join((" ", e.answer.strip())),
        )
        for e in examples
    ]


def elicit_qa_prompt(
    *,
    qa_question: str,
    excerpt: str,
) -> str:
    full_answer_prefix = "Answer:"

    return f"""Answer the question "{qa_question}" based on the excerpt from a research paper. \
Try to answer, but say "{COMBINED_NA_PHRASE}" if you don't know how to answer. \
Include everything that the paper excerpt has to say about the answer. \
Make sure everything you say is supported by the excerpt. \
The excerpt may cite other papers; \
answer about the paper you're reading the excerpt from, not the papers that it cites. \
Answer in one phrase or sentence:

Paper excerpt: {excerpt}

Question: {qa_question}

{full_answer_prefix}"""


def _process_instruct_answer(text: str) -> Optional[str]:
    text = text.strip()
    if re.search(_NA_MATCH_PHRASE, text, re.IGNORECASE):
        return None

    text = re.sub(r"^the |^that |^is |\.$", "", text)

    return text
