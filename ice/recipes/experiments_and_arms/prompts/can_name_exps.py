from collections.abc import Callable
from collections.abc import Sequence
from typing import Optional
from typing import Union

from ice.formatter.multi import format_multi
from ice.formatter.transform.dependent import CountWord
from ice.formatter.transform.dependent import DependentTransform
from ice.formatter.transform.dependent import plural_transform
from ice.formatter.transform.positional import PositionalTransform
from ice.formatter.transform.value import numbered_list
from ice.formatter.transform.value import ValueTransform
from ice.recipes.experiments_and_arms.prompts.utils import get_part
from ice.recipes.experiments_and_arms.prompts.utils import start_last_example
from ice.recipes.experiments_and_arms.types import MultipartReasoningPrompt


class FirstOrNow(PositionalTransform):
    def transform(self, position: int, total: int) -> str:
        total  # ignored
        if position == 0:
            return "First,"
        else:
            return "Now"


class ExperimentOrExperiments(DependentTransform[list]):
    def key(self):
        return "paragraphs"

    def transform(self, dependent) -> str:
        return "experiment" if len(dependent) == 1 else "experiments"


CAN_WE_NAME_EXPERIMENTS_EXAMPLES: list[
    dict[str, Union[ValueTransform[Sequence[str]], str, int]]
] = [
    dict(
        paragraphs=numbered_list(
            [
                """We present results from six randomized control trials of an integrated approach to improve livelihoods amongst the very poor. The approach combines the transfer of a productive asset with consumption support, training and coaching plus savings encouragement and health education and/or services. Results from the implementation of the same basic program, adapted to a wide variety of geographic and institutional contexts and with multiple implementing partners, show statistically significant, costeffective impacts on consumption (fueled mostly by increases in self-employment income) and psychosocial status of the targeted households. The impact on the poor households lasted at least a year after all implementation ended. It is possible to make sustainable improvements in the economic status of the poor with a relatively short-term intervention.""",
                """More than one fifth of the world\'s population lives on less than Purchasing Power Parity (PPP) US$1.25 a day, and there is an emerging international consensus that this share should (and can) be driven close to zero by 2030 (1,2). Reaching this objective will require enabling the poorest families, who are often the most marginalized within their villages, to shift from insecure and fragile sources of income to more sustainable income-generating activities. One possible avenue, popular with both development organizations and governments, is to promote self-employment activities (such as cow rearing or petty trading). Past efforts to reduce poverty by encouraging these types of activities among the poor, however, have often been plagued by implementation problems and been deemed failures (3). For example, India\'s Integrated Rural Development Program is believed to have been both poorly targeted and ineffective (4,5). However, in recent years, several large non-governmental organizations (prominent international northern NGOs such as Oxfam, World Vision and Heifer, as well as many local NGOs) have gone back to this "livelihood" approach. This past experience raises the question: is it actually possible to reliably improve the livelihoods of the poorest households by giving them access to self-employment activities, or is this entire approach flawed? In particular, is it possible to come up with a model for doing so that can be implemented by a wide variety of organizations and works in a wide range of geographic, institutional, and cultural contexts?""",
                """We present results from randomized control trials (RCTs) in six countries of a particular approach to foster self-employment activities amongst the very poor. Originally designed and implemented by BRAC, a large Bangladeshi NGO that runs several country-wide programs, the "Graduation" program provides a holistic set of services, including the grant of a productive asset, to the poorest households in a village (referred to by BRAC as the "ultra-poor"). The beneficiaries are identified through a participatory process in a village meeting, followed by a verification visit by the organization\'s staff. Selected beneficiaries are then given a productive asset that they choose from a list, training and support for the asset they have chosen, as well as general life skills coaching, weekly consumption support for some fixed period, and typically access to savings accounts and health information or services. These different activities (plus regular interactions with the households over the course of a year) are designed to complement each other in helping households to start a productive self-employment activity. The idea is to provide a "big push", over a limited period of time, with the hope of unlocking a poverty trap. The program costs per household average 100% (range from 62% to 145%) of baseline household consumption. While the program may initially be relatively expensive (compared to just providing training, coaching or a cash transfer), the thinking behind the program is that the combination of these activities is necessary and sufficient to obtain persistent impact on a large fraction of the beneficiaries. 4 including one year after the end of the program, which directly speaks to the sustainability of the changes we observe.""",
                """Of the six experiments, three are individual randomized trials with randomization at the household level within each village (India, Ethiopia and Pakistan) and three are clustered randomized trials, with randomization at both the village and household level (Ghana, Honduras, and Peru). In the countries with clustered randomization, villages were randomly selected to be treatment or control villages, and then treatment households were randomly selected within the set of eligible households in treatment villages.""",
            ]
        ),
        reasoning="\n\n".join(
            [
                "Excerpt 1 does not name the six different RCTs.",
                "Excerpt 2 provides background information but does not name the experiments.",
                "Excerpt 3 indicates that the 6 RCTs were conducted in 6 different countries and descrbies what they have in common, which is to study the 'Graduation' program in each of these countries",
                "Excerpt 4 actually names the 6 experiments: 'India', 'Ethiopia', 'Pakistan', 'Ghana', 'Honduras', and 'Peru'.",
            ]
        ),
        helpfulness="Excerpt 3 was somewhat helpful, excerpt 4 was extremely helpful, and excerpts 1 and 2 were not helpful.",
        experiments_count=6,
        answer="Yes",
    ),
    dict(
        paragraphs=numbered_list(
            [
                """We find that the effects of the workshop are significantly larger for the most disadvantaged. In particular, we show in Table 5 that the least educated, the least experienced, and those with the lowest expected earnings benefit the most from the interventions. For other dimensions, we are unable to find significant differences in response to treatment. 51  he size of the effects for the worst-off workers is substantial. For example, young people without tertiary education increase the earnings by almost 60 percent, while the low predicted earnings group experiences a 50 percent increase. This causes a large reduction in earning inequality: the earning gap between the low and the high earnings group drops from 142 percent to 54 percent and, strikingly, the gap between experienced and inexperienced workers is fully erased. Overall, these results illustrate the large equity gains that can be generated by helping young workers to access the labour market through improved signalling.""",
                """A.17""",
                """Note. In this table we report the intent-to-treat estimates of the direct and indirect effects of the transport intervention and the job application workshop on financial outcomes. These are obtained by OLS estimation of equation ( 1), weighting each observation by the inverse of the probability of being sampled. Below each coefficient estimate, we report the s.e. in parentheses and the q-value in brackets. We correct standard errors to allow for arbitrary correlation at the level of geographical clusters. q-values are obtained using the sharpened procedure of Benjamini et al. (2006). Changing number of observations due to missing values in the dependent variable. In the last three columns we report the mean outcome for the control group, the p-value from a F-test of the null hypothesis that transport subsidies and the job application workshop have the same effect, and the number of observations. ***p< 0.01, **p<0.05, *p<0.1. Note. In this table we report the intent-to-treat estimates of the direct and indirect effects of the transport intervention and the job application workshop on expectations, aspirations and reservation wages. These are obtained by OLS estimation of equation ( 1), weighting each observation by the inverse of the probability of being sampled. Below each coefficient estimate, we report the s.e. in parentheses and the q-value in brackets. We correct standard errors to allow for arbitrary correlation at the level of geographical clusters. q-values are obtained using the sharpened procedure of Benjamini et al. (2006). Changing number of observations due to missing values in the dependent variable. In the last three columns we report the mean outcome for the control group, the p-value from a F-test of the null hypothesis that transport subsidies and the job application workshop have the same effect, and the number of observations. ***p< 0.01, **p<0.05, *p<0.1. Note. In this table we report the intent-to-treat estimates of the direct and indirect effects of the transport intervention and the job application workshop on outcomes related to mobility. These are obtained by OLS estimation of equation ( 1), weighting each observation by the inverse of the probability of being sampled. Below each coefficient estimate, we report the s.e. in parentheses and the q-value in brackets. We correct standard errors to allow for arbitrary correlation at the level of geographical clusters. q-values are obtained using the sharpened procedure of Benjamini et al. (2006). Changing number of observations due to missing values in the dependent variable. In the last three columns we report the mean outcome for the control group, the p-value from a F-test of the null hypothesis that transport subsidies and the job application workshop have the same effect, and the number of observations. ***p< 0.01, **p<0.05, *p<0.1.""",
                """A.19 1), weighting each observation by the inverse of the probability of being sampled. Below each coefficient estimate, we report the s.e. in parentheses and the q-value in brackets. We correct standard errors to allow for arbitrary correlation at the level of geographical clusters. q-values are obtained using the sharpened procedure of Benjamini et al. (2006). Changing number of observations due to missing values in the dependent variable. In the last three columns we report the mean outcome for the control group, the p-value from a F-test of the null hypothesis that transport subsidies and the job application workshop have the same effect, and the number of observations. ***p< 0.01, **p<0.05, *p<0.1.""",
            ]
        ),
        reasoning="\n\n".join(
            (
                "Excerpt 1 discusses findings related to a workshop; this suggests that the experiment had to do with studying the effects of a workshop.",
                "Excerpt 2 is just a reference and does not have any useful content.",
                "Excerpt 3 is a note explaining some analytic methodology related to reporting outcomes from the job application workshop and the transport subsidy. Since there was a single experiment, this suggests that the experiment studied both a job application workshop and a transport subsidy.",
                "Excerpt 4 also explains some analytic methodology; because it seems to compare the effect sizes of the job application workshop and the transport subsidy together, it suggests that these might be two trial arms belonging to a single experiment, but it is ultimately unclear here.",
            )
        ),
        helpfulness="Excerpt 1 was somewhat helpful, excerpts 2 was not helpful, and excerpts 3 and 4 were moderately helpful.",
        experiments_count=1,
        answer="Yes",
    ),
    dict(
        paragraphs=numbered_list(
            [
                """At the beginning of each study session, a verbal explanation about the study and the consent form were given in Nepali by the research assistant, and written informed consent was gathered from participants in a forward and back translated document presented in Nepali. During debriefing, participants were informed that they could still withdraw from the study by contacting the research staff without penalty. A mental health resource list was emailed to participants if they had further questions, concerns, or interest in mental health services. No participants self-disclosed experiencing distress during the procedure, so none were referred for mental healthcare during the study. Participants were not compensated for their participation in the research activities. The procedures for this study were approved by the ethical review boards at Duke University (E0078), TU-IOM (380), KUSMS, and the Nepal Health Research Council (146/2017) prior to data collection. All data were stored on an encrypted server and validated by a second investigator before performing analyses.""",
                """Descriptive statistics summarized the characteristics of the participants. The primary inferential analyses evaluated differences in attitudes and knowledge by comparing intervention groups. Differences in attitudes and knowledge between study conditions were analyzed using linear and logistic regression. The primary comparisons were between (a) both interventions compared to the control and (b) the two intervention groups to each other. Pearson correlation was used to identify relationships between implicit and explicit attitudes as well as correlations between attitudes and knowledge. The implicit and explicit correlation was done to test if reported and unconscious beliefs were related. The other correlation tested if greater knowledge was associated with more positive attitudes. Analyses using IAT data only included frequent computer users. A subsequent regression model was adjusted for personal experience with mental illness to determine the association between the intervention videos and the primary outcome. We conducted an exploratory analysis comparing findings from Study 1 (depression only) and Study 2 (depression and psychosis). All analyses were performed in STATA software v. 15.0 [51] with two-tailed tests using a significance level of 0.05.""",
                """For the qualitative component, interviews were audio recorded and transcribed for analysis. Data management and coding were facilitated using QSR NVivo 11 software [52]. Data analysis was guided using a content analysis strategy. First, the interviews were transcribed, and then two independent reviewers wrote memos for each of the transcripts to identify salient themes and potential codes. A codebook was created using inductive and deductive sources of information to generate major and minor categories of themes. Each code under a theme had a unique definition and inclusion/exclusion criteria. Both researchers applied the codes to each transcript independently, discussed discrepancies until consensus was reached, and iteratively modified the codebook after each discussion. Codes were merged and sub-categorized into different themes for optimal organization and fit. All the transcripts were coded through this technique.""",
                """After review of 2nd and 3rd year MBBS student rosters, 18 students were excluded prior to randomization because of being international students not speaking Nepali or having already completed their psychiatry rotation. Among the remaining students, 100 were selected for randomization to one of the three arms. No potential participants refused to participate in this study. An additional six students were excluded at the time of analysis because information on their demographic forms revealed that they were international students whose native language was not Nepali or they had completed their clinical psychiatry rotation; this information had not been up to date in the class rosters at the time of randomization (Figure 1 ). One participant in the service user arm was excluded because of both being an international non-Nepali student and having completed a psychiatry rotation. Demographic characteristics of these participants are in Table 2 . Participants were randomized into one the three conditions: the control group with no video (n = 31, 33%), the didactic video group (n = 31, 33%), and the service user recovery testimonial video group (n = 32; 34%).""",
            ]
        ),
        reasoning="\n\n".join(
            (
                """Excerpt 1 discusses study methodology, including informed consent and approval from ethical review boards, but it does not discuss how many experiments were conducted.""",
                """Excerpt 2 discusses the analyses methods applied, referring to two studies. Because they call these "studies" and not merely "groups," "conditions," or "arms", this indicates that this paper covers two distinct experiments, one "depression only" study and one "depression and psychosis" study.""",
                """Excerpt 3 discusses the qualitative component of the analysis but does not provide more information about the nature of the two experiments.""",
                """Excerpt 4 discusses randomization across three arms but does not provide more information about which experiment these arms belong to or what distingishes the two experiments.""",
            )
        ),
        helpfulness="Excerpts 1, 3, and 4 were not helpful. Excerpt 2 was somewhat helpful.",
        experiments_count=2,
        answer="Yes",
    ),
]

