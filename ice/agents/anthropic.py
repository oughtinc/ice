from typing import List
from typing import Union

from anthropic import Anthropic

from ice.agents.base import Agent
from ice.settings import settings


class ClaudeAgent(Agent):
    """An agent that uses the Anthropic API to generate answers and predictions."""

    def __init__(self, model: str = "claude-2"):
        self.model = model
        api_key = settings.ANTHROPIC_API_KEY
        self.anthropic = Anthropic(api_key=api_key)

    async def complete(
        self,
        *,
        prompt: str,
        stop: Union[str, List[str], None] = None,
        verbose: bool = False,
        default: str = "",
        max_tokens: int = 256
    ) -> str:
        """Generate an answer to a question given some context."""
        prompt = "\n\nHuman:" + prompt + "\n\nAssistant: My answer is ("
        completion = self.anthropic.completions.create(
            model=self.model,
            max_tokens_to_sample=max_tokens,
            prompt=prompt,
        )
        return completion.completion


class ClaudeChatAgent(Agent):
    """An agent that uses the Anthropic API to generate chat completions."""

    def __init__(self, model: str = "claude-2"):
        self.model = model
        api_key = settings.ANTHROPIC_API_KEY
        self.anthropic = Anthropic(api_key=api_key)

    async def complete(
        self,
        *,
        prompt: str,
        stop: Union[str, List[str], None] = None,
        verbose: bool = False,
        default: str = "",
        max_tokens: int = 256
    ) -> str:
        """Generate an answer to a question given some context."""
        prompt = "\n\nHuman:" + prompt + "\n\nAssistant: My answer is ("
        completion = self.anthropic.completions.create(
            model=self.model,
            max_tokens_to_sample=max_tokens,
            prompt=prompt,
        )
        return completion.completion
