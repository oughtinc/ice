import math

from functools import partial

from structlog.stdlib import get_logger

from ice.apis.openai import openai_complete
from ice.recipe import recipe
from ice.utils import map_async
from ice.utils import n_tokens

log = get_logger()

PROMPTS = [
    "The Golden Gate bridge is in",
    "The Statue of Liberty is in",
    "The Eiffel Tower is in",
]

COMPLETION = " San Francisco, California, USA"


async def completion_perplexity(
    prompt: str = PROMPTS[0],
    completion: str = COMPLETION,
) -> float:
    """Calculate the perplexity of a completion given a prompt."""
    if not completion[0].isspace():
        log.warning("Completion does not start with whitespace!", completion=completion)

    #log.info("Calling GPT-3", num_tokens=n_tokens(prompt + completion))
    response = await openai_complete(
        prompt=prompt + completion,
        max_tokens=0,
        logprobs=1,
        echo=True,
    )

    choices = response.get("choices", [])

    if not choices:
        raise ValueError("No choices returned from OpenAI API")

    choice = choices[0]

    tokens = choice["logprobs"]["tokens"]

    logits = choice["logprobs"]["token_logprobs"]

    completion_logits = []

    current_completion = ""

    for token, logit in reversed(list(zip(tokens, logits))):
        current_completion = token + current_completion

        if not current_completion in completion:
            break

        completion_logits.append(logit)
    
    perplexity = math.exp(-sum(completion_logits) / len(completion_logits))

    return perplexity

async def generation_perplexity(
    prompt: str = PROMPTS[0],
    completion: str = COMPLETION,
    max_tokens: int = 384,
) -> float:
    """Calculate the perplexity of a completion given a prompt."""
    if not completion[0].isspace():
        log.warning("Completion does not start with whitespace!", completion=completion)

    #log.info("Calling GPT-3", num_tokens=n_tokens(prompt + completion))
    response = await openai_complete(
        prompt=prompt,
        max_tokens=max_tokens,
        logprobs=1,
        temperature=0.0,
        stop=("<|endoftext|>"),
    )

    choices = response.get("choices", [])

    if not choices:
        raise ValueError("No choices returned from OpenAI API")

    choice = choices[0]

    tokens = choice["logprobs"]["tokens"][:-1] # Remove the end of text token

    logits = choice["logprobs"]["token_logprobs"][:-1] # Remove the end of text token

    completion_logits = []

    current_completion = ""

    for token, logit in reversed(list(zip(tokens, logits))):
        current_completion = token + current_completion

        if not current_completion in completion:
            break

        completion_logits.append(logit)
    
    perplexity = math.exp(-sum(completion_logits) / len(completion_logits)) if completion_logits else 10000

    return perplexity


async def best_completion(
    prompts: list[str] = PROMPTS,
    completion: str = COMPLETION,
) -> list[tuple[str, float]]:
    """Returns a list of prompts and their perplexities."""
    perplexities = await map_async(
        input_list=prompts,
        fn=partial(completion_perplexity, completion=completion),
        max_concurrency=10,
    )
    return list(zip(prompts, perplexities))

PROMPTS = ["""Answer the question "Experiments are distinct from trial arms or groups; a single experiment might have multiple trial arms, like different interventions or controls. What experiment or experiments (aka trials, RCTs, studies) were conducted in this paper? Enumerate them, being mindful that there may just be one experiment or there could be more than one. Include the name and a brief description of each experiment." based on the excerpt from a research paper. Try to answer, but say "The answer to the question is not mentioned in the excerpt" if you don't know how to answer. Include everything that the paper excerpt has to say about the answer. Make sure everything you say is supported by the excerpt. The excerpt may cite other papers; answer about the paper you're reading the excerpt from, not the papers that it cites. Answer in one phrase or sentence:

Paper excerpt: Lunch breaks constitute the longest within-workday rest period, but it is unclear how they affect recovery from job stress. We conducted two randomized controlled trials with 153 Finnish knowledge workers who engaged for 15 minutes daily in prescribed lunch break activities for ten consecutive working days. Participants were randomly assigned to a: 1) park walking group (N = 51), 2) relaxation exercises group (N = 46) and 3) control group (N = 56). The study was divided into two parts scheduled in spring (N = 83) and fall (N = 70). Recovery experiences (detachment, relaxation, enjoyment) and recovery outcomes (restoration, fatigue, job satisfaction) were assessed with SMS and paper-and-pencil questionnaires several times per day before, during and after the intervention period. A manipulation check revealed that both intervention groups reported less tension after lunch breaks during the intervention than before. In spring, the interventions did hardly affect recovery experiences and outcomes. In fall, restoration increased and fatigue decreased markedly immediately after lunch breaks and in the afternoon in both intervention groups (d = 0.22-0.58) and most consistent positive effects across the day were reported by the park walking group. Park walks and relaxation exercises during lunch breaks can enhance knowledge workers' recovery from work, but effects seem weak, short-lived and dependent on the season.

Question: Experiments are distinct from trial arms or groups; a single experiment might have multiple trial arms, like different interventions or controls. What experiment or experiments (aka trials, RCTs, studies) were conducted in this paper? Enumerate them, being mindful that there may just be one experiment or there could be more than one. Include the name and a brief description of each experiment.

Let's think about each sentence in the excerpt and determine whether it answers the question.

First we'll do some reasoning then we'll write "Answer:" followed by the answer.

Reasoning:"""]

COMPLETION = " The answer to the question is not mentioned in the excerpt"

async def best_generation(
    prompts: list[str] = PROMPTS,
    completion: str = COMPLETION,
) -> tuple[str, float]:
    """Returns the best prompt and its perplexity."""
    perplexities = await map_async(
        input_list=prompts,
        fn=partial(generation_perplexity, completion=completion, max_tokens=384),
        max_concurrency=10,
    )
    return list(zip(prompts, perplexities))


recipe.main(best_generation)
