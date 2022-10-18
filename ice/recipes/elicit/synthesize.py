from dataclasses import dataclass

from transformers import GPT2TokenizerFast

from ice.recipe import recipe
import json


@dataclass
class Abstract:
    title: str
    authors: list[str]
    year: int | None
    text: str


DEFAULT_ABSTRACTS = [
    Abstract(
        title="Association Between Cigarette Smoking Prevalence and Income Level: A Systematic Review and Meta-Analysis",
        authors=[
            "Brunilda Casetta",
            "Alejandro J Videla",
            "Ariel Bardach",
            "Paola Morello",
            "Natalie Soto",
            "Kelly Lee",
            "Paul Anthony Camacho",
            "Rocío Victoria Hermoza Moquillaza",
            "Agustín Ciapponi",
        ],
        year=2016,
        text="""Introduction Previous evidence linked low socioeconomic status with higher smoking prevalence. Our objective was to assess the strength of this association in the world population, updating a previous work.
Methods Systematic review and meta-analysis of observational studies. Subgroup analyses included continents, WHO regions, country mortality levels, gender, age, risk of bias, and study publication date. Independent reviewers selected studies, assessed potential bias and extracted data. We searched MEDLINE, EMBASE, CENTRAL, SOCINDEX, AFRICAN INDEX MEDICUS, and LILACS, and other sources from 1989 to 2013 reporting direct measurements of income and current cigarette smoking.
Results We retrieved 13,583 articles and included 93 for meta-analysis. Median smoking prevalence was 17.8% (range 3-70%). Lower income was consistently associated with higher smoking prevalence (odds ratio [OR]: 1.45; 95% confidence interval [CI]: 1.35-1.56). This association was statistically significant in the subgroup analysis by WHO regions for the Americas (OR: 1.54; 95% CI: 1.42-1.68), South East Asia (OR: 1.53; 95% CI: 1.10-2.00), Europe (OR: 1.45; 95% CI: 1.29-1.63), and Western Pacific (OR: 1.32; 95% CI: 1.02-1.72), and in studies conducted during 1990s (OR: 1.42; 95% CI: 1.24-1.62) and 2000s (OR: 1.48; 95%CI: 1.30-1.64). Likewise, it was noted in low-mortality countries (OR: 1.48; 95% CI: 1.37-1.60) and for both genders. Prevalence was highest in the lowest income levels compared to the middle (OR: 1.69; 95% CI: 1.49-1.92), followed by the middle level compared to the highest (OR: 1.31; 95% CI: 1.20-1.43).
Conclusions Our results show that current cigarette smoking was significantly associated with lower income worldwide and across subgroups, suggesting a dose-response relationship.
Implications This unique updated systematic review shows a consistent inverse dose-response relationship between cigarette smoking and income level, present among most geographical areas and country characteristics. Public health measures should take into account this potential inequity and consider special efforts directed to disadvantaged populations.""",
    ),
    Abstract(
        title="Educational inequalities in cause-specific mortality in middle-aged and older men and women in eight western European populations",
        authors=[
            "Martijn Huisman",
            "Anton E Kunst",
            "Matthias Bopp",
            "Jens-Kristian Borgan",
            "Carme Borrell",
            "Giuseppe Costa",
            "Patrick Deboosere",
            "Sylvie Gadeyne",
            "Myer Glickman",
            "Chiara Marinacci",
            "Christoph Minder",
            "Enrique Regidor",
            "Tapani Valkonen",
            "Johan P Mackenbach",
        ],
        year=2005,
        text="""BACKGROUND The aim of the study was to determine whether education or income was more strongly related to smoking in the European Union at large, and within the individual countries of the EU, at the end of the 1990s.
METHODS We related smoking prevalence to education and income level by analyzing cross-sectional data on a total of 48,694 men and 52,618 women aged 16 and over from 11 countries of the European Union in 1998.
RESULTS Both education and income were related to smoking within the European Union at large. After adjustment of the other socioeconomic indicator, education remained related to smoking in the EU at large, but income only remained so among men. Educational inequalities were larger than income-related inequalities among younger and middle-aged men and women. Educational inequalities were larger than income-related inequalities among men in all individual countries, and among women in Northern Europe. For women from Southern European countries, the magnitude of education- and income-related inequalities was similar.
CONCLUSIONS Education is a strong predictor of smoking in Europe. Interventions should aim to prevent addiction to smoking among the lower educated, by price policies, school-based programs, and smoking cessation support for young adults.""",
    ),
    Abstract(
        title="Income levels and prevalence of smoking in Latin America",
        authors=[
            "Ariel Bardach",
            "Herney Andrés García Perdomo",
            "Ruth Amanda Ruano Gándara",
            "Agustín Ciapponi",
        ],
        year=2016,
        text="""Objective Determine the relationship between tobacco-use prevalence and smoker income level in Latin America and the Caribbean (LAC).
Methods A systematic search was carried out in MEDLINE, EMBASE, CENTRAL, SOCINDEX, and LILACS databases. Studies from LAC published from January 1989 to December 2015 were included and were analyzed by subgroups disaggregated by decade of data, country, bias risk, sex, and age group.
Results Of 1 254 studies evaluated by full text, 29 articles were included, of which 25 were chosen for meta-analysis. All included studies were cross-sectional or surveillance, primarily from Brazil and Mexico.Low income was associated with higher prevalence of active smoking (odds ratio [OR] 1.62; 95% confidence interval [95%CI] 1.34-1.96) than high income (reference). A dose-response effect trend was observed: middle income (OR 1.23; 95%CI 1.00-1.52) and low income (OR 1.64; 95%CI 1.17-2.30). This association was greater in men (OR 2.22; 95%CI 1.77-2.78) than in women (OR 1.6; 95%CI 1.11-2.47).
Conclusions An inverse relationship was observed between income and tobacco-use prevalence. Further efforts are required to determine this relationship in special populations, such as adolescents and pregnant women. This research can be useful for policymakers by improving tobacco control strategies and for characterizing public health equity issues.""",
    ),
    Abstract(
        title="Is income or employment a stronger predictor of smoking than education in economically less developed countries? A cross-sectional study in Hungary",
        authors=["Mall Leinsalu", "Csilla Kaposvári", "Anton E Kunst"],
        year=2011,
        text="""BackgroundIn developed European countries in the last phase of the smoking epidemic, education is a stronger predictor of smoking than income or employment. We examine whether this also applies in economically less developed countries.MethodsData from 7218 respondents in the 25-64 age group came from two National Health Interview Surveys conducted in 2000 and 2003 in Hungary. Independent effects of educational level, income and employment status were studied in relation to smoking prevalence, initiation and continuation for all age groups combined and separately for 25-34, 35-49 and 50-64 years old. Absolute levels were evaluated by using age-standardized prevalence rates. Relative differences were assessed by means of logistic regression.ResultsEducation and income, but not employment, were associated with equally large differences in smoking prevalence in Hungary in the 25-64 age group. Among men, smoking initiation was related to low educational level, whereas smoking continuation was related to low income. Among women, low education and low income were associated with both high initiation and high continuation rates. Considerable differences were found between the age groups. Inverse social gradients were generally strongest in the youngest age groups. However, smoking continuation among men had the strongest association with low income for the middle-aged group.ConclusionsPatterns of inequalities in smoking in Hungary can be best understood in relation to two processes: the smoking epidemic, and the additional effects of poverty. Equity orientated tobacco control measures should target the low educated to prevent their smoking initiation, and the poor to improve their cessation rates.""",
    ),
]


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


def _get_reference(authors: list[str], year: int | None) -> str:
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

async def synthesize_from_df(
    question,
    papers,
    **kwargs
):
    return await synthesize(question, [Abstract(
        title=paper["title"],
        authors=paper["authors"],
        year=paper["year"],
        text=paper["abstract"],
    ) for paper in json.loads(papers)])


async def synthesize_test():
    question = "what is the relationship between income and smoking?"
    abstracts = DEFAULT_ABSTRACTS
    gold_standard = "All four papers found that lower income is associated with higher smoking prevalence (Brunilda Casetta et al., 2016; M Huisman et al., 2005; Ariel Esteban Bardach et al., 2016; Mall Leinsalu et al., 2011). Two papers found that less education is also associated with higher smoking prevalence (M Huisman et al., 2005; Mall Leinsalu et al., 2011)."
    print(f"\nGold standard: {gold_standard}\n")
    return await synthesize(question, abstracts)


recipe.main(synthesize_test)
