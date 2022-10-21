from functools import partial

import transformers

from ice.recipe import recipe
from ice.recipes.synthesize import _get_reference
from ice.recipes.synthesize import Abstract
from ice.recipes.synthesize import num_tokens
from ice.recipes.synthesize import synthesize_from_df
from ice.recipes.synthesize_ft import n_tokens

PROMPT = """An ideal answer gives references to the academic literature. Example: "To our knowledge, the only freely and publicly available dense autoregressive language models larger than GPT2 are GPT-Neo (Black et al., 2021), GPT-J-6B (Wang and Komatsuzaki, 2021), Megatron-11B, Pangu-13B (Zeng et al., 2021), and the recently released FairSeq models (Artetxe et al., 2021)."

Let's look at some example questions.

Take the question: "How many emotions are there?"

Here are a few relevant papers, and excerpts from those papers:

Paper: How Many Emotions Are There? Wedding the Social and the Autonomic Components
Reference: Kemper (1987)
Excerpt: Fundamental in the field of emotions is the question of how many emotion there are or there can be. The answer proposed here is that the number of possible emotions is limites. As long as society differentiates new social situations, labels them, and socializes individuals to experience them, new emotions will continue to emerge. But this view must be qualified by an understanding of the autonomic constraints that limit variability in the experience of emotions. It is argued here that there are four psychologically grounded primary emotions: fear, anger, depression, and satisfaction. They are evolutionarily important, cross-culturally universal, ontogenetically early to emerge, and link empirically with important outcomes of social relations. Secondary emotions, such as guilt, shame, pride, gratitude, love, nostalgia, ennui, and so forth, are acquired through socializing agents who define and label such emotions while the individual is experiencing the autonomic reactions of one of the "primaries." Hence, it is argued here, guilt is a socialized response to arousal of the physiological conditions of fear; shame to those of anger; pride to those of satisfaction; and so on. This integration of primary with secondary emotions incorporates the contributions of both positivist and social constructionist positions in the sociology of emotions.

Paper: Neuropsychology: How Many Emotions Are There?
Reference: Dubois and Adolphs (2015)
Excerpt: Psychological theories disagree on how we attribute emotions to people. A new neuroimaging study shows that such attributions involve a large number of abstract features, rather than a small set of emotion categories.

Paper: Evidence for a three-factor theory of emotions
Reference: Russel and Mehrabian (1977)
Excerpt: Abstract Two studies provided evidence that three independent and bipolar dimensions, pleasure-displeasure, degree of arousal, and dominance-submissiveness, are both necessary and sufficient to adequately define emotional states. In one study with 200 subjects, 42 verbal-report emotion scales were explored in regression analyses as functions of the three dimensions plus a measure of acquiescence bias. Multiple correlation coefficients showed that almost all of the reliable variance in the 42 scales had been accounted for. The specific definitions provided by these equations were replicated in a second study that employed 300 subjects' ratings of 151 emotion-denoting terms on semantic differential-type scales.

Paper: Patterns of cognitive appraisal in emotion.
Reference: Smith and Ellsworth (1985)
Excerpt: There has long been interest in describing emotional experience in terms of underlying dimensions, but traditionally only two dimensions, pleasantness and arousal, have been reliably found. The reasons for these findings are reviewed, and integrating this review with two recent theories of emotions (Roseman, 1984; Scherer, 1982), we propose eight cognitive appraisal dimensions to differentiate emotional experience. In an investigation of this model, subjects recalled past experiences associated with each of 15 emotions, and rated them along the proposed dimensions. Six orthogonal dimensions, pleasantness, anticipated effort, certainty, attentional activity, self-other responsibility/control, and situational control, were recovered, and the emotions varied systematically along each of these dimensions, indicating a strong relation between the appraisal of one's circumstances and one's emotional state. The patterns of appraisal for the different emotions, and the role of each of the dimensions in differentiating emotional experience are discussed.

Let's think about how each paper answers the overall question: Kemper (1987) claims that there are four psychologically grounded emotions, a range of secondary emotions, and that overall the number of emotions is limited by autonomic constraints. This directly answers the question of "How many emotions are there?" Dubois and Adolphs (2015) reject the notion of emotion categories, and show that attributing emotions involves a large number of abstract features. This does not directly answer the question. Russel and Mehrabian (1977) suggest that there are three dimensions that contribute to the variance in the different emotional scales. This doesn't directly answer the question, but is still relevant information, since it describes the number of dimensions. Smith and Ellsworth (1985) discuss 15 different emotions that break down along six dimensions, but do not claim that there are only 15 emotions. This also doesn't directly answer the question, but is relevant information since it doescribes the number of emotions.

Now let's answer the question: "How many emotions are there?"

Overall, one paper claims that there are four emotions (Kemper, 1987), while the others claim that there are three dimensions of emotions (Russel & Mehrabian, 1977), six dimensions of emotions (Smith & Ellsworth, 1985), or that the notion of emotion categories doesn't make sense at all (Dubois & Adolphs, 2015). END"""

