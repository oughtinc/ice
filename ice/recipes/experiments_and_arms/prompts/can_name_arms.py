from collections.abc import Callable
from collections.abc import Sequence
from typing import Optional
from typing import Union

from ice.formatter.multi import format_multi
from ice.formatter.transform.dependent import CountWord
from ice.formatter.transform.dependent import plural_transform
from ice.formatter.transform.positional import OrdinalWord
from ice.formatter.transform.value import numbered_list
from ice.formatter.transform.value import ValueTransform
from ice.recipes.experiments_and_arms.prompts.utils import get_part
from ice.recipes.experiments_and_arms.prompts.utils import start_last_example
from ice.recipes.experiments_and_arms.types import MultipartReasoningPrompt


CAN_WE_NAME_ARMS_EXAMPLES: list[
    dict[str, Union[ValueTransform[Sequence[str]], str, int]]
] = [
    dict(
        paragraphs=numbered_list(
            [
                """As described above, prior research largely has focused on the types of threats to validity. Few explicit recommendations exist for quality control procedures (e.g., assertions of goldstandard approaches), and little is known about how specific quality assurance approaches affect study outcomes. Therefore, given the literature indicating the need to manage VPNs/bots, misrepresentation, and inattention, we conducted a randomized, controlled experiment with four study arms (Control Arm, Bot/VPN Arm, Truth/Attention Arm, and Stringent Arm). The purpose of the study was to determine the absolute numeric difference, as well as differences in magnitude, skewness, and standard deviation, of different quality control procedures on outcomes from three self-administered digital tools used in a cross section of fields focused on mental health and substance use: the U.S. Alcohol Use Disorder Identification Test (USAUDIT) (Higgins-Biddle & Babor, 2018), the Patient Health Questionnaire (PHQ-9) (Kroenke et al., 2001), and the screener for Generalized Anxiety Disorder (GAD-7) (Spitzer et al., 2006).""",
                """These instruments (or similar, such as the AUDIT-C) have been used in recent crowdsourced studies on MTurk to explore a variety of important topics, such as associations between loneliness, depression, and COVID-19 (Killgore et al., 2020), relationships between sleep debt and anxiety (Dickinson et al., 2018), temporal relationships between day-level cravings and alcohol use (Jain et al., 2021), and the efficacy of Internet interventions for unhealthy alcohol use (Cunningham et al., 2019). At the same time, clinical studies have noted differences in self-reported prevalence of depression and anxiety between adult MTurk samples and other data sources, such as adult community samples or undergraduate research samples. Often, but not always, anxiety and depression have appeared to be more prevalent in samples from MTurk, and researchers have encouraged exploration of why this might be the case (Arditte et al., 2016;van Stolk-Cooke et al., 2018;Ophir et al., 2019;Engle et al., 2020). In response to this need, our methodological research provides the rapidly growing number of scholars using crowdsourced sampling with objective data indicating the expected impact and utility of multiple different quality-control procedures on crowdsourced data assessing depression, anxiety, and risky alcohol use.""",
                """We proposed two exploratory, preregistered hypotheses .""",
                """(1) Outcome scores from each of the three screening tools would be significantly different for each pairwise comparison of study arms, except for the pairing (Bot/VPN with Truth/Attention). We expected that each additional form of quality control would affect outcomes on all screening tools, except that we were agnostic as to whether there would be a meaningful difference between the different types of quality control (e.g., that the Bot/VPN control and the Truth/Attention control would produce differential effects). Thus, our hypotheses were based on the stringency of control mechanics by frequency count (e.g., 0, 1, 1, or 2 approaches within the arm), and we expected differences between each pair except the 1:1 pairing.""",
            ]
        ),
        reasoning="\n\n".join(
            [
                "Excerpt 1 says that there were four arms and describes them: Control, Bot/VPN, Truth/Attention, and Stringent.",
                "Excerpt 2 provides background information but does not discuss arms.",
                "Excerpt 3 says that there were two preregistered hypotheses for the study",
                "Excerpt 4 discusses the first of these preregistered hypotheses and alludes to some of the aforementioned arms (Bot/VPN and Truth/Attention)",
            ]
        ),
        helpfulness="Excerpt 1 was extremely helpful; excerpts 2, 3, and 4 were not helpful.",
        experiments=numbered_list(
            [
                "An experiment to test whether quality control on MTurk affects outcomes relevant to psychological/behavioral research"
            ]
        ),
        experiment_in_question="An experiment to test whether quality control on MTurk affects outcomes relevant to psychological/behavioral research",
        answer="Yes",
    ),
    dict(
        paragraphs=numbered_list(
            [
                """To measure the effect of an electronic health record (EHR) alert on chronic hepatitis B (CHB) screening among at-risk Asian and Pacific Islanders (API). API patients who had not yet completed hepatitis B surface antigen (HBsAg) testing were identified by a novel EHR-based population health tool. At-risk API patients in Cohort 1 (primarily privately insured) and Cohort 2 (includes Medicare and/or Medicaid) were randomized to alert activation in their electronic medical charts or not. In total, 8299 API were found to be deficient in HBsAg completion at baseline within our health system. In Cohort 1, 1542 patients and 1568 patients were randomized to the alert and control respectively. In Cohort 2, 2599 patients and 2590 patients were randomized to the alert and control respectively. For both cohorts combined, 389 HBsAg tests were completed in the alert group compared to 177 HBsAg tests in the control group (p < 0.0001; OR = 2.3; 95% CI 1.94-2.80), but there was no increased detection of HBsAg positivity from the alert (15 versus 13 respectively, p = 0.09; OR = 0.5; 95% CI 0.24-1.09). Our results demonstrate that personalized, automated electronic alerts increase screening for CHB, but more comprehensive measures are needed to detect HBsAg positive patients. NIH Trial Registry Number: NCT04240678.""",
                """Based on the most recent analysis of National Health and Nutrition Examination Survey (NHANES), chronic hepatitis B (CHB) affects 847,000 persons in the United States, which included approximately 400,000 non-Hispanic Asians. These Asians had a tenfold greater prevalence of CHB than the American general population 1 . Foreign-born persons have the highest CHB prevalence in the United States, between 4.5 and 10.3%, and the majority of foreign-born persons with CHB living in the United States originated from Asia 2 . Since CHB is the leading cause of hepatocellular carcinoma and cirrhosis in the world 3 , it is not surprising that Asian and Pacific Islanders (API) living in the US have the highest rates of HCC and HCC-related death 4 .""",
                """Because of this, the Centers for Disease Control and Prevention (CDC), United States Preventive Services Task Force, and the American Association for Study of Liver Diseases have recommended screening all persons born in countries with CHB endemicity ≥ 2%. Despite these recommendations, screening rates for CHB remain low, which may be due in part to lack of physician awareness and knowledge about CHB guidelines [5][6][7][8] .""",
                """Because of this, the Centers for Disease Control and Prevention (CDC), United States Preventive Services Task Force, and the American Association for Study of Liver Diseases have recommended screening all persons born in countries with CHB endemicity ≥ 2%. Despite these recommendations, screening rates for CHB remain low, which may be due in part to lack of physician awareness and knowledge about CHB guidelines [5][6][7][8] .""",
            ]
        ),
        reasoning="\n\n".join(
            (
                "Excerpt 1 identifies the two arms for the Cohort 1 (and Cohort 2) study: patients were randomized to alert activation in their electronic medical charts (the 'alert' arm) or not (the control arm).",
                "Excerpt 2 provides background information",
                "Excerpt 3 profides additional background information",
                "Excerpt 4 describes the significance of the findings, alluding to the two groups mentioned above (alert and control), here without specifically mentioning the two studies.",
            )
        ),
        helpfulness="Excerpt 1 was extremely helpful, and excerpt 2, 3, and 4 were not helpful.",
        experiments=numbered_list(["Cohort 1", "Cohort 2"]),
        experiment_in_question="Cohort 1",
        answer="Yes",
    ),
    dict(
        paragraphs=numbered_list(
            [
                """Although the curricula were delivered in English, some children spoke primarily Spanish or Haitian-Creole, particularly at the younger assessment ages. Twenty-five children in Miami and 92 children in LA completed at least one assessment in Spanish, and some assessment items were translated into Haitian-Creole for 7 children in Miami. Children who were bilingual or monolingual non-English speaking were assessed by bilingual staff. Bilingual ability increased over time for foreign language speakers. By third grade, all child assessments were conducted in English. There was no racial or gender bias in the selection of participants.""",
                """Children's cognitive development was assessed directly using the following developmentally appropriate measures: Kaufman Assessment Battery for Children-II (KABC) 25 at ages 3 and 5 years and at third grade ( Y3, Y5, and third grade, respectively) and WoodcockJohnson (WJ) III Tests of Achievement 26 at Y5 and third grade. See Table 4 for a summary of cognitive and language measures and assessment time points.""",
                """All the cognitive composite scores are standardized to a mean of 100 and SD of 15. The KABC measures are widely used, 27 norm-referenced instruments designed to assess cognitive ability 25 with utility for bilingual children. The WJ Tests of Achievement are a comprehensive set of norm-referenced tests for measuring academic achievement. The WJ Tests of Achievement have good reliability and validity 28 and have been used in other large studies with low-income children, such as the Head Start Family and Child Experiences Survey. 29 The WJ Achievement subscales administered in this sample were Letter-Word Identification (Y5 and third grade), Spelling(y5)and Passage Comprehension (third grade) to measure reading skills and Applied Problems (Y5 and third grade) and Calculations (third grade) to measure mathematical skills.""",
                """Child language development was assessed directly with the Preschool Language Scale-4 (PLS) 30 at Y2 and Y4, with the Test of Early Reading Ability-3 (TERA) 31 at Y4, and through maternal report on the Adaptive Language Inventory (ALI) 32 at Y5. The PLS is a normreferenced instrument designed to assess expressive and receptive language skills; the PLS includes 2 subscales, Auditory Comprehension and Expressive Communication, as well as a Total Language score. The TERA is an assessment that measures young children's ability to attribute meaning to printed symbols, knowledge of the alphabet, and understanding of the conventions of print. The TERA has concurrent validity with other measures of reading achievement and verbal intelligence quotient (IQ) tests. 31 The PLS and TERA subscale scores are standardized to a mean of 100 and a SD of 15. The ALI is a rating scale to assess children's use of narrative and discourse skills. Mothers were interviewed on items that addressed the following domains: Comprehension, Expression, Rephrase, Listening, Spontaneity, and Fluency. Total scores for each of these domains range from 4 to 20 for Comprehension, Expression, and Rephrase and from 2 to 10 for Listening, Spontaneity, and Fluency. Alphas for the ALI scales ranged from 0.67 to 0.89 for this sample, indicating moderate to high internal consistency. Language was not separately assessed at the third grade follow-up assessment.""",
            ]
        ),
        reasoning="\n\n".join(
            (
                """Excerpt 1 discusses some findings but does not name trial arms, and it is not clear which experiment is being discussed.""",
                """Excerpt 2 discusses how results were measured but does not identify trial arms.""",
                """Excerpt 3 continues to discuss the assessment methodology""",
                """Excerpt 4 continues to discuss measurement methodology.""",
            )
        ),
        helpfulness="Excerpts 1, 2, 3, and 4 were not helpful.",
        experiments=numbered_list(
            [
                "an RCT of the Legacy for Children program in LA",
                "an RCT of the Legacy for Children program in Miami",
            ]
        ),
        experiment_in_question="an RCT of the Legacy for Children program in Miami",
        answer="No",
    ),
]

