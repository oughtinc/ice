import re
from collections.abc import Callable
from dataclasses import dataclass
from time import perf_counter

import torch
import torch.nn.functional as F
from structlog.stdlib import get_logger
from torch import nn
from transformers.models.auto.modeling_auto import AutoModelForSeq2SeqLM
from transformers.models.auto.tokenization_auto import AutoTokenizer
from transformers.models.t5.modeling_t5 import T5ForConditionalGeneration
from transformers.models.t5.tokenization_t5_fast import T5TokenizerFast

log = get_logger()

LORA_MODULES = ".*SelfAttention|.*EncDecAttention|.*DenseReluDense"
LORA_LAYERS = "k|v|wi_1.*"


@dataclass
class PromptedClassificationInput:
    prompt: str
    choices: tuple[str, ...]


@dataclass
class T5Batch:
    input_ids: torch.LongTensor
    choices_ids: torch.Tensor


@dataclass
class PromptedClassificationOutput:
    prediction: str
    prob: float


def create_collate_fn(
    tokenizer: T5TokenizerFast,
) -> Callable[[list[PromptedClassificationInput]], T5Batch]:
    def collate_fn(items: list[PromptedClassificationInput]) -> T5Batch:
        input_ids: torch.LongTensor = tokenizer.batch_encode_plus(
            [item.prompt for item in items],
            padding=True,
            truncation=True,
            return_tensors="pt",
        )["input_ids"]
        num_choices = [len(item.choices) for item in items]
        flat_choices_ids: torch.LongTensor = tokenizer.batch_encode_plus(
            [choice for item in items for choice in item.choices],
            padding=True,
            truncation=True,
            return_tensors="pt",
        )["input_ids"]
        choices_ids = flat_choices_ids.view(
            len(items), max(num_choices), -1
        ).contiguous()
        return T5Batch(input_ids, choices_ids)

    return collate_fn


class TfewInferenceModel(nn.Module):
    def __init__(
        self,
        origin_model: T5ForConditionalGeneration,
        tokenizer: T5TokenizerFast,
        lora_weights_path: str,
    ):
        super().__init__()
        self.model = origin_model
        self.tokenizer = tokenizer
        self.collate_fn = create_collate_fn(tokenizer)
        lora_weights = torch.load(lora_weights_path, map_location="cpu")
        load_result = self.model.load_state_dict(lora_weights, strict=False)
        assert (
            not load_result.unexpected_keys
        ), f"Unexpected keys found in state dict: {load_result.unexpected_keys}"
        self.model.to(torch.bfloat16)

    def predict(
        self, batch: list[PromptedClassificationInput]
    ) -> list[PromptedClassificationOutput]:
        with torch.no_grad():
            return self._predict(batch)

    def _predict(
        self, batch: list[PromptedClassificationInput]
    ) -> list[PromptedClassificationOutput]:
        start = perf_counter()
        t5_batch = self.collate_fn(batch)
        input_ids, choices_ids = t5_batch.input_ids, t5_batch.choices_ids
        input_ids, choices_ids = input_ids.to(self.model.device), choices_ids.to(
            self.model.device
        )
        bs, num_choices = choices_ids.size()[:2]
        flat_choices_ids = choices_ids.flatten(0, 1)
        attention_mask = (
            input_ids != self.tokenizer.pad_token_id
        ).float()  # [bs, max_seq_len]
        encoder_hidden_states = self.model.encoder(
            input_ids=input_ids, attention_mask=attention_mask
        )[0]
        encoder_hidden_states = (
            encoder_hidden_states.unsqueeze(dim=1)
            .repeat(1, num_choices, 1, 1)
            .flatten(0, 1)
        )
        attention_mask = (
            attention_mask.unsqueeze(dim=1).repeat(1, num_choices, 1).flatten(0, 1)
        )
        decoder_input_ids = torch.cat(
            [torch.zeros_like(flat_choices_ids[:, :1]), flat_choices_ids[:, :-1]], dim=1
        )
        decoder_attention_mask = (decoder_input_ids == decoder_input_ids).float()
        lm_target = (
            flat_choices_ids
            - 100 * (flat_choices_ids == self.tokenizer.pad_token_id).long()
        )

        model_output = self.model(
            attention_mask=attention_mask,
            encoder_outputs=[encoder_hidden_states],
            decoder_input_ids=decoder_input_ids,
            decoder_attention_mask=decoder_attention_mask,
        )
        choices_scores = (
            F.cross_entropy(
                model_output.logits.flatten(0, 1),
                lm_target.flatten(0, 1),
                reduction="none",
            )
            .view(bs, num_choices, -1)
            .sum(dim=-1)
        )
        # Length normalization
        choices_scores = choices_scores / (
            choices_ids != self.tokenizer.pad_token_id
        ).sum(dim=-1)
        _, prediction = choices_scores.min(dim=1)
        probs, _ = F.softmax(choices_scores, dim=1).max(dim=1)
        pred_list = prediction.tolist()
        pred_choices = [
            example.choices[pred_list[i]] for i, example in enumerate(batch)
        ]
        log.info(
            "T-Few batch inference",
            batch_size=len(batch),
            latency_in_s=perf_counter() - start,
        )
        return [
            PromptedClassificationOutput(prediction=pred_choice, prob=prob)
            for pred_choice, prob in zip(pred_choices, probs.tolist())
        ]


