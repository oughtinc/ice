from typing import Optional

from anyio.to_thread import run_sync

from ice.agents.base import Agent
from ice.nn.tfew import load_inference_model
from ice.nn.tfew import PromptedClassificationInput
from ice.nn.tfew import PromptedClassificationOutput
from ice.utils import DynamicBatcher


class TFew(Agent):
    def __init__(
        self,
        origin_model_name: str,
        lora_weights_path: str,
        max_batch_size: int = 32,
        batch_interval_seconds=0.1,
    ):
        self.model = load_inference_model(
            origin_model_name=origin_model_name, lora_weights_path=lora_weights_path
        )
        self.batcher = DynamicBatcher(
            handler=self.model.predict,
            max_batch_size=max_batch_size,
            batch_interval_seconds=batch_interval_seconds,
        )

    async def classify(
        self,
        *,
        prompt: str,
        choices: tuple[str, ...],
        default: Optional[str] = None,
        verbose: bool = False
    ) -> tuple[dict[str, float], Optional[str]]:
        inp = PromptedClassificationInput(prompt=prompt, choices=choices)

        def run_batch() -> PromptedClassificationOutput:
            return self.batcher.process(arg=inp)

        output = await run_sync(run_batch)

        # FIXME: Return full dict of probabilities
        return {output.prediction: output.prob}, None