EXTRA_SHOT = """Take the question: "How does l-theanine affect anxiety?"

Here are the relevant papers, and excerpts from those papers:

Paper: Effects of l-theanine on anxiety-like behavior, cerebrospinal fluid amino acid profile, and hippocampal activity in Wistar Kyoto rats
Reference: Ogawa et al. (2017)
Excerpt: Rationale and objectivesThe amino acid l-theanine (N-ethyl-l-glutamine) has historically been considered a relaxing agent. In the present study, we examined the effects of repeated l-theanine administration on behavior, levels of amino acids in the cerebrospinal fluid (CSF), and hippocampal activity in Wistar Kyoto (WKY) rats, an animal model of anxiety and depressive disorders.MethodsBehavioral tests were performed after 7–10 days of l-theanine (0.4 mg kg−1 day−1) or saline administration, followed by CSF sampling for high-performance liquid chromatography (HPLC) analysis. An independent set of animals was subjected to [18F]fluorodeoxyglucose positron emission tomography (PET) scanning after the same dose of l-theanine or saline administration for 7 days.ResultsIn the elevated plus maze test, the time spent in the open arms was significantly longer in the l-theanine group than in the saline group (P = 0.035). In addition, significantly lower CSF glutamate (P = 0.039) and higher methionine (P = 0.024) concentrations were observed in the l-theanine group than in the saline group. A significant increase in the standard uptake value ratio was observed in the hippocampus/cerebellum of the l-theanine group (P < 0.001). ConclusionsThese results suggest that l-theanine enhances hippocampal activity and exerts anxiolytic effects, which may be mediated by changes in glutamate and methionine levels in the brain. Further study is required to more fully elucidate the mechanisms underlying the effects of l-theanine.

Paper: L-theanine—a unique amino acid of green tea and its relaxation effect in humans
Reference: Raj Juneja et al. (1999)
Excerpt: Since ancient times, it has been said that drinking green tea brings relaxation. The substance that is responsible for a sense of relaxation, is theanine. Theanine is a unique amino acid found almost solely in tea plants and the main component responsible for the exotic taste of ‘green’ tea. It was found that L-theanine administered intraperitoneally to rats reached the brain within 30 min without any metabolic change. Theanine also acts as a neurotransmitter in the brain and decreased blood pressure significantly in hypertensive rats. In general, animals always generate very weak electric pulses on the surface of the brain, called brain waves. Brain waves are classified into four types, namely α,β,δ and θ-waves, based on mental conditions. Generation of α-waves is considered to be an index of relaxation. In human volunteers, α-waves were generated on the occipital and parietal regions of the brain surface within 40 min after the oral administration of theanine (50–200 mg), signifying relaxation without causing drowsiness. With the successful industrial production of L-theanine, we are now able to supply Suntheanine™ (trade name of L-theanine) which offers a tremendous opportunity for designing foods and medical foods targeting relaxation and the reduction of stress. Taiyo Kagaku Co., Ltd, Japan won the 1998 ‘Food Ingredient Research Award’ for development of Suntheanine™ at Food Ingredients in Europe (Frankfurt). The judges felt it was a particularly well-documented and fascinating piece of research.

Paper: The acute effects of L‐theanine in comparison with alprazolam on anticipatory anxiety in humans
Reference: Lu et al. (2004)
Excerpt: L‐Theanine (δ‐glutamylethylamide) is one of the predominant amino acids ordinarily found in green tea, and historically has been used as a relaxing agent. The current study examined the acute effects of L‐theanine in comparison with a standard benzodiazepine anxiolytic, alprazolam and placebo on behavioural measures of anxiety in healthy human subjects using the model of anticipatory anxiety (AA). Sixteen healthy volunteers received alprazolam (1 mg), L‐theanine (200 mg) or placebo in a double‐blind placebo‐controlled repeated measures design. The acute effects of alprazolam and L‐theanine were assessed under a relaxed and experimentally induced anxiety condition. Subjective self‐reports of anxiety including BAI, VAMS, STAI state anxiety, were obtained during both task conditions at pre‐ and post‐drug administrations. The results showed some evidence for relaxing effects of L‐theanine during the baseline condition on the tranquil–troubled subscale of the VAMS. Alprazolam did not exert any anxiolytic effects in comparison with the placebo on any of the measures during the relaxed state. Neither L‐theanine nor alprazalam had any significant anxiolytic effects during the experimentally induced anxiety state. The findings suggest that while L‐theanine may have some relaxing effects under resting conditions, neither L‐theanine not alprazolam demonstrate any acute anxiolytic effects under conditions of increased anxiety in the AA model. Copyright © 2004 John Wiley & Sons, Ltd.

Let's think about how each paper answers the overall question: Ogawa et al. (2017) found that l-theanine exerts anxiolytic effects in an independent set of animals, which suggests that l-theanine is effective for anxiety. Raj Juneja et al. (1999) review the evidence for l-theanine. They find that oral administration of l-theanine in humans led to α-waves (indicative of relaxation), which also suggests that l-theanine is effective for anxiety. Lu et al. (2004) found that while l-theanine may have relaxing effects under resting conditions, it did not demonstrate acute acute anxiolytic effects under anxious conditions, which suggests the opposite conclusion that l-theanine may not be effective for anxiety.

Now let's answer the question: "How does l-theanine affect anxiety?"

Overall, the evidence points to l-theanine being effective for anxiety. Two of the three papers indicate that l-theanine reduces anxiety in animals (Ogawa et al., 2017) and humans (Kimura et al., 2007), while only one study indicates that l-theanine may not be effective for anxiety (Lu et al., 2004). END"""

