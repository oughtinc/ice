import asyncio
import random

import defopt
import nest_asyncio
import rich

from rich.markdown import Markdown
from rich.pretty import pprint
from tqdm import tqdm

from ice.cli_utils import select_recipe_class
from ice.metrics.gold_paragraphs import get_gold_paragraph_df
from ice.mode import Mode
from ice.utils import quoted


async def main(
    *,
    mode: Mode = "augmented-cached",
    question_short_name: str,
    recipe_name: str,
    random_seed: int | None = None,
    method_name: str = "analyze_paragraph",
):
    recipe_class = await select_recipe_class(recipe_name=recipe_name)
    paragraph_df, id_to_paragraph = get_gold_paragraph_df(question_short_name)

    recipe = recipe_class(mode=mode)

    paragraph_results = []

    rows = list(paragraph_df.iterrows())

    if random_seed is not None:
        random.seed(random_seed)
        random.shuffle(rows)

    for row_index, row in tqdm(rows):
        paragraph_id = row["paragraph_id"]
        paragraph = id_to_paragraph[paragraph_id]
        experiment = row["experiment"]
        rich.print(
            Markdown(
                f"""
### Paragraph {paragraph_id}

Gold standard quote:

{quoted(row["quote"])}

Gold standard paper-level classification:

{quoted(row["paper_gold_classification"])}

Gold standard paper-level answer:

{quoted(row["paper_gold_answer"])}"""
            )
        )
        method = getattr(recipe, method_name)
        paragraph_result = asyncio.run(
            method(
                paragraph=paragraph,
                experiment=experiment,
            )
        )
        paragraph_results.append(paragraph_result)

    pprint(paragraph_results)


def main_cli(
    *,
    mode: Mode = "augmented-cached",
    question_short_name: str = "placebo",
    recipe_name: str = "placebo",
    random_seed: int | None = None,
    method_name: str = "analyze_paragraph",
):
    """

    ::

    Run a recipe method over gold standard paragraphs.

    :param mode Mode:
    :param question_short_name: Used to look up gold standards (e.g. "placebo")
    :param recipe_name: Name of the recipe to run. Needs to have a analyze_paragraph method.
    :param random_seed: If provided, paragraphs will be shuffled randomly with this seed.
    :param method_name: Name of the paragraph-level recipe method to run.

    """
    nest_asyncio.apply()
    asyncio.run(
        main(
            mode=mode,
            question_short_name=question_short_name,
            recipe_name=recipe_name,
            random_seed=random_seed,
            method_name=method_name,
        )
    )


if __name__ == "__main__":
    defopt.run(main_cli)
