from collections.abc import Sequence
from itertools import count
from typing import Optional

from tqdm import tqdm

from ice.apis.openai import TooLongRequestError
from ice.paper import Paper
from ice.paper import Paragraph
from ice.recipe import Recipe
from ice.recipe import recipe
from ice.recipes.program_search.nodes.decontext.prompts import decontext_prompt
from ice.recipes.program_search.types import Decontext
from ice.recipes.program_search.types import Selection
from ice.recipes.program_search.types import sentences


async def local_decontext(
    texts: Sequence[Selection],
    to_decontext: Selection,
    questions: Optional[Sequence[str]] = None,
) -> Decontext:
    context = " ".join((str(text) for text in texts))
    prompt = decontext_prompt(context, passage=str(to_decontext), questions=questions)
    decontext = await recipe.agent().complete(prompt=prompt, stop="\n\n")
    return Decontext(
        p=to_decontext.p,
        start=to_decontext.start,
        end=to_decontext.end,
        questions=questions,
        out=decontext.strip(),
    )


async def _decontext(context: Sequence[str], passage: str):
    try:
        prompt = decontext_prompt(" ".join(context), passage=passage)
        return await recipe.agent().complete(prompt=prompt, stop="\n\n")
    except TooLongRequestError:
        return await _decontext(context[-(len(context) - 1) :], passage)


async def autoregressive_decontext(
    texts: Sequence[Selection], k: int = 15
) -> Sequence[Decontext]:
    """Decontextualize the (ordered) contexts autoregressively.

    Args:
        texts (Sequence[Selection]): Texts to decontextualize.
        k (int, optional): Number of previous texts to keep in the context. Defaults to 15.

    Returns:
        Sequence[Decontext]: Decontextualized texts
    """
    first = texts[0]
    output: list[Decontext] = [
        Decontext(p=first.p, start=first.start, end=first.end, out=str(first))
    ]

    for text in tqdm(texts[1:]):
        context = [dec.out for dec in output[-k:]]
        decontext = await _decontext(context, str(text))
        output.append(
            Decontext(
                p=text.p,
                start=text.start,
                end=text.end,
                questions=None,
                out=decontext.strip(),
            )
        )
    return output


async def paper_decontext(paper: Paper) -> Paper:
    """Decontextualize the paper by adding explanations in square brackets.

    Args:
        paper (Paper): Paper to decontextualize.

    Returns:
        Paper: Paper with the decontextualized text.
    """
    texts = sentences(paper)
    decontexted = await autoregressive_decontext(texts)
    restructured: list[Paragraph] = []
    counter = count()
    for paragraph in paper.paragraphs:
        new_para: list[str] = []
        for _ in paragraph.sentences:
            new_para.append(decontexted[next(counter)].out)
        restructured.append(
            Paragraph(
                sentences=new_para,
                sections=paragraph.sections,
                sectionType=paragraph.section_type,
            )
        )
    return Paper(paragraphs=restructured, document_id=f"decontext-{paper.document_id}")


class PaperDecontext(Recipe):
    async def run(self, paper: Paper):
        return await paper_decontext(paper)


recipe.main(autoregressive_decontext)
# Meta-Strategies
# Autoregressive
# Holistic tree
# holistic windowed/autoregressive
