from functools import partial

from ice.recipe import recipe
from ice.recipes.abstract_qa import Abstract
from ice.recipes.abstract_qa import abstract_qa
from ice.recipes.abstract_qa import DEFAULT_ABSTRACTS
from ice.recipes.combine_abstract_answers import combine_abstract_answers
from ice.recipes.paragraph_synthesis.synthesize import synthesize_from_df
from ice.recipes.paragraph_synthesis.synthesize_ft import synthesize_ft
from ice.utils import map_async


async def synthesize_compositional(question: str, abstracts: list[Abstract]) -> str:
    answers = await map_async(
        abstracts, lambda abstract: abstract_qa(abstract=abstract, question=question)
    )
    answer = await combine_abstract_answers(
        question=question, abstracts=abstracts, answers=answers
    )
    return answer


async def synthesize_compositional_cli() -> str:
    abstracts = DEFAULT_ABSTRACTS
    question = "what is the relationship between income and smoking?"
    answer = await synthesize_compositional(abstracts=abstracts, question=question)
    return answer


recipe.main(synthesize_compositional_cli)

synthesize_compositional_from_df = partial(
    synthesize_from_df, synthesize_fn=synthesize_compositional
)
synthesize_compositional_from_df.__name__ = "synthesize_compositional_from_df"
