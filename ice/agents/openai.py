import math
from typing import Any
from typing import Optional
from typing import Union

import numpy as np
from structlog.stdlib import get_logger

from ice.agents.base import Agent
from ice.agents.base import Stop
from ice.apis.openai import openai_chatcomplete
from ice.apis.openai import openai_complete
from ice.apis.openai import openai_embedding
from ice.environment import env
from ice.utils import longest_common_prefix

log = get_logger()


class OpenAIAgent(Agent):
    """An agent that uses the OpenAI API to generate answers and predictions."""

    def __init__(
        self,
        model: str = "gpt-3.5-turbo-instruct",
        temperature: float = 0.0,
        top_p: float = 1.0,
    ):
        self.model = model
        self.temperature = temperature
        self.top_p = top_p

    async def complete(
        self,
        *,
        prompt: str,
        stop: Stop = None,
        verbose: bool = False,
        default: str = "",
        max_tokens: int = 256,
    ) -> str:
        """Generate an answer to a question given some context."""
        if verbose:
            self._print_markdown(prompt)
        response = await self._complete(prompt, stop=stop, max_tokens=max_tokens)
        completion = self._extract_completion(response)
        if verbose:
            self._print_markdown(completion)
        return completion

    async def predict(self, *, context, default="", verbose=False) -> dict[str, float]:
        """Generate a probability distribution over the next token given some context."""
        if verbose:
            self._print_markdown(context)
        response = await self._complete(context, logprobs=5, max_tokens=1)
        prediction = self._extract_prediction(response)
        if verbose:
            self._print_markdown(prediction)
        return prediction

    async def classify(
        self,
        *,
        prompt: str,
        choices: tuple[str, ...],
        default: Optional[str] = None,
        verbose: bool = False,
    ) -> tuple[dict[str, float], Optional[str]]:
        """Generate a classification from a list of choices given some context and a question."""
        if verbose:
            self._print_markdown(prompt)
            self._print_markdown(choices)

        choice_prefix = longest_common_prefix(choices).rstrip()
        prompt_with_prefix = f"{prompt}{choice_prefix}"

        if prompt_with_prefix.endswith(" "):
            prompt_with_prefix = prompt_with_prefix[:-1]
            default = " "
        else:
            default = ""

        prediction = await self.predict(context=prompt_with_prefix, default=default)

        rel_probs = self._compute_relative_probs(choices, choice_prefix, prediction)

        if verbose:
            self._print_markdown(rel_probs)

        return rel_probs, None

    async def _complete(self, prompt, **kwargs) -> dict:
        """Send a completion request to the OpenAI API with the given prompt and parameters."""
        kwargs.update(
            {
                "model": self.model,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "n": 1,
            }
        )
        response = await openai_complete(prompt, **kwargs)
        if "choices" not in response:
            raise ValueError(f"No choices in response: {response}")
        return response

    def _extract_completion(self, response: dict) -> str:
        """Extract the answer text from the completion response."""
        return response["choices"][0]["text"].strip()

    def _extract_prediction(self, response: dict) -> dict[str, float]:
        """Extract the prediction dictionary from the completion response."""
        answer = response["choices"][0]["logprobs"]["top_logprobs"][0]
        return {k: math.exp(p) for (k, p) in answer.items()}

    def _compute_relative_probs(
        self, choices: tuple[str, ...], choice_prefix: str, prediction: dict[str, float]
    ) -> dict[str, float]:
        """Compute the relative probabilities of the choices based on the prediction."""

        def lookup_prob(choice: str):
            scores = 0.0
            for token, prob in prediction.items():
                if choice[len(choice_prefix) :].startswith(token):
                    scores += prob
            return scores

        abs_probs = {choice: lookup_prob(choice) for choice in choices}
        Z = sum(abs_probs.values())
        if Z < 0.6:
            log.warning(f"{1-Z} of unaccounted probability in classify")
            log.warning(choice_prefix)
            log.warning(str(prediction))
            log.warning(str(abs_probs))

        rel_probs = (
            {choice: prob / Z for (choice, prob) in abs_probs.items()}
            if Z != 0.0
            else abs_probs
        )
        return rel_probs

    def _print_markdown(self, obj: Any):
        """Print the text with markdown formatting."""
        env().print(obj, format_markdown=True)


