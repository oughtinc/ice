from anthropic import Anthropic

from ice.settings import settings


class ClaudeAgent:
    """An agent that uses the Anthropic API to generate answers and predictions."""

    def __init__(self, model: str = "claude-2"):
        self.model = model
        api_key = settings.ANTHROPIC_API_KEY
        self.anthropic = Anthropic(api_key=api_key)

    async def complete(self, prompt: str, max_tokens: int = 256) -> str:
        """Generate an answer to a question given some context."""
        # Prepend "\n\nHuman:" to the prompt
        prompt = "\n\nHuman:" + prompt + "\n\nAssistant:"
        completion = self.anthropic.completions.create(
            model=self.model,
            max_tokens_to_sample=max_tokens,
            prompt=prompt,
        )
        return completion.completion
