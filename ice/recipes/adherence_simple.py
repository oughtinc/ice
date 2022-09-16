from ice.recipes.single_prompt import SinglePrompt

QUESTION_SHORT_NAME = "adherence"

DEFAULT_ANSWER_CLASSIFICATION: None = None

AI_PROMPT: str = "\nAssistant:"

HUMAN_PROMPT: str = "\nHuman:"

qa_prompt_template = f"""
{HUMAN_PROMPT} I'm trying to evaluate some RCTs. I've been told I should consider the adherence, attrition, and compliance of these papers when thinking about how much I should trust their results. Can you define these terms for me?
{AI_PROMPT} Sure, adherence describes how many participants selected for an intervention actually received it. Attrition describes how many of the initial sample dropped out of the study or were otherwise not available to be included in the final analysis. Compliance describes how well participants in the intervention complied with its protocol. All of these are important for the internal validity of a study, which informs how much we should trust its results.
{HUMAN_PROMPT} Here's the text of a paper I've been thinking about. Can you read it and summarize what it says, if anything, about adherence, attrition, and compliance?

{{paper_text}}
{AI_PROMPT} First, I'll identify all the parts of the paper that talk about adherence, attrition, or compliance. Then, I'll summarize these sections."""


class AdherenceSimpleInstruct(SinglePrompt):
    agent_str = "instruct"
    max_tokens = 3500
    qa_prompt_template = qa_prompt_template
    question_short_name = QUESTION_SHORT_NAME
    default_answer_classification = DEFAULT_ANSWER_CLASSIFICATION
