from anyio.to_thread import run_sync
from transformers.pipelines import pipeline

from ice.agents.base import Agent


class SquadAgent(Agent):
    def __init__(self, model_name: str = "z-uo/roberta-qasper"):
        self.nlp = pipeline(
            "question-answering", model=model_name, tokenizer=model_name
        )

    async def relevance(
        self, *, question, context, verbose=False, default=None
    ) -> float:
        response = await run_sync(
            self.nlp, dict(question=question, context=context), cancellable=True
        )
        return response["score"]