SHARED_CAN_WE_NAME_ARMS_PROMPT = dict(
    maybe_plural=plural_transform("experiments", "", "s"),
    order=OrdinalWord(capitalize=True),
    just_one_or_how_many=CountWord("experiments"),
    do_or_does_the_above_excerpts=plural_transform(
        "paragraphs", "does the above excerpt", "do the above excerpts"
    ),
    experiments_count=CountWord("experiments"),
    each_or_the=plural_transform("experiments", "the", "each"),
    were_or_was=plural_transform("experiments", "was", "were"),
    maybe_plural_excerpts=plural_transform("paragraphs", "", "s"),
)

CAN_WE_NAME_ARMS_TEMPLATE = """{order} consider the following excerpt{maybe_plural_excerpts} from a research paper that conducted {just_one_or_how_many} experiment{maybe_plural}:

{paragraphs}

In this paper, there {were_or_was} {experiments_count} experiment{maybe_plural}:

{experiments}

Do these excerpts identify the different trial arms (subgroups of participants) of the "{experiment_in_question}" experiment specifically?

Let's think it over:

{reasoning}

Which excerpts, if any, were helpful in identifying the trial arms (subgroups of participants) of the "{experiment_in_question}" experiment? {helpfulness}

Therefore, {do_or_does_the_above_excerpts} provide insight into what the trial arms were? f we cannot tell from the excerpt{maybe_plural_excerpts}, answer "Unclear". Answer Yes, No, or Unclear. {answer}
"""


