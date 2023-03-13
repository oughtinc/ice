from typing import Optional

from transformers import GPT2TokenizerFast

from ice.recipe import recipe
from ice.recipes.abstract_qa import Abstract
from ice.recipes.abstract_qa import DEFAULT_ABSTRACTS


def make_gpt2_tokenizer() -> GPT2TokenizerFast:
    return GPT2TokenizerFast.from_pretrained("gpt2")


gpt2_tokenizer = make_gpt2_tokenizer()


def num_tokens(text: str) -> int:
    """
    Return how many tokens are in 'text'.
    """
    return len(gpt2_tokenizer.tokenize(text))


PREFIX = """In this section, we will demonstrate how to write an ideal answer for a question using academic literature. When answering questions using academic literature you MUST use references.
An ideal answer gives references to the academic literature. Example: "To our knowledge, the only freely and publicly available dense autoregressive language models larger than GPT2 are GPT-Neo (Black et al., 2021), GPT-J-6B (Wang and Komatsuzaki, 2021), Megatron-11B, Pangu-13B (Zeng et al., 2021), and the recently released FairSeq models (Artetxe et al., 2021)."
Let's look at some example questions."""

MAX_TOKENS = 4001

MIN_COMPLETION_TOKENS = 250

SHOTS = [
    """Question: "How does l-theanine affect anxiety?"

Here are the relevant papers, and excerpts from those papers:

Paper: Effects of l-theanine on anxiety-like behavior, cerebrospinal fluid amino acid profile, and hippocampal activity in Wistar Kyoto rats
Reference: Ogawa et al. (2017)
Excerpt: Rationale and objectives In the present study, we examined the effects of repeated l-theanine administration on behavior, levels of amino acids in the cerebrospinal fluid (CSF), and hippocampal activity in Wistar Kyoto (WKY) rats, an animal model of anxiety and depressive disorders.MethodsBehavioral tests were performed after 7–10 days of l-theanine (0.4 mg kg−1 day−1) or saline administration, followed by CSF sampling for high-performance liquid chromatography (HPLC) analysis. An independent set of animals was subjected to [18F]fluorodeoxyglucose positron emission tomography (PET) scanning after the same dose of l-theanine or saline administration for 7 days.ResultsIn the elevated plus maze test, the time spent in the open arms was significantly longer in the l-theanine group than in the saline group (P = 0.035). In addition, significantly lower CSF glutamate (P = 0.039) and higher methionine (P = 0.024) concentrations were observed in the l-theanine group than in the saline group. A significant increase in the standard uptake value ratio was observed in the hippocampus/cerebellum of the l-theanine group (P < 0.001). ConclusionsThese results suggest that l-theanine enhances hippocampal activity and exerts anxiolytic effects, which may be mediated by changes in glutamate and methionine levels in the brain.

Paper: L-theanine—a unique amino acid of green tea and its relaxation effect in humans
Reference: Raj Juneja et al. (1999)
Excerpt: It was found that L-theanine administered intraperitoneally to rats reached the brain within 30 min without any metabolic change. Theanine also acts as a neurotransmitter in the brain and decreased blood pressure significantly in hypertensive rats. In general, animals always generate very weak electric pulses on the surface of the brain, called brain waves. Brain waves are classified into four types, namely α,β,δ and θ-waves, based on mental conditions. Generation of α-waves is considered to be an index of relaxation. In human volunteers, α-waves were generated on the occipital and parietal regions of the brain surface within 40 min after the oral administration of theanine (50–200 mg), signifying relaxation without causing drowsiness.

Paper: The acute effects of L-theanine in comparison with alprazolam on anticipatory anxiety in humans
Reference: Lu et al. (2004)
Excerpt: Sixteen healthy volunteers received alprazolam (1 mg), L‐theanine (200 mg) or placebo in a double‐blind placebo‐controlled repeated measures design. The acute effects of alprazolam and L‐theanine were assessed under a relaxed and experimentally induced anxiety condition. Subjective self‐reports of anxiety including BAI, VAMS, STAI state anxiety, were obtained during both task conditions at pre‐ and post‐drug administrations. The results showed some evidence for relaxing effects of L‐theanine during the baseline condition on the tranquil–troubled subscale of the VAMS. Alprazolam did not exert any anxiolytic effects in comparison with the placebo on any of the measures during the relaxed state. Neither L‐theanine nor alprazalam had any significant anxiolytic effects during the experimentally induced anxiety state. The findings suggest that while L‐theanine may have some relaxing effects under resting conditions, neither L‐theanine not alprazolam demonstrate any acute anxiolytic effects under conditions of increased anxiety in the AA model.

Ideal answer to the question "How does l-theanine affect anxiety?" based on the papers above using references: Two of the three papers indicate that l-theanine reduces anxiety in animals (Ogawa et al., 2017) and humans (Kimura et al., 2007), while one study indicates that l-theanine may not be effective for anxiety (Lu et al., 2004).""",
    """Question: "How many emotions are there?"

Here are the relevant papers, and excerpts from those papers:

Paper: How Many Emotions Are There? Wedding the Social and the Autonomic Components
Reference: Kemper (1987)
Excerpt: Fundamental in the field of emotions is the question of how many emotion there are or there can be. The answer proposed here is that the number of possible emotions is limites. As long as society differentiates new social situations, labels them, and socializes individuals to experience them, new emotions will continue to emerge. But this view must be qualified by an understanding of the autonomic constraints that limit variability in the experience of emotions. It is argued here that there are four psychologically grounded primary emotions: fear, anger, depression, and satisfaction. They are evolutionarily important, cross-culturally universal, ontogenetically early to emerge, and link empirically with important outcomes of social relations. Secondary emotions, such as guilt, shame, pride, gratitude, love, nostalgia, ennui, and so forth, are acquired through socializing agents who define and label such emotions while the individual is experiencing the autonomic reactions of one of the "primaries." Hence, it is argued here, guilt is a socialized response to arousal of the physiological conditions of fear; shame to those of anger; pride to those of satisfaction; and so on.

Paper: Neuropsychology: How Many Emotions Are There?
Reference: Dubois and Adolphs (2015)
Excerpt: Psychological theories disagree on how we attribute emotions to people. A new neuroimaging study shows that such attributions involve a large number of abstract features, rather than a small set of emotion categories.

Paper: Evidence for a three-factor theory of emotions
Reference: Russel and Mehrabian (1977)
Excerpt: Abstract Two studies provided evidence that three independent and bipolar dimensions, pleasure-displeasure, degree of arousal, and dominance-submissiveness, are both necessary and sufficient to adequately define emotional states. In one study with 200 subjects, 42 verbal-report emotion scales were explored in regression analyses as functions of the three dimensions plus a measure of acquiescence bias. Multiple correlation coefficients showed that almost all of the reliable variance in the 42 scales had been accounted for. The specific definitions provided by these equations were replicated in a second study that employed 300 subjects' ratings of 151 emotion-denoting terms on semantic differential-type scales.

Paper: Patterns of cognitive appraisal in emotion.
Reference: Smith and Ellsworth (1985)
Excerpt: There has long been interest in describing emotional experience in terms of underlying dimensions, but traditionally only two dimensions, pleasantness and arousal, have been reliably found. The reasons for these findings are reviewed, and integrating this review with two recent theories of emotions (Roseman, 1984; Scherer, 1982), we propose eight cognitive appraisal dimensions to differentiate emotional experience. In an investigation of this model, subjects recalled past experiences associated with each of 15 emotions, and rated them along the proposed dimensions. Six orthogonal dimensions, pleasantness, anticipated effort, certainty, attentional activity, self-other responsibility/control, and situational control, were recovered, and the emotions varied systematically along each of these dimensions, indicating a strong relation between the appraisal of one's circumstances and one's emotional state.

Ideal answer to the question "How many emotions are there?" based on the papers above using references: One paper claims that there are four emotions (Kemper, 1987), while the others claim that there are three dimensions of emotions (Russel & Mehrabian, 1977), six dimensions of emotions (Smith & Ellsworth, 1985), or that the notion of emotion categories doesn't make sense at all (Dubois & Adolphs, 2015).""",
]

