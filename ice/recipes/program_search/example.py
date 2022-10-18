from ice.recipe import Recipe
from ice.recipes.program_search.nodes.answer.answer import simple_answer
from ice.recipes.program_search.nodes.decontext.decontextualize import (
    PaperDecontext,
    autoregressive_decontext,
)
from ice.recipes.program_search.nodes.select.select import windowed_select
from ice.paper import Paper
from ice.recipes.experiments_and_arms.golds import get_ea_gs


from ice.recipes.single_prompt import SinglePrompt

QUESTION_SHORT_NAME = "adherence"

DEFAULT_ANSWER_CLASSIFICATION: None = None

AI_PROMPT: str = "\nAssistant:"

HUMAN_PROMPT: str = "\nHuman:"


def baseline(question: str):
    template = f"""
    {HUMAN_PROMPT} I'm trying to evaluate some RCTs. I've been told I should answer the question: "{question}". Can you help me with this?
    {AI_PROMPT} Yes, I can help you with this, if you provide text from the paper in question.
    {HUMAN_PROMPT} Here's the text of the paper I've been thinking about. Can you read it and identify what it says, if anything, to answer the question: "{question}"

    {{paper_text}}
    {AI_PROMPT} First, I'll identify all the parts of the paper that help answer the question. Then, I'll summarize the answer to the question."""

    class InitialSampleSimple(SinglePrompt):
        agent_str = "instruct"
        max_tokens = 3500
        qa_prompt_template: str = template
        question_short_name: str = QUESTION_SHORT_NAME
        default_answer_classification = DEFAULT_ANSWER_CLASSIFICATION

    return InitialSampleSimple


class DecontextAndSelect(Recipe):
    async def run(self, paper: Paper):
        gs = get_ea_gs(paper.document_id)

        # TODO: Actually iterate over all possible choices (this is a hack to get a spread across papers)
        # for which we currently have labeled data

        if not gs or not gs.parsed_answer:
            return
        exps = gs.parsed_answer.experiments[0]
        arm = exps.arms[0]
        if not arm.sample or arm.sample.stage != "randomized":
            return

        question = f"The {exps.name} experiment included {len(exps.arms)} arms: {', '.join((arm.name for arm in exps.arms))}. How many participants were initially allocated to the {arm.name} arm of the {exps.name} experiment?"

        baseline_answer = await (baseline(question)(mode=self.mode).run(paper=paper))

        decontexted = await (PaperDecontext(mode=self.mode).run(paper))

        texts = await windowed_select(
            question=question,
            texts=list(decontexted.sentences()),
            n=5,
            step=2,
        )
        answer = await simple_answer(question, texts)
        gold_answer = arm.sample.size
        return gold_answer, baseline_answer, answer