def can_we_name_experiments_stop_seq(reasoning: Optional[str]) -> Sequence[str]:
    return ["\n\n"] if reasoning else ["Therefore, "]


def make_can_we_name_arms_prompt(
    experiments: Sequence[str],
    experiment_in_question: str,
) -> Callable[[int], MultipartReasoningPrompt]:
    def from_num_shot(num_shot: int):
        def make_can_we_name_arms_prompt(
            paragraphs: Sequence[str],
            helpfulness: Optional[str] = None,
            reasoning: Optional[str] = None,
        ) -> str:
            last_example: dict = start_last_example(
                helpfulness=helpfulness, reasoning=reasoning, pre_final="Excerpt 1"
            ) | dict(
                paragraphs=numbered_list(paragraphs),
                experiments=numbered_list(experiments),
                experiment_in_question=experiment_in_question,
            )
            shots = format_multi(
                CAN_WE_NAME_ARMS_TEMPLATE,
                CAN_WE_NAME_ARMS_EXAMPLES[:num_shot] + [last_example],
                SHARED_CAN_WE_NAME_ARMS_PROMPT,
            )
            instructions = """When evaluating a Randomized Controlled Trial, we should first identify its methodology; in particular, we should identify how different subgroups of participants were split into different trial arms, in order to receive different treatments or controls. We will look at a few paragraphs from different papers to identify whether any of those paragraphs identify the trial arms for specific experiments. Once we do this task, we will be able to draw a chart identifying, for each experiment, what the trial arms were. After that, we will look to identify how many participants were put into each arm, and how randomization was performed. Some of these excerpts may not be helpful, or it may be unclear. We'll try to find the paragraphs that most clearly identify what the different trial arms for the experiments in question were."""
            parts = [instructions] + list(shots)
            return "\n\n".join(parts)

        return make_can_we_name_arms_prompt

    return from_num_shot


CAN_WE_NAME_ARMS_CHOICES = [" Yes", " No", " Unsure"]
CAN_WE_NAME_ARMS_BEST_CHOICE = " Yes"
CAN_WE_NAME_ARMS_REASONING_STOP = ("\nWhich excerpt",)


def get_can_we_name_arms_reasoning(response: str) -> str:
    return "".join(
        ("Excerpt 1 ", get_part(response, "think it over:\n", "\nWhich excerpts"))
    )


def get_can_we_name_arms_helpfulness(response: str) -> str:
    return get_part(response, "conducted in this study?", "Therefore, do")