PAPER_FORMAT = """Paper: {title}
Reference: {citation}
Excerpt: {abstract}"""

PREFIX = """Take the question: "{question}"

Here are the relevant papers, and excerpts from those papers:\n\n"""

SUFFIX = "\n\nLet's think about how each paper answers the overall question:"


def _get_prompt(question, titles, citations, abstracts):
    paper_prompt = (
        PREFIX.format(question=question)
        + "\n\n".join(
            PAPER_FORMAT.format(title=title, citation=citation, abstract=abstract)
            for title, citation, abstract in zip(titles, citations, abstracts)
        )
        + SUFFIX
    )
    prompt = PREFIX + "\n\n" + EXTRA_SHOT + "\n\n" + paper_prompt
    if n_tokens(prompt) > 3700:  # 300 tokens for the completion
        prompt = PREFIX + "\n\n" + paper_prompt
    return prompt, 4000 - n_tokens(prompt)


async def synthesize_chain_of_thought(question: str, abstracts: list[Abstract]) -> str:
    prompt, max_tokens = _get_prompt(
        question=question,
        titles=[abstract.title for abstract in abstracts],
        abstracts=[abstract.text for abstract in abstracts],
        citations=[
            _get_reference(abstract.authors, abstract.year) for abstract in abstracts
        ],
    )

    completion = await recipe.agent().complete(
        prompt=prompt,
        max_tokens=max_tokens,
        logit_bias={"50256": -100},
        stop=["END"],
    )

    return completion


synthesize_chain_of_thought_from_df = partial(
    synthesize_from_df, synthesize_fn=synthesize_chain_of_thought
)
synthesize_chain_of_thought_from_df.__name__ = "synthesize_chain_of_thought_from_df"