SHARED_CAN_WE_NAME_EXPERIMENTS_ARGS = dict(
    maybe_plural=plural_transform("experiments_count", "", "s"),
    first_or_now=FirstOrNow(),
    just_one_or_how_many=CountWord("experiments_count", {1: "just one"}),
    do_or_does_the_above_excerpts=plural_transform(
        "paragraphs", "does the above excerpt", "do the above excerpts"
    ),
    each_or_the=plural_transform("experiments_count", "the", "each"),
    were_or_was=plural_transform("experiments_count", "was", "were"),
    maybe_plural_excerpts=plural_transform("paragraphs", "", "s"),
)

CAN_WE_NAME_EXPERIMENTS_TEMPLATE = """{first_or_now} consider the following excerpt{maybe_plural_excerpts} from a research paper that conducted {just_one_or_how_many} experiment{maybe_plural}

{paragraphs}

Let's think it over:

{reasoning}

Which excerpts, if any, were helpful in understanding what the experiment{maybe_plural} conducted in this study {were_or_was}? {helpfulness}

Therefore, {do_or_does_the_above_excerpts} provide insight into what the experiment{maybe_plural} {were_or_was}, including the name of {each_or_the} experiment? If we cannot tell from the excerpt{maybe_plural_excerpts}, answer "Unclear". Answer Yes, No, or Unclear. {answer}
"""


