from types import SimpleNamespace
from typing import Any
from typing import Optional

from pydantic import BaseModel
from structlog.stdlib import get_logger

from ice.agent import Agent
from ice.evaluation.evaluate_recipe_result import RecipeResult
from ice.metrics.gold_standards import get_gold_standards
from ice.metrics.gold_standards import list_experiments
from ice.paper import get_full_document_id
from ice.paper import Paper
from ice.paper import Paragraph
from ice.recipe import Recipe
from ice.utils import flatten
from ice.utils import longest_common_prefix
from ice.utils import map_async

log = get_logger()

Experiment = str


def get_section_title(paragraph: Paragraph) -> str:
    if not paragraph.sections:
        return "Unknown section"
    return paragraph.sections[0].title


def parse_quotes(s: str) -> list[str]:
    if s.strip() == "n/a":
        return []
    return [clean_quote for line in s.split("\n") if (clean_quote := line.strip('" '))]


def make_placebo_kind_aggregation_prompt(
    experiment: str, quotes: list[str], descriptions: list[str]
) -> str:
    quotes_str = "\n".join(f'- "{quote}"' for quote in quotes)
    description_str = "\n".join(f"- {description}" for description in descriptions)
    prompt = f"""Rewrite a description of the placebo used in the "{experiment}" experiment of a scientific paper.

Quotes from the paper that mention the placebo:
{quotes_str}

Descriptions of the placebo used in the "{experiment}" experiment:
{description_str}

Rewritten description of the placebo used in the "{experiment}" experiment (without repetition, using only information from the quotes and initial description): The placebo was"""
    return prompt


class DialogState(BaseModel):
    agent: Agent
    context: str
    verbose: bool = False

    async def ask(self, question: str, multiline=True, answer_prefix=""):
        partial_answer = await self.agent.complete(
            prompt=f"{self.context}\n\nQ: {question}\n\nA: {answer_prefix}",
            stop=None if multiline else "\n",
        )
        answer = f"{answer_prefix} {partial_answer}".strip()
        successor_context = f"{self.context}\n\nQ: {question}\n\nA: {answer}"
        new_state = DialogState(
            agent=self.agent, context=successor_context, verbose=self.verbose
        )
        if self.verbose:
            new_state.pprint()
        return answer, new_state

    async def multiple_choice(
        self, question: str, answers: list[str]
    ) -> tuple[dict[str, float], "DialogState"]:
        answer_prefix = longest_common_prefix(answers).rstrip()
        new_context = f"{self.context}\n\nQ: {question}\n\nA: {answer_prefix}"
        prediction = await self.agent.predict(context=new_context, default=" ")

        def lookup_prob(answer: str):
            scores = 0.0
            for token, prob in prediction.items():
                if answer[len(answer_prefix) :].startswith(token):
                    scores += prob
            return scores

        abs_probs = {answer: lookup_prob(answer) for answer in answers}
        Z = sum(abs_probs.values())
        if Z < 0.8:
            log.warning(f"{1-Z} of unaccounted probability in multiple choice")
            log.warning(answer_prefix)
            log.warning(str(prediction))
            log.warning(str(abs_probs))
        rel_probs = {answer: prob / Z for (answer, prob) in abs_probs.items()}
        most_likely_answer = max(answers, key=lambda answer: rel_probs[answer])

        successor_context = new_context[: -len(answer_prefix)] + most_likely_answer
        new_state = DialogState(
            agent=self.agent, context=successor_context, verbose=self.verbose
        )
        if self.verbose:
            new_state.pprint()

        return rel_probs, new_state

    def pprint(self):
        # rich.print(Panel(self.context))
        s = f"""
{'-'*80}
{self.context}
{'-'*80}
"""
        # env().print(s, format_markdown=True)
        print(s)

    class Config:
        arbitrary_types_allowed = True


def make_initial_paragraph_context(
    paragraph: Paragraph, experiment: str, section_title: str
) -> str:
    prompt = f"""Below is a paragraph from the "{section_title}" section of a scientific paper. We'll answer questions about potential use of a placebo in the "{experiment}" experiment.

The paragraph: "{paragraph}"
""".strip()
    return prompt


