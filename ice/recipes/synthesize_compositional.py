from transformers import GPT2TokenizerFast

from ice.apis.openai import openai_complete
from ice.recipe import recipe
from ice.recipes.abstract_qa import Abstract
from ice.recipes.abstract_qa import abstract_qa
from ice.recipes.abstract_qa import DEFAULT_ABSTRACTS
from ice.recipes.combine_abstract_answers import combine_abstract_answers
from ice.utils import map_async


def make_gpt2_tokenizer() -> GPT2TokenizerFast:
    return GPT2TokenizerFast.from_pretrained("gpt2")


gpt2_tokenizer = make_gpt2_tokenizer()


def n_tokens(text: str) -> int:
    return len(gpt2_tokenizer.encode(text))


CRITIQUE_PROMPT = """Let's try to improve the answers below using the critiques.

Question: what is the relationship between income and smoking?

Relevant papers:

Paper B1: Association Between Cigarette Smoking Prevalence and Income Level: A Systematic Review and Meta-Analysis
Paper B1 summary: Studies worldwide show a consistent inverse dose-response relationship between cigarette smoking and income level, present among most geographical areas and country characteristics.

Paper B2: Educational inequalities in cause-specific mortality in middle-aged and older men and women in eight western European populations
Paper B2 summary: Income and education are both related to smoking in the EU

Paper B3: Income levels and prevalence of smoking in Latin America
Paper B3 summary: There is an inverse relationship between income and smoking prevalence in studies from Latin America

Paper B4: Is income or employment a stronger predictor of smoking than education in economically less developed countries? A cross-sectional study in Hungary
Paper B4 summary: Education and income are both negatively related to smoking in health surveys in Hungary

Bad answer: Studies worldwide show a consistent inverse dose-response relationship between cigarette smoking and income level, present among most geographical areas and country characteristics (B1). Education is a strong predictor of smoking in Europe (B2). An inverse relationship was observed between income and tobacco-use prevalence in Latin American studies (B3). In Hungary, education and income are both negatively related to smoking (B4).

First let's write a critique of the answer then some reasoning followed by an improved answer based on the critiques. After the improved answer, we'll write "END" on a new line.

Top 3 critiques:
-Does not tie the summaries of papers B1, B2, B3 and B4 together into a single coherent answer.
-List the papers in the order they are given above rather than by topic.
-The sentence are disjointed and do not flow well.

Let's think about how we can improve the answer above using the critiques above.

Reasoning:
Let's try to tie the summaries of papers B1, B2, B3 and B4 together into a narrative that flows well.
The strongest evidence comes from B1 as it states that "Studies worldwide show a consistent inverse dose-response relationship between cigarette smoking and income level, present among most geographical areas and country characteristics." so we should start with that. Let's write "Studies worldwide show a inverse relationship between cigarette smoking and income level (B1)." as our first sentence. Smoking was also inversely related to income in Latin America, EU and Hungary (B3; B2; B4). This is good secondary evidence so let's write "This has been confirmed in studies from Latin America, EU and Hungary (B3; B2; B4)."
Papers B2 and B4 are about education and smoking which is less relevant to the question but still worth mentioning this should us order by topic. Let's write "Education is a strong predictor of smoking in Europe (B2). In Hungary, education and income are both negatively related to smoking (B4)." as our last sentence. Let's write "The other studies (B2; B4) also look at the relationship between education and smoking. They show that education is a strong predictor of smoking in Europe (B2) and Hungary (B4)." These two sentences should create a narrative that flows well.

Improved answer: Studies worldwide show a inverse relationship between cigarette smoking and income level (B1). This has been confirmed in studies from Latin America, EU and Hungary (B3; B2; B4). The other studies (B2; B4) also look at the relationship between education and smoking. They show that education is a strong predictor of smoking in Europe (B2) and Hungary (B4).

END

Question: {question}

Relevant papers:

{relevant_papers_str}

Bad answer: {answer}

First let's write a critique of the answer then some reasoning followed by an improved answer based on the critiques. After the improved answer, we'll write "END" on a new line.

Top 3 critiques:
-Does not tie the summaries of papers B1, B2, B3 and B4 together into a single coherent answer.
-List the papers in the order they are given above rather than by topic.
-The sentence are disjointed and do not flow well.

Let's think about how we can improve the answer above using the critiques above.

Reasoning:"""


def _create_relevant_papers_str(abstracts: list[Abstract], answers: list[str]) -> str:
    return "\n\n".join(
        [
            f"""Paper B{i}: {abstract.title}\nPaper B{i} summary: {answer}"""
            for i, (abstract, answer) in enumerate(zip(abstracts, answers), start=1)
        ]
    )


async def critque_answer(
    question: str, answer: str, abstracts: list[Abstract], answers: list[str]
) -> str:
    prompt = CRITIQUE_PROMPT.format(
        question=question,
        relevant_papers_str=_create_relevant_papers_str(abstracts, answers),
        answer=answer,
    )

    remaining_tokens = 4000 - n_tokens(prompt)
    response = await openai_complete(
        prompt=prompt,
        temperature=0.0,
        max_tokens=remaining_tokens,
        stop=["END"],
        logit_bias={"50256": -100},
    )

    choices = response["choices"]
    text = choices[0]["text"]
    if "Improved answer:" in text:
        text = text.split("Improved answer:")[1].replace("The paper", "One paper")
    return text.strip()


async def synthesize_compositional(abstracts: list[Abstract], question: str) -> str:
    paper_answers = await map_async(
        abstracts, lambda abstract: abstract_qa(abstract=abstract, question=question)
    )
    answer = await combine_abstract_answers(
        question=question,
        abstracts=abstracts,
        answers=paper_answers,
    )

    improved_answer = await critque_answer(question, answer, abstracts, paper_answers)
    return improved_answer


async def synthesize_compositional_cli() -> str:
    abstracts = DEFAULT_ABSTRACTS
    question = "what is the relationship between income and smoking?"
    answer = await synthesize_compositional(abstracts=abstracts, question=question)
    return answer


recipe.main(synthesize_compositional_cli)
