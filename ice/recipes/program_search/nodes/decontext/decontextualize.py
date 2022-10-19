from dataclasses import dataclass
from typing import Protocol, Sequence
from ice.paper import Paper, Paragraph

from ice.recipes.program_search.types import Decontext, Selection, sentences
from ice.recipes.program_search.nodes.decontext.prompts import decontext_prompt
from ice.recipe import Recipe, recipe
from itertools import count
from tqdm import tqdm


@dataclass
class Example:
    question: str | None
    texts: list[str]
    decontextualized: list[str]


class Decontextualize(Protocol):
    async def __call__(
        self, question: str | None, texts: list[str], examples: list[Example]
    ) -> list[str]:
        pass


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
        context = " ".join((dec.out for dec in output[-k:]))
        prompt = decontext_prompt(context=context, passage=str(text))
        decontext = await recipe.agent().answer(prompt=prompt)
        output.append(
            Decontext(
                p=text.p, start=text.start, end=text.end, question=None, out=decontext
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
