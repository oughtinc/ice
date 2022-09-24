from pathlib import Path

from ice.paper import Paper


def test_pdf():
    script_path = Path(__file__).parent
    paper = Paper.load(script_path / "../papers/keenan-2018.pdf")
    sentences = list(paper.sentences())
    assert (
        sentences[0]
        == "We hypothesized that mass distribution of a broad-spectrum antibiotic agent to preschool children would reduce mortality in areas of sub-Saharan Africa that are currently far from meeting the Sustainable Development Goals of the United Nations."
    )
    assert (
        sentences[-1]
        == "Disclosure forms provided by the authors are available with the full text of this article at NEJM.org."
    )


def test_txt():
    script_path = Path(__file__).parent
    paper = Paper.load(script_path / "../papers/keenan-2018-tiny.txt")
    sentences = list(paper.sentences())
    assert (
        sentences[0]
        == "In this cluster-randomized trial, we assigned communities in Malawi, Niger, and Tanzania to four twice-yearly mass distributions of either oral azithromycin (approxi- mately 20 mg per kilogram of body weight) or placebo."
    )
    assert (
        sentences[-1]
        == "The proportion of children whose census status was recorded as moved or unknown did not differ significantly between the groups (P=0.71 and P=0.36, respectively)."
    )