class LoRALinear(nn.Module):
    def __init__(
        self,
        linear_layer: nn.Linear,
    ):
        super().__init__()
        self.in_features = linear_layer.in_features
        self.out_features = linear_layer.out_features
        self.weight = linear_layer.weight
        self.bias = linear_layer.bias
        self.multi_lora_a = nn.parameter.Parameter(
            torch.ones(1, linear_layer.in_features)
        )
        self.multi_lora_b = nn.parameter.Parameter(
            torch.ones(linear_layer.out_features, 1)
        )

    def forward(self, input):
        hidden = F.linear((input * self.multi_lora_a.flatten()), self.weight, self.bias)
        hidden = hidden * self.multi_lora_b.flatten()
        return hidden

    def extra_repr(self):
        return f"in_features={self.in_features}, out_features={self.out_features}, bias={self.bias is not None}"


def inject_low_rank_adaptation(transformer: torch.nn.Module):
    for m_name, module in dict(transformer.named_modules()).items():
        if re.fullmatch(LORA_MODULES, m_name):
            for c_name, layer in dict(module.named_children()).items():
                if re.fullmatch(LORA_LAYERS, c_name):
                    assert isinstance(
                        layer, nn.Linear
                    ), f"LoRA can only be applied to torch.nn.Linear, but {layer} is {type(layer)}."
                    setattr(
                        module,
                        c_name,
                        LoRALinear(layer),
                    )
    return transformer


def make_origin_model(
    origin_model_name: str, max_seq_len: int = 1024
) -> tuple[T5TokenizerFast, T5ForConditionalGeneration]:
    tokenizer: T5TokenizerFast = AutoTokenizer.from_pretrained(origin_model_name)
    origin_model: T5ForConditionalGeneration = AutoModelForSeq2SeqLM.from_pretrained(
        origin_model_name
    )
    tokenizer.model_max_length = max_seq_len
    origin_model = inject_low_rank_adaptation(origin_model)
    origin_model.eval()
    if torch.cuda.is_available():
        origin_model.cuda()
    return tokenizer, origin_model


def load_inference_model(
    origin_model_name: str, lora_weights_path: str, max_seq_len: int = 1024
) -> TfewInferenceModel:
    start = perf_counter()
    log.info(
        "Loading tfew model",
        origin_model_name=origin_model_name,
        lora_weights_path=lora_weights_path,
    )
    tokenizer, origin_model = make_origin_model(origin_model_name, max_seq_len)
    model = TfewInferenceModel(origin_model, tokenizer, lora_weights_path)
    log.info(
        "Loaded tfew model", elapsed_s=perf_counter() - start, device=model.model.device
    )
    return model
