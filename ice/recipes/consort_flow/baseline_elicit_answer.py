import re

from typing import Optional

from structlog import get_logger

from ice.apis.openai import openai_complete


log = get_logger()


NA_PHRASE = "not mentioned in the excerpt"

# Instruct sometimes says "mentioned in the excerpt"
# That's not a useful output, so we want to consider it a non-answer
NA_MATCH_PHRASE = "mentioned in the excerpt"


async def answer_like_elicit_qa(
    *,
    question: str,
    passage: str,
) -> str:

    prompt = _excerpt_prompt(
        qa_question=question,
        excerpt=passage,
    )

    response = await openai_complete(
        prompt,
    )

    choices = response.get("choices")

    response_text = choices[0]["text"].strip()
    answer = _process_instruct_answer(response_text)

    if answer is None:
        return "Not mentioned"

    return answer


def _excerpt_prompt(
    *,
    qa_question: str,
    excerpt: str,
    answer_prefix: Optional[str] = None,
) -> str:
    combined_na_phrase = (
        f"The answer to the question is {NA_PHRASE}"
        if answer_prefix is None
        else f"{answer_prefix} {NA_PHRASE}"
    )

    full_answer_prefix = (
        "Answer:" if answer_prefix is None else f"Answer: {answer_prefix}"
    )

    return f"""Answer the question "{qa_question}" based on the excerpt from a research paper. \
Try to answer, but say "{combined_na_phrase}" if you don't know how to answer. \
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
    if re.search(NA_MATCH_PHRASE, text, re.IGNORECASE):
        return None

    text = re.sub(r"^the |^that |^is |\.$", "", text)

    return text