class OpenAIChatCompletionAgent(Agent):
    """An agent that uses the OpenAI ChatCompletion API to generate completions."""

    def __init__(
        self,
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.0,
        top_p: float = 1.0,
    ):
        self.model = model
        self.temperature = temperature
        self.top_p = top_p

    async def complete(
        self,
        *,
        prompt: str,
        stop: Stop = None,
        verbose: bool = False,
        default: str = "",
        max_tokens: int = 256,
    ) -> str:
        """Generate an answer to a question given some context."""
        if verbose:
            self._print_markdown(prompt)
        response = await self._complete(prompt, stop=stop, max_tokens=max_tokens)
        completion = self._extract_completion(response)
        if verbose:
            self._print_markdown(completion)
        return completion

    async def classify(
        self,
        *,
        prompt: str,
        choices: tuple[str, ...],
        default: Optional[str] = None,
        verbose: bool = False,
    ) -> tuple[dict[str, float], Optional[str]]:
        raise NotImplementedError(
            "OpenAI ChatCompletion has no option to score a classification."
        )

    async def relevance(
        self,
        *,
        context: str,
        question: str,
        verbose: bool = False,
        default: Optional[float] = None,
    ) -> float:
        raise NotImplementedError(
            "OpenAI ChatCompletion has no option to return a relevance score."
        )

    async def predict(
        self, *, context: str, default: str = "", verbose: bool = False
    ) -> dict[str, float]:
        raise NotImplementedError(
            "OpenAI ChatCompletion does not support getting probabilities."
        )

    async def _complete(self, prompt, **kwargs) -> dict:
        """Send a completion request to the OpenAI API with the given prompt and parameters."""
        kwargs.update(
            {
                "model": self.model,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "n": 1,
            }
        )
        messages = [{"role": "user", "content": prompt}]
        response = await openai_chatcomplete(messages, **kwargs)
        if "choices" not in response:
            raise ValueError(f"No choices in response: {response}")
        return response

    def _extract_completion(self, response: dict) -> str:
        """Extract the answer text from the completion response."""
        return response["choices"][0]["message"]["content"].strip()

    def _print_markdown(self, obj: Any):
        """Print the text with markdown formatting."""
        env().print(obj, format_markdown=True)


class OpenAIEmbeddingAgent(Agent):
    """An agent that uses the OpenAI API to generate a relevance score by cosine similarity between two text embeddings."""

    def __init__(
        self,
        model: str = "text-embedding-ada-002",
    ):
        self.model = model

    async def relevance(
        self,
        *,
        context: str,
        question: str,
        verbose: bool = False,
        default: Optional[float] = None,
    ) -> float:
        """Generate a relevance score (cosine similarity) from a context and a question."""
        if verbose:
            self._print_markdown(context)
            self._print_markdown(question)
        context_embedding_response = await openai_embedding(context, model=self.model)
        question_embedding_response = await openai_embedding(question, model=self.model)

        context_embedding = self._extract_embedding(context_embedding_response)
        question_embedding = self._extract_embedding(question_embedding_response)

        relevance = self._cosine_similarity(context_embedding, question_embedding)

        if verbose:
            self._print_markdown(relevance)
        return relevance

    def _extract_embedding(self, response: dict) -> list:
        """Extract the embedding from the response."""
        return response["data"][0]["embedding"]

    def _cosine_similarity(
        self, a: Union[list, np.ndarray], b: Union[list, np.ndarray]
    ) -> float:
        """Compute the cosine similarity between two vectors."""
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    def _print_markdown(self, obj: Any):
        """Print the text with markdown formatting."""
        env().print(obj, format_markdown=True)
