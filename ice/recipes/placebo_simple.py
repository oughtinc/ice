from ice.recipes.single_prompt import SinglePrompt

QUESTION_SHORT_NAME = "placebo"

DEFAULT_ANSWER_CLASSIFICATION = "Placebo"

AI_PROMPT: str = "\nAssistant:"

HUMAN_PROMPT: str = "\nHuman:"

qa_prompt_template = f"""
{HUMAN_PROMPT} What is a placebo-controlled study?
{AI_PROMPT} A placebo-controlled study is a way of testing a treatment in which a separate control group receives a sham "placebo" treatment which is specifically designed to be indistinguishable from the real treatment but has no real effect.
{HUMAN_PROMPT} Here's the text of a paper I've been thinking about:

{{paper_text}}
{AI_PROMPT} I've read it thoroughly and can answer any question you may have about it.
{HUMAN_PROMPT} Was this a placebo-controlled study? Say "yes", "no", or "unclear".
{AI_PROMPT} Let's think step by step:"""


class PlaceboSimpleInstruct(SinglePrompt):
    agent_str = "instruct"
    max_tokens = 3500
    qa_prompt_template = qa_prompt_template
    question_short_name = QUESTION_SHORT_NAME
    default_answer_classification = DEFAULT_ANSWER_CLASSIFICATION
