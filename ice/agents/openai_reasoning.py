from collections import Counter
from typing import Optional

from structlog.stdlib import get_logger

from ice.agents.base import Agent
from ice.agents.base import Stop
from ice.apis.openai import openai_complete

log = get_logger()


class OpenAIReasoningAgent(Agent):
    def __init__(
        self,
        model: str = "text-davinci-002",
        temperature: float = 0.0,
        top_p: float = 1.0,
        num_workers: int = 1,
        reasoning_prefix: str = "Reasoning: ",
    ):
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.num_workers = num_workers
        self.reasoning_prefix = reasoning_prefix

    def _answer_prefix(self, prompt: str) -> str:
        return prompt.split("\n")[-1]

    async def complete(
        self,
        *,
        prompt: str,
        stop: Stop = None,
        verbose: bool = False,
        default: str = "",
        max_tokens: int = 256,
    ) -> str:
        answer_prefix = self._answer_prefix(prompt)

        # Generate the prompt for the reasoning task
        reasoning_prompt = self._generate_reasoning_prompt(prompt)

        # Request multiple completions from the API
        response = await self._request_completions(reasoning_prompt)

        # Parse the responses and aggregate the answers and reasonings
        answers, reasonings = await self._parse_and_aggregate_responses(
            reasoning_prompt, response, answer_prefix, stop=stop
        )

        # Return the most common answer (TODO: Smarter aggregation)
        return answers.most_common(1)[0][0]

    async def predict(self, *, context, default="", verbose=False) -> dict[str, float]:
        raise NotImplementedError

    async def classify(
        self,
        *,
        prompt: str,
        choices: tuple[str, ...],
        default: Optional[str] = None,
        verbose: bool = False,
    ) -> tuple[dict[str, float], Optional[str]]:
        # Generate the prompt for the reasoning task
        answer_prefix = self._answer_prefix(prompt)
        reasoning_prompt = self._generate_reasoning_prompt(prompt)

        # Request multiple completions from the API
        response = await self._request_completions(reasoning_prompt)

        # Parse the responses and aggregate the answers and reasonings
        answers, reasonings = await self._parse_and_aggregate_responses(
            reasoning_prompt, response, answer_prefix, choices=choices
        )

        # Return a dict [str, float] and the joined reasonings
        return self._format_result(answers, reasonings)

    def _generate_reasoning_prompt(self, prompt: str) -> str:
        answer_prefix = self._answer_prefix(prompt)

        # Replace the answer prefix with the reasoning prefix
        prompt = prompt[: -len(answer_prefix)] + self.reasoning_prefix
        return prompt

    async def _request_completions(self, prompt: str) -> dict:
        # Adjust the temperature based on the number of workers
        temperature = (
            self.temperature
            if self.num_workers == 1
            else min(self.temperature + 0.4, 1.0)
        )

        # Request multiple completions from the API
        response = await openai_complete(
            prompt,
            stop=None,
            model=self.model,
            temperature=temperature,
            top_p=self.top_p,
            n=self.num_workers,
        )
        return response

    async def _parse_and_aggregate_responses(
        self,
        prompt: str,
        response: dict,
        answer_prefix: str,
        stop: Stop = None,
        choices: Optional[tuple[str, ...]] = None,
    ) -> tuple[Counter[str], list[str]]:
        # Extract the response texts
        response_texts = [choice["text"] for choice in response["choices"]]

        # Parse the responses and aggregate the answers and reasonings
        answers: Counter[str] = Counter()
        reasonings: list[str] = []
        for i, response_text in enumerate(response_texts):
            # Check if the response contains the answer prefix
            if answer_prefix not in response_text:
                # If not, request an explicit answer from the API
                response_text = await self._request_explicit_answer(
                    prompt, response_text, answer_prefix, stop=stop
                )

            # Parse the answer and the reasoning from the response
            answer, reasoning = self._parse_answer_and_reasoning(
                response_text, answer_prefix, stop=stop
            )

            # Update the answer counts and the reasoning list
            if choices is not None:
                for choice in choices:
                    if answer.strip().startswith(choice.strip()):
                        answers[choice] += 1
            else:
                answers[answer] += 1

            reasonings.append(reasoning)

        return answers, reasonings

    async def _request_explicit_answer(
        self, prompt: str, response_text: str, answer_prefix: str, stop: Stop = None
    ) -> str:
        # Generate a follow-up prompt with the answer prefix
        followup_prompt = f"{prompt}{response_text}\n\n{answer_prefix}"

        # Request a single completion from the API
        followup_response = await openai_complete(
            followup_prompt,
            stop=stop,
            model=self.model,
            temperature=self.temperature,
            top_p=self.top_p,
            n=1,
        )

        # Extract the follow-up response text
        followup_response_text = self._enforce_stop(
            followup_response["choices"][0]["text"], stop
        )

        # Append the follow-up response text to the original response text
        response_text += f"\n\n{answer_prefix}{followup_response_text}"

        return response_text

    def _enforce_stop(self, response_text: str, stop: Stop) -> str:
        if stop is None:
            return response_text.strip()
        return response_text.strip().split("".join(stop))[0]

    def _parse_answer_and_reasoning(
        self, response_text: str, answer_prefix: str, stop: Stop
    ) -> tuple[str, str]:
        # Split the response text by the answer prefix
        response_parts = response_text.split(answer_prefix, maxsplit=1)

        # Check that the response has two parts
        if len(response_parts) != 2:
            log.warning(f"Unexpected response format: {response_text}")
            raise ValueError(f"Unexpected response format: {response_text}")

        # Strip the whitespace from the parts
        reasoning, answer = map(str.strip, response_parts)

        # Check that the reasoning and the answer are not empty
        if not reasoning or not answer:
            log.warning(f"Empty reasoning or answer: {response_text}")

        answer = self._enforce_stop(answer, stop)

        return answer, reasoning

    def _format_result(
        self, answers: Counter[str], reasonings: list[str]
    ) -> tuple[dict[str, float], str]:
        # Join the reasonings with counts
        joined_reasonings = self._join_texts_with_counts(reasonings)

        # Convert the answers counter to a dictionary of probabilities
        total = sum(answers.values())
        answer_probs = {k: v / total for k, v in answers.items()}

        # Sort the dictionary by descending probability
        answer_probs = dict(
            sorted(answer_probs.items(), key=lambda x: x[1], reverse=True)
        )
        return answer_probs, joined_reasonings

    def _join_texts_with_counts(self, texts: list[str]) -> str:
        """
        Given a list like ["bla", "blubb", "bla", "foo", "blubb"], return
        an answer like "(3) bla\n\n(2) blubb\n\n(1)foo".
        """
        counts = Counter(texts)
        return "\n\n".join(
            f"({count}) {text}" for (text, count) in counts.most_common()
        )
