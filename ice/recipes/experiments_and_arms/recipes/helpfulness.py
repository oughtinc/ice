# from ice.formatter.multi import stop, StopSentinel, format_multi
# from ice.trace import trace
# from typing import Sequence, cast
# from structlog.stdlib import get_logger
# from ice.recipe import recipe


# log = get_logger()

# def make_helpfulness_prompt(prefix: str, helpful_line: str) -> str:
#     TEMPLATE = """{helpful_line}

# List them here: {translation}""".strip()

#     helpfulness_cases: list[dict[str, str | StopSentinel]] = [
#         dict(helpful_line="None of the excerpts were helpful", translation="None"),
#         dict(
#             helpful_line="Excerpt 3 was helpful. Excerpts 1, 2, and 4 were not helpful",
#             translation="3",
#         ),
#         dict(
#             helpful_line="Excerpts 1 and 2 were helpful, and excerpt 3 was somewhat helpful. Excerpt 4 was not helpful.",
#             translation="1, 2, 3",
#         ),
#         dict(
#             helpful_line="Excerpts 3 and 4 were somewhat helpful. Excerpts 1 and 2 were not helpful.",
#             translation="3, 4",
#         ),
#     ]
#     for example in helpfulness_cases:
#         example["helpful_line"] = prefix + example["helpful_line"]
#     helpfulness_cases.append(dict(helpful_line=helpful_line, translation=stop("")))

#     filled = format_multi(TEMPLATE, helpfulness_cases)
#     return "\n\n".join(filled)


# HELPFULNESS_TEMPLATE = "Which excerpts, if any, were helpful in understanding {thing_to_understand}? {helpful_line}"

# HELPFULNESS_SHARED = dict(
#     thing_to_understand="how many experiments were conducted in the study"
# )

# HELPFULNESS_PREFIX = "Which excerpts, if any were helpful in understanding how many experiments were conducted in the study?"


# @trace
# async def _which_paras_were_helpful(
#     helpfulness_prefix: str, helpful_line: str
# ) -> list[int]:
#     prompt = make_helpfulness_prompt(helpfulness_prefix, helpful_line)
#     completion = await recipe.agent().answer(prompt=prompt, multiline=False)
#     return [num - 1 for num in _nums_from_answer(completion)]


# def extract_helpful_line(reasoning: str) -> str | None:
#     lines = reasoning.split("\n")
#     helpful_lines = [
#         line for line in lines if "were helpful in understanding" in line.lower()
#     ]
#     if not helpful_lines:
#         log.warning("Unexpected response", reasoning=reasoning)
#         return None
#     if len(helpful_lines) > 1:
#         log.warning("Unexepected response")
#     return helpful_lines[0]


# async def helpful_paragraphs(
#     helpful_line: str, paragraphs: Sequence[Paragraph]
# ) -> Sequence[Paragraph]:
#     idxs = await _which_paras_were_helpful(helpful_line)
#     return [paragraphs[idx] for idx in idxs]