def can_we_name_experiments_stop_seq(reasoning: Optional[str]) -> Sequence[str]:
    return ["\n\n"] if reasoning else ["Therefore, "]


def make_can_we_name_experiments_prompt(
    num_experiments: int,
) -> Callable[[int], MultipartReasoningPrompt]:
    def from_num_shot(num_shots: int):
        def can_we_name_experiments_prompt(
            paragraphs: Sequence[str],
            helpfulness: Optional[str] = None,
            reasoning: Optional[str] = None,
        ) -> str:
            last_example: dict = start_last_example(
                helpfulness=helpfulness, reasoning=reasoning, pre_final="Excerpt 1"
            ) | dict(
                paragraphs=numbered_list(paragraphs),
                experiments_count=num_experiments,
            )
            shots = format_multi(
                CAN_WE_NAME_EXPERIMENTS_TEMPLATE,
                CAN_WE_NAME_EXPERIMENTS_EXAMPLES[:num_shots] + [last_example],
                SHARED_CAN_WE_NAME_EXPERIMENTS_ARGS,
            )
            instructions = """The following excerpts are from a research papers that conducted different numbers of experiments. Experiments are separate studies on distinct populations. Each experiment may have multiple trial arms, which describe the different treatment or control conditions participants were in. Do the following excerpts describe what this experiment was? Don't confuse describing the experiment with describing trial arms in a single experiment."""
            parts = [instructions] + list(shots)
            return "\n\n".join(parts)

        return can_we_name_experiments_prompt

    return from_num_shot


CAN_WE_NAME_EXPERIMENTS_CHOICES = [" Yes", " No", " Unsure"]
CAN_WE_NAME_EXPERIMENTS_BEST_CHOICE = " Yes"
CAN_WE_NAME_EXPERIMENTS_REASONING_STOP = ("\nWhich excerpt",)


def get_can_we_name_experiments_reasoning(response: str) -> str:
    return "".join(
        ("Excerpt 1 ", get_part(response, "think it over:\n", "\nWhich excerpts"))
    )


def get_can_we_name_experiments_helpfulness(response: str) -> str:
    return get_part(response, "conducted in this study?", "Therefore, do")
