import functools
import re
import time
from enum import IntEnum
from typing import Tuple

import torch
from structlog.stdlib import get_logger
from transformers.models.auto.modeling_auto import AutoModelForSeq2SeqLM
from transformers.models.auto.tokenization_auto import AutoTokenizer
from transformers.models.bart.modeling_bart import BartForConditionalGeneration
from transformers.models.bart.modeling_bart import BartForSequenceClassification
from transformers.models.bart.tokenization_bart_fast import BartTokenizerFast
from transformers.models.t5.modeling_t5 import T5ForConditionalGeneration
from transformers.models.t5.tokenization_t5_fast import T5TokenizerFast

from ice.paper import split_sentences

log = get_logger()


@functools.cache
def get_device() -> torch.device:
    device_name = "cuda" if torch.cuda.is_available() else "cpu"
    if device_name == "cpu":
        log.warning("Running on CPU could be *very* slow.")
    log.info(f"Running on {str(device_name).upper()}.")
    return torch.device(device_name)


@functools.cache
def load_T5() -> Tuple[T5TokenizerFast, T5ForConditionalGeneration]:
    device = get_device()
    T5_tokenizer = AutoTokenizer.from_pretrained("castorini/monot5-base-msmarco-10k")

    T5_model = AutoModelForSeq2SeqLM.from_pretrained(
        "castorini/monot5-base-msmarco-10k"
    ).to(device)
    return T5_tokenizer, T5_model


@functools.cache
def load_BART() -> Tuple[BartTokenizerFast, BartForConditionalGeneration]:
    device = get_device()
    BART_tokenizer = BartTokenizerFast.from_pretrained("facebook/bart-large-mnli")

    BART_model = BartForSequenceClassification.from_pretrained(
        "facebook/bart-large-mnli"
    ).to(device)
    return BART_tokenizer, BART_model


@functools.cache
def load_T0(
    model_name="bigscience/T0_3B",
) -> Tuple[T5TokenizerFast, T5ForConditionalGeneration]:
    # For testing
    model_name = "t5-small"
    device = get_device()
    T0_tokenizer = AutoTokenizer.from_pretrained(model_name)

    i: float = time.time()
    T0_model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(device)
    log.info(f"Loaded T0 in {time.time() - i} seconds.")
    return T0_tokenizer, T0_model


def get_sentence(paragraph: str, number: str) -> str:
    for sentence in split_sentences(paragraph):
        if number in sentence:
            return sentence
    return ""


class IsCategory(IntEnum):
    NO = 0
    YES = 1


def BART_classify(
    category: str, paragraph: str, number: str, BART_threshold=2 / 3
) -> IsCategory:  # Classification is either "Y" or "N"
    device = get_device()
    BART_tokenizer, BART_model = load_BART()
    hypothesis = f"The number {number} is about the {category} of the study."
    premise = get_sentence(paragraph, number)
    if not premise:
        log.info(f"Could not find number {number} in paragraph")
        return IsCategory.NO
    input_ids = BART_tokenizer.encode(
        premise, hypothesis, return_tensors="pt", max_length=512, truncation=True
    ).to(device)
    with torch.no_grad():
        logits = BART_model(input_ids)[0][:, [0, 2]]
        logits = logits.softmax(dim=-1)[0]
    return IsCategory((logits[1] > BART_threshold).item())


def T5_predict(question: str, document: str) -> float:
    device = get_device()
    T5_tokenizer, T5_model = load_T5()
    T5_input = f"Query: {question} Document: {document} Relevant:"
    inputs = T5_tokenizer.encode(
        T5_input, return_tensors="pt", max_length=512, truncation=True
    ).to(device)
    false_token_index = T5_tokenizer.encode("false", return_tensors="pt")[0][0].to(
        device
    )
    true_token_index = T5_tokenizer.encode("true", return_tensors="pt")[0][0].to(device)
    outputs = T5_model.generate(
        inputs, return_dict_in_generate=True, output_scores=True
    )
    scores = outputs["scores"][0][:, [true_token_index, false_token_index]].softmax(
        dim=-1
    )
    return scores[0][0].item()


def T5_score(question: str, document: str) -> float:
    scores = []
    for sentence in split_sentences(document):
        scores.append(T5_predict(question, sentence))
    if not scores:
        return 0
    return sum(scores) / len(
        scores
    )  # Could use max(scores) instead of sum(scores)/len(scores)


def T0_classify(
    category: str, abstract: str, paragraph: str, number: str, t0_threshold=0.45
) -> IsCategory:
    device = get_device()
    T0_tokenizer, T0_model = load_T0()
    question = f"Is the number {number} is about the {category} of the study?"
    premise = get_sentence(paragraph, number)
    if not premise:
        log.info(f"Could not find number {number} in paragraph")
        return IsCategory.NO
    context = abstract + premise
    prompt = f"""{context}
Given the context: {question}
Possible answers: Yes the number {number} is about the {category} of the study?, No the number {number} is not about the {category} of the study?"""

    # Run T0_3B
    inputs = T0_tokenizer.encode(
        prompt, return_tensors="pt", max_length=1024, truncation=True
    ).to(device)
    outputs = T0_model.generate(
        inputs, return_dict_in_generate=True, output_scores=True, max_new_tokens=2
    )
    false_token_index, true_token_index = (
        T0_tokenizer.encode("No")[0],
        T0_tokenizer.encode("Yes")[0],
    )
    scores = outputs["scores"][0][:, [true_token_index, false_token_index]].softmax(
        dim=-1
    )
    scores = scores[0]

    return IsCategory((scores[0] > t0_threshold).item())


# Credit: https://stackoverflow.com/questions/39936527/python-removing-references-from-a-scientific-paper


# Remove citations
def remove_citations(s: str) -> str:
    return re.sub(r"\s\([A-Z][a-z]+,\s[A-Z][a-z]?\.[^\)]*,\s\d{4}\)", "", s)


threshold = 0.0009468319839808456
# Max score threshold is 0.001010593439036711
# Average score threshold is 0.0009468319839808456


def BERT_T5_T0(
    category: str,
    abstract: str,
    paragraph: str,
    number: str,
    threshold=0.0010661712990630886,
) -> IsCategory:
    paragraph, abstract = remove_citations(paragraph), remove_citations(abstract)
    score = T5_score(f"What is the {category} of this study?", paragraph)
    if score < threshold:
        log.info("T5 score too low", t5_score=score)
        return IsCategory.NO
    bert_classification = BART_classify(category, paragraph, number)
    if bert_classification == IsCategory.NO:
        log.info("Failed BART")
        return IsCategory.NO
    T0_classification = T0_classify(category, abstract, paragraph, number)
    if T0_classification == IsCategory.NO:
        log.info("Failed T0")
        return IsCategory.NO
    log.info(
        "BERT, T5 and T0 agree on the answer Y.", paragraph=paragraph, number=number
    )
    return IsCategory.YES