PROMPT_FORMAT = """Question: "{question}"

Here are the relevant papers, and excerpts from those papers:

{papers_str}

Ideal answer to the question "{question}" based on the papers above using references:"""

PAPER_FORMAT = """Paper: {title}
Reference: {reference}
Excerpt: {abstract}"""


def _get_reference(authors: list[str], year: Optional[int]) -> str:
    if len(authors) == 0:
        return f"({year})"
    if len(authors) == 1:
        return f"{authors[0]} ({year})"
    elif len(authors) == 2:
        return f"{authors[0]} and {authors[1]} ({year})"
    else:
        return f"{authors[0]} et al. ({year})"


async def synthesize(question: str, abstracts: list[Abstract]) -> str:
    papers_str = "\n\n".join(
        [
            PAPER_FORMAT.format(
                title=abstract.title,
                reference=_get_reference(abstract.authors, abstract.year),
                abstract=abstract.text,
            )
            for abstract in abstracts
        ]
    )

    suffix = PROMPT_FORMAT.format(
        question=question,
        papers_str=papers_str,
    )

    sep = "\n\n###\n\n"

    prompt = PREFIX + sep + sep.join(SHOTS) + sep + suffix
    number_of_shots = len(SHOTS)
    while (
        num_tokens(prompt) > MAX_TOKENS - MIN_COMPLETION_TOKENS and number_of_shots > 0
    ):
        number_of_shots -= 1
        prompt = PREFIX + sep + sep.join(SHOTS[:number_of_shots]) + sep + suffix

    remaining_tokens = MAX_TOKENS - num_tokens(prompt)

    completion = await recipe.agent().complete(
        prompt=prompt, max_tokens=remaining_tokens, stop="<|endoftext|>"
    )

    return completion


async def synthesize_cli():
    question = "what is the relationship between income and smoking?"
    abstracts = DEFAULT_ABSTRACTS
    gold_standard = "All four papers found that lower income is associated with higher smoking prevalence (Brunilda Casetta et al., 2016; M Huisman et al., 2005; Ariel Esteban Bardach et al., 2016; Mall Leinsalu et al., 2011). Two papers found that less education is also associated with higher smoking prevalence (M Huisman et al., 2005; Mall Leinsalu et al., 2011)."
    print(f"\nGold standard: {gold_standard}\n")
    return await synthesize(question, abstracts)


recipe.main(synthesize_cli)