class PlaceboDialogs(Recipe):
    verbose = False

    msg = SimpleNamespace(
        **dict(
            relevant="The paragraph mentions the placebo procedure.",
            irrelevant="The paragraph doesn't mention the placebo procedure.",
            open_control="The paragraph states that the experiment was open-control/open-label.",
            no_open_control="The paragraph doesn't state that the experiment was open-control/open-label.",
            explicit_placebo="The paragraph states that the experiment used a placebo.",
            not_explicit_placebo="The paragraph doesn't state that the experiment used a placebo.",
            explicit_no_placebo="The paragraph states that the experiment didn't use a placebo.",
            not_explicit_no_placebo="The paragraph doesn't state that the experiment didn't use a placebo.",
            placebo_described="The kind of placebo is described.",
            placebo_undescribed="The kind of placebo is not described.",
            explicit_control="The paragraph states that there was a control group.",
            not_explicit_control="The paragraph doesn't state that there was a control group.",
            explicit_control_treatment="The paragraph says whether the control group was treated or not.",
            not_explicit_control_treatment="The paragraph doesn't say whether the control group was treated or not.",
            treatment_nothing="The control group treatment was nothing.",
            treatment_placebo="The control group treatment was a placebo.",
            treatment_baseline="The control group treatment was another baseline treatment.",
            treatment_unspecified="The control group treatment was unspecified.",
        )
    )

    async def analyze_paragraph(self, paragraph: Paragraph, experiment: Experiment):
        section_title = get_section_title(paragraph)
        initial_paragraph_context = make_initial_paragraph_context(
            paragraph, experiment, section_title
        )

        msg = self.msg

        state = DialogState(
            agent=self.agent(), context=initial_paragraph_context, verbose=self.verbose
        )
        return_info: dict[str, Any] = {"section": section_title}

        # Ask about the control group

        control_placebo_prob: Optional[float] = None
        control_no_placebo_prob: Optional[float] = None
        explicit_control_quotes = []

        explicit_control_p, state = await state.multiple_choice(
            question=f"""Does the paragraph state that there was a control group in the "{experiment}" experiment? If yes, say "{msg.explicit_control}". If no, say "{msg.not_explicit_control}".""",
            answers=[msg.explicit_control, msg.not_explicit_control],
        )

        if explicit_control_p[msg.explicit_control] > 0.5:
            explicit_control_quotes_str, state = await state.ask(
                question=f"""What quotes from the paragraph mention the control group in the "{experiment}" experiment? Say n/a if none are relevant to the control group""",
            )

            control_treatment_p, state = await state.multiple_choice(
                question=f"""Does the paragraph say whether the control group was treated or not? If yes, say "{msg.explicit_control_treatment}". If no, say "{msg.not_explicit_control_treatment}".""",
                answers=[
                    msg.explicit_control_treatment,
                    msg.not_explicit_control_treatment,
                ],
            )

            if control_treatment_p[msg.explicit_control_treatment] > 0.5:
                control_treatment_p, state = await state.multiple_choice(
                    question=f"""Which of the following is true: The control group treatment was {msg.treatment_nothing} / {msg.treatment_placebo} / {msg.treatment_baseline} / {msg.treatment_unspecified}?""",
                    answers=[
                        msg.treatment_nothing,
                        msg.treatment_placebo,
                        msg.treatment_baseline,
                        msg.treatment_unspecified,
                    ],
                )

                control_placebo_prob = control_treatment_p[msg.treatment_placebo]

                # "nothing" and "another baseline" imply no placebo
                control_no_placebo_prob = max(
                    control_treatment_p[msg.treatment_nothing],
                    control_treatment_p[msg.treatment_baseline],
                )

                if control_placebo_prob > 0.5 or control_no_placebo_prob > 0.5:
                    explicit_control_quotes = parse_quotes(explicit_control_quotes_str)

        # Ask whether control was open

        open_control_p, state = await state.multiple_choice(
            question=f"""Does the paragraph state that the "{experiment}" experiment was "open-control" or "open-label"? If yes, say "{msg.open_control}". If no, say "{msg.no_open_control}".""",
            answers=[msg.open_control, msg.no_open_control],
        )

        if open_control_p[msg.open_control] < 0.5:
            open_control_quotes = []
        else:
            open_control_quotes_str, state = await state.ask(
                "Which quotes from the paragraph explicitly talk about whether the study was open-control/open-label? One per line. Say n/a if there are none."
            )
            open_control_quotes = parse_quotes(open_control_quotes_str)

        # Ask about quotes that talk about whether a placebo was used

        used_placebo_quotes_str, state = await state.ask(
            "Which quotes from the paragraph talk about whether a placebo was used or not? One per line. Say n/a if none are relevant to placebos."
        )
        used_placebo_quotes = parse_quotes(used_placebo_quotes_str)

        explicit_placebo_p, state = await state.multiple_choice(
            question=f"""Does the paragraph state explicitly that the "{experiment}" experiment used a placebo? If yes, say "{msg.explicit_placebo}". If no, say "{msg.not_explicit_placebo}".""",
            answers=[msg.explicit_placebo, msg.not_explicit_placebo],
        )

        explicit_no_placebo_p, state = await state.multiple_choice(
            question=f"""Does the paragraph state explicitly that the "{experiment}" experiment didn't use a placebo? If yes, say "{msg.explicit_no_placebo}". If no, say "{msg.not_explicit_no_placebo}".""",
            answers=[msg.explicit_no_placebo, msg.not_explicit_no_placebo],
        )

        no_placebo_prob = max(
            open_control_p[msg.open_control],
            explicit_no_placebo_p[msg.explicit_no_placebo],
            control_no_placebo_prob or 0.0,
        )
        placebo_prob = max(
            explicit_placebo_p[msg.explicit_placebo],
            control_placebo_prob or 0.0,
        )

        return_info["used_placebo"] = {
            "quotes": list(
                set(used_placebo_quotes + open_control_quotes + explicit_control_quotes)
            ),
            "components": {
                "open_control": open_control_p[msg.open_control],
                "explicit_placebo": explicit_placebo_p[msg.explicit_placebo],
                "explicit_no_placebo": explicit_no_placebo_p[msg.explicit_no_placebo],
                "control_placebo": control_placebo_prob,
                "control_no_placebo": control_no_placebo_prob,
            },
            "placebo_prob": placebo_prob,
            "no_placebo_prob": no_placebo_prob,
        }

        if placebo_prob < 0.5:
            return return_info

        # Ask about quotes that talk about what the placebo was

        placebo_kind_quotes_str, state = await state.ask(
            f"""Which quotes from the paragraph describe what the placebo was in the "{experiment}" experiment? One per line. Say n/a if none describe the placebo."""
        )
        placebo_kind_quotes = parse_quotes(placebo_kind_quotes_str)

        # Ask about whether the quotes describe what the placebo was

        placebo_kind_p, state = await state.multiple_choice(
            f"""Does the paragraph say what kind of placebo was used in the "{experiment}" experiment? Say "{msg.placebo_described}" if it explains something about the placebo. Say "{msg.placebo_undescribed}" if it doesn't say what the placebo was like.""",
            answers=[msg.placebo_described, msg.placebo_undescribed],
        )

        return_info["placebo_kind"] = {
            "quotes": placebo_kind_quotes,
            "probs": placebo_kind_p,
        }
        if placebo_kind_p[msg.placebo_described] < 0.5:
            return return_info

        # Ask what the placebo was

        placebo_kind, state = await state.ask(
            f"""What does the paragraph say about what the placebo was like in the "{experiment}" experiment?"""
        )

        return_info["placebo_kind"]["answer"] = placebo_kind
        return return_info

    @staticmethod
    async def aggregate_used_placebo(paragraph_infos: list[dict]) -> dict:
        aggregate = {}

        pro_placebo_infos = []
        con_placebo_infos = []
        for paragraph_info in paragraph_infos:
            if "used_placebo" in paragraph_info:
                used_placebo_prob = paragraph_info["used_placebo"]["placebo_prob"]
                no_placebo_prob = paragraph_info["used_placebo"]["no_placebo_prob"]
                if used_placebo_prob > 0.5:
                    pro_placebo_infos.append(paragraph_info["used_placebo"])
                if no_placebo_prob > 0.5:
                    con_placebo_infos.append(paragraph_info["used_placebo"])
        if pro_placebo_infos and not con_placebo_infos:
            aggregate = {
                "answer": "Placebo",
                "quotes": flatten([info["quotes"] for info in pro_placebo_infos]),
            }
        elif not pro_placebo_infos and con_placebo_infos:
            aggregate = {
                "answer": "No placebo",
                "quotes": flatten([info["quotes"] for info in con_placebo_infos]),
            }
        elif pro_placebo_infos and con_placebo_infos:
            aggregate = {
                "answer": "Unclear",
                "quotes": flatten(
                    [info["quotes"] for info in con_placebo_infos + pro_placebo_infos]
                ),
                "quotes_pro": [info["quotes"] for info in pro_placebo_infos],
                "quotes_cons": [info["quotes"] for info in con_placebo_infos],
            }
        else:
            aggregate = {"answer": "Not mentioned", "quotes": []}

        return aggregate

    async def aggregate_placebo_kind(
        self, paragraph_infos: list[dict], experiment: str
    ) -> dict:
        answers = []
        quotes = []

        for paragraph_info in paragraph_infos:
            if "placebo_kind" in paragraph_info:
                kind = paragraph_info["placebo_kind"]
                if "answer" in kind:
                    answers.append(kind["answer"])
                    quotes += kind["quotes"]
        prompt = make_placebo_kind_aggregation_prompt(experiment, quotes, answers)

        answer_completion = await self.agent().complete(
            prompt=prompt,
        )
        answer = f"The placebo was {answer_completion}"

        if self.verbose:
            print(f"{prompt} {answer_completion}")

        return {"answer": answer, "quotes": quotes, "component_answers": answers}

    async def analyze_experiment(self, paper: Paper, experiment: Experiment):
        paragraphs = [
            paragraph
            for paragraph in paper.paragraphs
            if str(paragraph).strip()
            and len(str(paragraph)) > 40  # Against hallucination
        ]

        # Run paragraph-wise dialogs
        paragraph_infos = await map_async(
            paragraphs,
            lambda paragraph: self.analyze_paragraph(paragraph, experiment),
            max_concurrency=10 if self.mode == "machine" else 1,
            show_progress_bar=True,
        )

        # Aggregate paragraph information
        aggregate_used = await self.aggregate_used_placebo(paragraph_infos)
        aggregate_kind = await self.aggregate_placebo_kind(paragraph_infos, experiment)

        # Summarize aggregates to match RecipeResult schema
        has_placebo_info = aggregate_used["answer"] == "Placebo"
        placebo_result = (
            aggregate_kind["answer"] if has_placebo_info else aggregate_used["answer"]
        )
        placebo_excerpts = list(
            set(aggregate_kind["quotes"] + aggregate_used["quotes"])
        )

        # Log for analysis
        self.maybe_add_to_results(
            [
                RecipeResult(
                    document_id=paper.document_id,
                    question_short_name="placebo",
                    experiment=experiment,
                    classifications=[
                        aggregate_used["answer"],
                        "Placebo"
                        if has_placebo_info
                        else "No placebo or placebo not mentioned",
                    ],
                    answer=placebo_result,
                    result=placebo_result,
                    excerpts=placebo_excerpts,
                )
            ]
        )

        gold_standards = get_gold_standards(
            document_id=paper.document_id,
            question_short_name="placebo",
            experiment=experiment,
        )

        if gold_standards:
            gold_standard = gold_standards[0]
            gold_answer = gold_standard.answer
            gold_quotes = gold_standard.quotes
        else:
            gold_answer = "n/a"
            gold_quotes = []

        return {
            "result": {"actual": placebo_result, "gold": gold_answer},
            "quotes": {"actual": placebo_excerpts, "gold": gold_quotes},
            "paragraph_infos": paragraph_infos,
            "aggregate": {
                "used_placebo": aggregate_used,
                "placebo_kind": aggregate_kind,
            },
        }

    async def run(self, paper: Paper):
        experiments = list_experiments(
            document_id=get_full_document_id(paper.document_id)
        )

        results_by_experiment = {}
        for experiment in experiments:
            experiment_result = await self.analyze_experiment(paper, experiment)
            results_by_experiment[experiment] = experiment_result

        return results_by_experiment
