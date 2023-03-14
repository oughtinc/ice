import re
from collections import Counter
from collections.abc import Awaitable
from collections.abc import Callable
from typing import Literal
from typing import Optional

from pydantic import BaseModel
from pydantic import BaseSettings
from structlog.stdlib import get_logger
from transformers.models.auto.tokenization_auto import AutoTokenizer
from transformers.models.gpt2.tokenization_gpt2_fast import GPT2TokenizerFast

from ..trace import recorder
from ..trace import trace
from ice.apis.openai import openai_complete
from ice.evaluation.evaluate_recipe_result import RecipeResult
from ice.metrics.gold_standards import list_experiments
from ice.paper import Paper
from ice.paper import Paragraph
from ice.paper import split_sentences
from ice.recipe import Recipe
from ice.utils import filter_async
from ice.utils import map_async
from ice.utils import max_by_value


gpt2_tokenizer: GPT2TokenizerFast = AutoTokenizer.from_pretrained("gpt2")


def n_tokens(prompt: str) -> int:
    tokenized = gpt2_tokenizer(prompt)
    return len(tokenized.input_ids)


def n_remaining_tokens(prompt: str, ensure_min: int, capacity=4097):
    remaining = capacity - n_tokens(prompt)
    if remaining < ensure_min:
        raise ValueError(
            f"Prompt too long by {ensure_min - remaining} tokens: {prompt}"
        )
    return remaining


log = get_logger()


def extract_numbers(text: str) -> list[str]:
    words = text.split()

    set_number_str = {
        "zero",
        "one",
        "two",
        "three",
        "four",
        "five",
        "six",
        "seven",
        "eight",
        "nine",
        "ten",
        "teen",
        "twenty",
        "thirty",
        "forty",
        "fifty",
        "sixty",
        "seventy",
        "eighty",
        "ninety",
        "hundred",
        "thousand",
        "million",
        "billion",
        "trillion",
        "quadrillion",
        "quintillion",
    }
    number_strings = list(filter(lambda word: word.lower() in set_number_str, words))

    numbers_set = set("0123456789")
    number_strings += list(
        filter(lambda x: set(x).intersection(numbers_set) != set(), words)
    )

    # Remove parentheses
    remove_parentheses = (
        lambda s: s.replace("(", "")
        .replace(")", "")
        .replace("...", "")
        .replace("..", "")
    )
    number_strings = list(map(remove_parentheses, number_strings))

    # Remove "," or "." from the end of the number string
    for i, number in enumerate(number_strings):
        if number[-1] == "," or number[-1] == ".":
            number_strings[i] = number[:-1]

    return number_strings


N_TO_STRING: dict[int, str] = {
    1: "one",
    2: "two",
    3: "three",
    4: "four",
    5: "five",
    6: "six",
    7: "seven",
    8: "eight",
    9: "nine",
    10: "ten",
}


def paragraphs_to_numbered_list(paragraphs: list[str]) -> str:
    return "\n".join(
        f"{n}. {paragraph}".strip() for n, paragraph in enumerate(paragraphs, 1)
    )


def even_shorter_intervention_generation_prompt(
    paragraphs: list[str], intervention: str, final_reasoning: Optional[str] = None
) -> str:
    paragraph_n = N_TO_STRING[len(paragraphs)]
    prefix = f"""From the textbook, "Critically Evaluating Interventional Studies," Chapter 3:

When evaluating the quality of a randomized controlled trial, you should also consider whether any participants dropped out of the study or failed to follow its protocols correctly. This is sometimes called "adherence," "attrition," or "compliance". If too many participants failed to receive the intervention or perform it correctly, for whatever reason, this may damage the internal validity of the study's results.

Unfortunately, papers are often not as clear as they should be when discussing adherence. For simple interventions that are accomplished in one shot (e.g., having a group of college students complete a test in a lab that takes 30 minutes), the study doesn't discuss adherence unless something unusual happened, and we can safely assume that everyone in the sample completed the study. Sometimes studies provide specific numbers or percentages of people who dropped out (attrited), and sometimes they only provide qualitative descriptions, such as saying that adherence was "generally good." Often, papers are genuinely unclear, and we can only conclude that there is not enough information in the paper for us to know anything about adherence or compliance.

Let's look at excerpts from six different papers to see what information, if any, they provide about the study's adherence, attrition, or compliance. We'll have to identify what each extract tells us about adherence (some extracts may only discuss methodology or results, telling us nothing about adherence), and for some, we may have to conclude that the attrition or compliance is simply unclear.

First, consider these three excerpts from a paper studying the Tumaini game:

1. Intervention arm participants completed a 45-minute informational onboarding session, including instructions on the interface, technology, and game content. They were instructed to play at least 1 hour per day for the 16 days of the study and asked not to share their own gameplay profile with others. The game interface allows for 5 additional players' profiles so that others may play without compromising the enrolled player's data. Intervention participants were provided with a phone with the game preloaded and used it at their own pace for the duration of the intervention. Control participants received standard of care, namely no additional intervention beyond any existing sex education from family, school, and peers. No specific data on the content or source of this education were collected from participants. All study smartphones were returned by the participants at the end of the intervention period.
2. Preliminary cleaning of survey data was conducted in MS Excel, with additional cleaning and all analyses completed using SAS version 9.4 (SAS Institute Inc., Cary, NC, USA). All control arm participants were included in analyses. One participant from the intervention arm was removed from analyses of effect at T2 due to delayed completion of the T2 survey. His data were retained for T1-T3 analyses, as he completed all other study activities on time. Descriptive statistics on demographic questions and game feedback questions were computed.
3. We recruited and enrolled 60 adolescent participants. Half of the participants were allocated to the intervention arm. All adolescents who were recruited completed all 3 study visits, and all intervention arm participants initiated gameplay. Participant demographics are presented in Table 3 . There were no significant demographic differences between the two arms. Preliminary calculations of exposure indicate that the intervention arm played Tumaini a mean of approximately 27 hours over the 16 days of the intervention.

Let's think about what each excerpt tells us, if anything, about adherence, attrition or compliance: The first excerpt describes the study's methodology, but does not tell us how many or how well participants followed the instructions, so it does not inform us about adherence. The second excerpt tells us that all control arm participants were included in analysis, but one intervention arm participant was removed from the analysis of effect at T2 but included in the T3 analysis; this is attrition information. The third excerpt says that all participants completed all visits and that all intervention arm participants initiated gameplay; this is adherence information.

Here's all the information in this paper about adherence, attrition, and compliance: All participants completed all visits, and all intervention arm participants initiated gameplay. One intervention arm participant was not included in the T2 analysis but was included in the T3 analysis.

Second, consider these three excerpts from a paper studying antioxidant/anti-inflammatory supplement containing lemon verbena extract and omega-3 fatty acid:

1. Flow chart showing the dropout rate at different timepoints in the study.
2. Forty-eight (48) participants were enrolled for screening evaluation (Fig. 1 ) and after 3 exclusions, 45 participants were randomly assigned either to placebo or nutritional supplement groups, n = 22 and n = 23, respectively. Of these, 14 participants were withdrawn during the study for different reasons; there were 10 dropouts in the placebo group and 4 dropouts in the supplement group (treatment refusal, irregular treatment, starting on medication, or occurrence of an adverse event [AE]). Finally, 31 participants completed the study (12 in the placebo and 19 in the supplement group; Fig. 1 ).
3. Only 1 patient reported an AE (i.e., a heartburn sensation). The subject, who was in the placebo group, stopped the treatment immediately and was excluded from the study (Table 1 ). No major complications were reported by this subject.

Let's think about what each excerpt tells us, if anything, about adherence, attrition or compliance: The first excerpt refers to a flow chart showing the dropout rate, but since we do not have the figure here, we cannot conclude anything from this about the study's attrition. The second excerpt says that there were 10 dropouts in the placebo group of 22 participants and 4 dropouts in the supplement group of 23 participants, meaning that 31 participants out of the initial 45 participants after randomization completed the study. The third excerpt provides more detail for one patient in the placebo group who dropped out, stopping treatment after experiencing a heartburn sensation.

Here's all the the information in this paper about adherence, attrition, and compliance: Ten of the 22 participants in the placebo group dropped out, and 4 of the 23 participants in the supplement group dropped out.

Third, consider these {paragraph_n} excerpt{"s" if len(paragraphs) > 1 else ""} from a paper studying {intervention}:

{paragraphs_to_numbered_list(paragraphs).strip()}

Let's think about what {"each" if len(paragraphs) > 1 else "this"} excerpt tells us, if anything, about adherence, attrition or compliance:""".strip()

    if final_reasoning is None:
        return prefix
    return f"""{prefix} {final_reasoning.strip()}

Here's all the information in this paper about adherence, attrition, and compliance:""".strip()


def shorter_intervention_generation_prompt(
    paragraphs: list[str], intervention: str, final_reasoning: Optional[str] = None
) -> str:
    paragraph_n = N_TO_STRING[len(paragraphs)]
    prefix = f"""From the textbook, "Critically Evaluating Interventional Studies," Chapter 3:

When evaluating the quality of a randomized controlled trial, you should also consider whether any participants dropped out of the study or failed to follow its protocols correctly. This is sometimes called "adherence," "attrition," or "compliance". If too many participants failed to receive the intervention or perform it correctly, for whatever reason, this may damage the internal validity of the study's results.

Unfortunately, papers are often not as clear as they should be when discussing adherence. For simple interventions that are accomplished in one shot (e.g., having a group of college students complete a test in a lab that takes 30 minutes), the study doesn't discuss adherence unless something unusual happened, and we can safely assume that everyone in the sample completed the study. Sometimes studies provide specific numbers or percentages of people who dropped out (attrited), and sometimes they only provide qualitative descriptions, such as saying that adherence was "generally good." Often, papers are genuinely unclear, and we can only conclude that there is not enough information in the paper for us to know anything about adherence or compliance.

Let's look at excerpts from six different papers to see what information, if any, they provide about the study's adherence, attrition, or compliance. We'll have to identify what each extract tells us about adherence (some extracts may only discuss methodology or results, telling us nothing about adherence), and for some, we may have to conclude that the attrition or compliance is simply unclear.

First, consider these three excerpts from a paper studying the Tumaini game:

1. Intervention arm participants completed a 45-minute informational onboarding session, including instructions on the interface, technology, and game content. They were instructed to play at least 1 hour per day for the 16 days of the study and asked not to share their own gameplay profile with others. The game interface allows for 5 additional players' profiles so that others may play without compromising the enrolled player's data. Intervention participants were provided with a phone with the game preloaded and used it at their own pace for the duration of the intervention. Control participants received standard of care, namely no additional intervention beyond any existing sex education from family, school, and peers. No specific data on the content or source of this education were collected from participants. All study smartphones were returned by the participants at the end of the intervention period.
2. Preliminary cleaning of survey data was conducted in MS Excel, with additional cleaning and all analyses completed using SAS version 9.4 (SAS Institute Inc., Cary, NC, USA). All control arm participants were included in analyses. One participant from the intervention arm was removed from analyses of effect at T2 due to delayed completion of the T2 survey. His data were retained for T1-T3 analyses, as he completed all other study activities on time. Descriptive statistics on demographic questions and game feedback questions were computed.
3. We recruited and enrolled 60 adolescent participants. Half of the participants were allocated to the intervention arm. All adolescents who were recruited completed all 3 study visits, and all intervention arm participants initiated gameplay. Participant demographics are presented in Table 3 . There were no significant demographic differences between the two arms. Preliminary calculations of exposure indicate that the intervention arm played Tumaini a mean of approximately 27 hours over the 16 days of the intervention.

Let's think about what each excerpt tells us, if anything, about adherence, attrition or compliance: The first excerpt describes the study's methodology, but does not tell us how many or how well participants followed the instructions, so it does not inform us about adherence. The second excerpt tells us that all control arm participants were included in analysis, but one intervention arm participant was removed from the analysis of effect at T2 but included in the T3 analysis; this is attrition information. The third excerpt says that all participants completed all visits and that all intervention arm participants initiated gameplay; this is adherence information.

Here's all the information in this paper about adherence, attrition, and compliance: All participants completed all visits, and all intervention arm participants initiated gameplay. One intervention arm participant was not included in the T2 analysis but was included in the T3 analysis.

Second, consider these four excerpts from a paper studying Study 2 on depression and psychosis:

1. The intervention was a single session that lasted approximately one hour for participants to provide informed consent, complete a demographic form, watch videos relevant to their study arm, complete the assessments, and be debriefed. Participants in either of the video groups stayed for the full hour, but participants in the control condition who did not watch the video finished in about 50 min. In Study 2, which included two 8 min videos with diagnostic accuracy for both conditions, the protocol required an additional 15 min. Survey data were collected using SurveyCTO (Ver 2.30, Dobility, Inc., Cambridge, MA, USA), an android application, on tablets (www.surveycto.com/accessed on: 19 June 2017). In Study 1, after completion of the video session, participants were invited to participate in the optional qualitative interview to be held within one week.
2. After review of 2nd and 3rd year MBBS student rosters, 18 students were excluded prior to randomization because of being international students not speaking Nepali or having already completed their psychiatry rotation. Among the remaining students, 100 were selected for randomization to one of the three arms. No potential participants refused to participate in this study. An additional six students were excluded at the time of analysis because information on their demographic forms revealed that they were international students whose native language was not Nepali or they had completed their clinical psychiatry rotation; this information had not been up to date in the class rosters at the time of randomization (Figure 1 ). One participant in the service user arm was excluded because of both being an international non-Nepali student and having completed a psychiatry rotation. Demographic characteristics of these participants are in Table 2 . Of note, only three participants indicated that they were primarily interested psychiatry as a specialty (see Figure 2 ). Participants were randomized into one the three conditions: the control group with no video (n = 31, 33%), the didactic video group (n = 31, 33%), and the service user recovery testimonial video group (n = 32; 34%).
3. Due to limited time availability on the part of the researchers and students as well as the exploratory nature of the interviews, only six participants completed interviews. Qualitative results were analyzed from a subset of six students, two women and four men in their third year, who participated in in-depth interviews.
4. For the second study, 248 students were enrolled in first-and second-year MBBS program across the two institutions participating. From roster, 28 students were excluded because of being international or having completed a psychiatry clinical rotation. The remaining 220 students were randomized; however, seven students declined to participate or were unavailable during data collection periods. Therefore, 213 participants were randomly allocated to the following arms: didactic video condition (n = 73), the service user video condition (n = 72), and the no video control condition (n = 75) (Figure 3 ). At the analysis phase, there were additional exclusions because of missing data or identification of exclusion criteria that was not recorded in the school registers. Participant characteristics for each condition are shown in Table 4 .

Let's think about what each excerpt tells us, if anything, about adherence, attrition or compliance. The first excerpt describes the methodology, describing the intervention as taking place in a single one-hour session. This does not tell us anything explicitly about adherence, but it does make it more likely that adherence was high, since participants only had to attend the single session, which is easy to do. The second excerpt says that 18 students were excluded prior to randomization; since this took place before sampling, it is not relevant to adherence. It also says that six students were excluded at the time of analysis because it turned out that they met exclusion criteria. Although this is not adherence strictly speaking, it is important to note when thinking about the validity of the results. The third excerpt says that only six participants completed interviews. The fourth excerpt says that in Study 2, seven students declined to participate or were not available during data collection after randomization of 220 students, and there were additional exclusions at analysis phase because of missing data or identification of exclusion criteria.

Here's all the information in this paper about adherence, attrition, and compliance: This paper does not discuss adherence explicitly. For the video study, six of the 100 randomized students were excluded from analysis, and in the second study, seven of the 220 randomized students declined to participate or were unavailable during data collection periods, with additional students excluded from the analysis because of missing data or identification of exclusion criteria. Only six participants completed interviews.

Third, consider these three excerpts from a paper studying antioxidant/anti-inflammatory supplement containing lemon verbena extract and omega-3 fatty acid:

1. Flow chart showing the dropout rate at different timepoints in the study.
2. Forty-eight (48) participants were enrolled for screening evaluation (Fig. 1 ) and after 3 exclusions, 45 participants were randomly assigned either to placebo or nutritional supplement groups, n = 22 and n = 23, respectively. Of these, 14 participants were withdrawn during the study for different reasons; there were 10 dropouts in the placebo group and 4 dropouts in the supplement group (treatment refusal, irregular treatment, starting on medication, or occurrence of an adverse event [AE]). Finally, 31 participants completed the study (12 in the placebo and 19 in the supplement group; Fig. 1 ).
3. Only 1 patient reported an AE (i.e., a heartburn sensation). The subject, who was in the placebo group, stopped the treatment immediately and was excluded from the study (Table 1 ). No major complications were reported by this subject.

Let's think about what each excerpt tells us, if anything, about adherence, attrition or compliance: The first excerpt refers to a flow chart showing the dropout rate, but since we do not have the figure here, we cannot conclude anything from this about the study's attrition. The second excerpt says that there were 10 dropouts in the placebo group of 22 participants and 4 dropouts in the supplement group of 23 participants, meaning that 31 participants out of the initial 45 participants after randomization completed the study. The third excerpt provides more detail for one patient in the placebo group who dropped out, stopping treatment after experiencing a heartburn sensation.

Here's all the the information in this paper about adherence, attrition, and compliance: Ten of the 22 participants in the placebo group dropped out, and 4 of the 23 participants in the supplement group dropped out.

Fourth, consider these {paragraph_n} excerpt{"s" if len(paragraphs) > 1 else ""} from a paper studying {intervention}:

{paragraphs_to_numbered_list(paragraphs).strip()}

Let's think about what {"each" if len(paragraphs) > 1 else "this"} excerpt tells us, if anything, about adherence, attrition or compliance:""".strip()

    if final_reasoning is None:
        return prefix
    return f"""{prefix} {final_reasoning.strip()}

Here's all the information in this paper about adherence, attrition, and compliance:""".strip()


def intervention_generation_prompt(
    paragraphs: list[str], intervention: str, final_reasoning: Optional[str] = None
) -> str:
    paragraph_n = N_TO_STRING[len(paragraphs)]
    prefix = f"""From the textbook, "Critically Evaluating Interventional Studies," Chapter 3:

When evaluating the quality of a randomized controlled trial, you should also consider whether any participants dropped out of the study or failed to follow its protocols correctly. This is sometimes called "adherence," "attrition," or "compliance". If too many participants failed to receive the intervention or perform it correctly, for whatever reason, this may damage the internal validity of the study's results.

Unfortunately, papers are often not as clear as they should be when discussing adherence. For simple interventions that are accomplished in one shot (e.g., having a group of college students complete a test in a lab that takes 30 minutes), the study doesn't discuss adherence unless something unusual happened, and we can safely assume that everyone in the sample completed the study. Sometimes studies provide specific numbers or percentages of people who dropped out (attrited), and sometimes they only provide qualitative descriptions, such as saying that adherence was "generally good." Often, papers are genuinely unclear, and we can only conclude that there is not enough information in the paper for us to know anything about adherence or compliance.

Let's look at excerpts from five different papers to see what information, if any, they provide about the study's adherence, attrition, or compliance. We'll have to identify what each extract tells us about adherence (some extracts may only discuss methodology or results, telling us nothing about adherence), and for some, we may have to conclude that the attrition or compliance is simply unclear.

First, consider these three excerpts from a paper studying the Tumaini game:

1. Intervention arm participants completed a 45-minute informational onboarding session, including instructions on the interface, technology, and game content. They were instructed to play at least 1 hour per day for the 16 days of the study and asked not to share their own gameplay profile with others. The game interface allows for 5 additional players' profiles so that others may play without compromising the enrolled player's data. Intervention participants were provided with a phone with the game preloaded and used it at their own pace for the duration of the intervention. Control participants received standard of care, namely no additional intervention beyond any existing sex education from family, school, and peers. No specific data on the content or source of this education were collected from participants. All study smartphones were returned by the participants at the end of the intervention period.
2. Preliminary cleaning of survey data was conducted in MS Excel, with additional cleaning and all analyses completed using SAS version 9.4 (SAS Institute Inc., Cary, NC, USA). All control arm participants were included in analyses. One participant from the intervention arm was removed from analyses of effect at T2 due to delayed completion of the T2 survey. His data were retained for T1-T3 analyses, as he completed all other study activities on time. Descriptive statistics on demographic questions and game feedback questions were computed.
3. We recruited and enrolled 60 adolescent participants. Half of the participants were allocated to the intervention arm. All adolescents who were recruited completed all 3 study visits, and all intervention arm participants initiated gameplay. Participant demographics are presented in Table 3 . There were no significant demographic differences between the two arms. Preliminary calculations of exposure indicate that the intervention arm played Tumaini a mean of approximately 27 hours over the 16 days of the intervention.

Let's think about what each excerpt tells us, if anything, about adherence, attrition or compliance: The first excerpt describes the study's methodology, but does not tell us how many or how well participants followed the instructions, so it does not inform us about adherence. The second excerpt tells us that all control arm participants were included in analysis, but one intervention arm participant was removed from the analysis of effect at T2 but included in the T3 analysis; this is attrition information. The third excerpt says that all participants completed all visits and that all intervention arm participants initiated gameplay; this is adherence information.

Here's all the information in this paper about adherence, attrition, and compliance: All participants completed all visits, and all intervention arm participants initiated gameplay. One intervention arm participant was not included in the T2 analysis but was included in the T3 analysis.

Second, consider these three excerpts from a paper studying the Preschool Situational Self-Regulation Toolkit (PRSIST) Program:

1. All children in their final prior-to-school year in these centers, who attended at least one of the 1-2 assessment days, were invited to participate in this study. There were no further exclusion criteria. Parental consent to participate was provided for 547 3-5-year old children, all of whom were identified as likely to be attending school in the subsequent year. The flow of participants throughout the study is depicted in Figure 1 . At baseline, 473 of these children were assessed (86.5%), with non-participation largely due to absence on the day of assessment. The mean age of this sample was 4.44 years (SD = 0.38, range = 3.20-5.33), with a relative balance of boys and girls (48.2% girls). Children who were identified as of Aboriginal or Torres Strait Islander descent comprised 7.2% of the sample, which is in line with population estimates for this age group (Australian Institute of Health and Welfare (AIHW), 2012). Family income was diverse: 11.9% of families qualified for full childcare benefit subsidies (low income); 65.5% of families qualified for some childcare benefit (low-middle to middle-high income); and 22.7% of families did not qualify for any childcare benefit subsidy (high income). Maternal education levels were also diverse: 9.5% did not complete high school; 9.3% completed only high school; 30.6% had completed a diploma, trade, certificate; 34.6% completed a tertiary degree; and 16.0% a post-graduate qualification. At follow-up, 426 children were assessed, which corresponded to a 90.1% retention rate. Nonparticipation at follow-up was due to the child having left the center or absence on the day of assessment.
2. Based on these patterns of participation, 20 services (80%) were deemed to have met or exceeded the minimum threshold of participation (i.e., completed the professional development modules and met the minimum of three child activities per week). Those that did not participate in the program were a result of: preparations for government assessment and rating (n = 1); substantial illness, maternity leave or turnover of key staff that precluded participation (n = 2); or low-or non-participation for undisclosed reasons (n = 2). Two of these five centers did not participate in any program elements. The other three centers did not engage with professional development modules or induction teleconference call yet completed child activities. Overall, there were good levels of adherence to the program, especially amongst those centers without significant sector-imposed impediments to participation.
3. Inability to conclusively and exclusively provide evidence for one of these possibilities, however, highlights limitations within the current study. That is, although the evaluation was rigorously designed and executed according to CONSORT guidelines, funding considerations limited the roll-out and intervention period to only 6 months. It is possible that a full year of program implementation would yield stronger program effects (see, for example, Schachter, 2015). It is also possible that program effects would be strengthened with stricter adherence to highquality program implementation. While fidelity data indicate good compliance in the frequency and timing of program elements, data are insufficient to evaluate the integrity with which program elements were implemented. While in-person or video fidelity checks were not possible in the current study, this would help monitor adherence. As a researcher-implemented model of delivery would violate our aspiration for a lowcost and barrier-free resource for educators, a plausible middle ground might be a coaching model that supports educators in implementation and adaptation of the program in their context. Lastly, the program was designed with the intention to foster selfregulation in all children, and thus did not focus on instances of dysregulation. However, it is clear that child dysregulation remains a significant concern for educators (Neilsen-Hewett et al., 2019), and future iterations of the program would do well to more explicitly provide support for these children. In guiding such an expansion of the program, there is evidence that children with frequent and severe dysregulation require a different approach to fostering self-regulation, as demonstrated successfully in trauma-informed practice approaches (Holmes et al., 2015). Future studies would also do well to consider implications of differing educator qualifications and experience, whereby different types and levels of support may be needed at varying levels of behavior challenges and educators' skills to address these.

Let's think about what each excerpt tells us, if anything, about adherence, attrition or compliance: The first excerpt includes demographic information about the participants but also reveals that at baseline, 473 of the total sample of 547 children were assessed (with non-participation mostly due to absence), and at follow-up, 426 children were assessed (with non-participation mostly due to the child having left the center or absence), corresponding to a 90.1% retention rate. The second excerpt describes compliance with protocols: 20 of the 25 intervention centers met or exceeded the minimum threshold of participation. The third excerpt describes compliance in the frequency and timing of program elements as "good" but also says that the study did not monitor adherence with in-person or video checks, which would have helped provide a better picture of compliance with the study design.

Here's all the information in this paper about adherence, attrition, and compliance: Of the initial sample of 547 children, 473 were assessed at baseline and 426 at follow-up. While 20 of 25 intervention centers met or exceeded the minimum threshold of participation and the frequency and timing of program elements was good, the study did not monitor adherence with in-person or video checks.

Third, consider these four excerpts from a paper studying Study 2 on depression and psychosis:

1. The intervention was a single session that lasted approximately one hour for participants to provide informed consent, complete a demographic form, watch videos relevant to their study arm, complete the assessments, and be debriefed. Participants in either of the video groups stayed for the full hour, but participants in the control condition who did not watch the video finished in about 50 min. In Study 2, which included two 8 min videos with diagnostic accuracy for both conditions, the protocol required an additional 15 min. Survey data were collected using SurveyCTO (Ver 2.30, Dobility, Inc., Cambridge, MA, USA), an android application, on tablets (www.surveycto.com/accessed on: 19 June 2017). In Study 1, after completion of the video session, participants were invited to participate in the optional qualitative interview to be held within one week.
2. After review of 2nd and 3rd year MBBS student rosters, 18 students were excluded prior to randomization because of being international students not speaking Nepali or having already completed their psychiatry rotation. Among the remaining students, 100 were selected for randomization to one of the three arms. No potential participants refused to participate in this study. An additional six students were excluded at the time of analysis because information on their demographic forms revealed that they were international students whose native language was not Nepali or they had completed their clinical psychiatry rotation; this information had not been up to date in the class rosters at the time of randomization (Figure 1 ). One participant in the service user arm was excluded because of both being an international non-Nepali student and having completed a psychiatry rotation. Demographic characteristics of these participants are in Table 2 . Of note, only three participants indicated that they were primarily interested psychiatry as a specialty (see Figure 2 ). Participants were randomized into one the three conditions: the control group with no video (n = 31, 33%), the didactic video group (n = 31, 33%), and the service user recovery testimonial video group (n = 32; 34%).
3. Due to limited time availability on the part of the researchers and students as well as the exploratory nature of the interviews, only six participants completed interviews. Qualitative results were analyzed from a subset of six students, two women and four men in their third year, who participated in in-depth interviews.
4. For the second study, 248 students were enrolled in first-and second-year MBBS program across the two institutions participating. From roster, 28 students were excluded because of being international or having completed a psychiatry clinical rotation. The remaining 220 students were randomized; however, seven students declined to participate or were unavailable during data collection periods. Therefore, 213 participants were randomly allocated to the following arms: didactic video condition (n = 73), the service user video condition (n = 72), and the no video control condition (n = 75) (Figure 3 ). At the analysis phase, there were additional exclusions because of missing data or identification of exclusion criteria that was not recorded in the school registers. Participant characteristics for each condition are shown in Table 4 .

Let's think about what each excerpt tells us, if anything, about adherence, attrition or compliance. The first excerpt describes the methodology, describing the intervention as taking place in a single one-hour session. This does not tell us anything explicitly about adherence, but it does make it more likely that adherence was high, since participants only had to attend the single session, which is easy to do. The second excerpt says that 18 students were excluded prior to randomization; since this took place before sampling, it is not relevant to adherence. It also says that six students were excluded at the time of analysis because it turned out that they met exclusion criteria. Although this is not adherence strictly speaking, it is important to note when thinking about the validity of the results. The third excerpt says that only six participants completed interviews. The fourth excerpt says that in Study 2, seven students declined to participate or were not available during data collection after randomization of 220 students, and there were additional exclusions at analysis phase because of missing data or identification of exclusion criteria.

Here's all the information in this paper about adherence, attrition, and compliance: This paper does not discuss adherence explicitly. For the video study, six of the 100 randomized students were excluded from analysis, and in the second study, seven of the 220 randomized students declined to participate or were unavailable during data collection periods, with additional students excluded from the analysis because of missing data or identification of exclusion criteria. Only six participants completed interviews.

Fourth, consider these three excerpts from a paper studying antioxidant/anti-inflammatory supplement containing lemon verbena extract and omega-3 fatty acid:

1. Flow chart showing the dropout rate at different timepoints in the study.
2. Forty-eight (48) participants were enrolled for screening evaluation (Fig. 1 ) and after 3 exclusions, 45 participants were randomly assigned either to placebo or nutritional supplement groups, n = 22 and n = 23, respectively. Of these, 14 participants were withdrawn during the study for different reasons; there were 10 dropouts in the placebo group and 4 dropouts in the supplement group (treatment refusal, irregular treatment, starting on medication, or occurrence of an adverse event [AE]). Finally, 31 participants completed the study (12 in the placebo and 19 in the supplement group; Fig. 1 ).
3. Only 1 patient reported an AE (i.e., a heartburn sensation). The subject, who was in the placebo group, stopped the treatment immediately and was excluded from the study (Table 1 ). No major complications were reported by this subject.

Let's think about what each excerpt tells us, if anything, about adherence, attrition or compliance: The first excerpt refers to a flow chart showing the dropout rate, but since we do not have the figure here, we cannot conclude anything from this about the study's attrition. The second excerpt says that there were 10 dropouts in the placebo group of 22 participants and 4 dropouts in the supplement group of 23 participants, meaning that 31 participants out of the initial 45 participants after randomization completed the study. The third excerpt provides more detail for one patient in the placebo group who dropped out, stopping treatment after experiencing a heartburn sensation.

Here's all the the information in this paper about adherence, attrition, and compliance: Ten of the 22 participants in the placebo group dropped out, and 4 of the 23 participants in the supplement group dropped out.

Fifth, consider these {paragraph_n} excerpt{"s" if len(paragraphs) > 1 else ""} from a paper studying {intervention}:

{paragraphs_to_numbered_list(paragraphs).strip()}

Let's think about what {"each" if len(paragraphs) > 1 else "this"} excerpt tells us, if anything, about adherence, attrition or compliance:""".strip()

    if final_reasoning is None:
        return prefix
    return f"""{prefix} {final_reasoning.strip()}

Here's all the the information in this paper about adherence, attrition, and compliance:""".strip()


async def complete_with_cache_buster(
    prompt: str, temperature: float, max_tokens: int, top_p: float, stop, cache_id: int
):
    return await openai_complete(
        stop=stop,
        prompt=prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
        cache_id=cache_id,
    )


def remove_last_subsentence(text: str) -> str:
    sentences = split_sentences(text)
    if not sentences[-1].strip().endswith("."):
        log.warning("Removing last sentence", sentences=sentences)
        sentences = sentences[:-1]
    return " ".join(sentences)


@trace
async def sample_generation_answer_with_reasoning(
    paragraphs: list[str],
    intervention: str,
    cache_id: int,
    ranked_paragraphs: list[str],
) -> tuple["AnswerWithReasoning", Callable]:
    """Sample reasoning and a final answer,
    given the prompt. Shorten the prompt dynamically
    to fit in the paragraphs provided, by first
    reducing the number of few-shot examples, then
    dropping the paragraphs that are least likely to be
    about adherence.
    """
    for prompt_func in (
        intervention_generation_prompt,
        shorter_intervention_generation_prompt,
        even_shorter_intervention_generation_prompt,
    ):
        prompt = prompt_func(paragraphs, intervention)
        used_prompt_func = prompt_func

        if n_remaining_tokens(prompt, -100_000) >= 400:
            break

    while n_remaining_tokens(prompt, -100_000) < 400:  # some huge negative number
        paragraphs = remove_worst_paragraph(paragraphs, ranked_paragraphs)
        if not paragraphs:
            raise ValueError("Prompt too long with even one paragraph")
        prompt = shorter_intervention_generation_prompt(paragraphs, intervention)
        log.warning("Dropped paragraph", n=len(paragraphs))

    response = await complete_with_cache_buster(
        prompt=prompt,
        temperature=0.4,
        max_tokens=n_remaining_tokens(prompt, 400) - 100,
        top_p=1,
        stop=("\nFourth", "\nFifth", "\nSixth", "\nFinally"),
        cache_id=cache_id,
    )
    response_text = response["choices"][0]["text"]
    token_usage = response["usage"]["total_tokens"]
    if (
        "Here's all the information in this paper about adherence, attrition, and compliance:"
        in response_text
    ):
        reasoning, answer = response_text.split(
            "Here's all the information in this paper about adherence, attrition, and compliance:"
        )
        return (
            AnswerWithReasoning(
                paragraph="\n\n".join(paragraphs),
                reasoning=reasoning.strip(),
                answer=remove_last_subsentence(answer.strip()),
                token_usage=token_usage,
            ),
            used_prompt_func,
        )
    log.warning(
        "Unexpected response for final generation reasoning", response=response_text
    )
    return (
        AnswerWithReasoning(
            paragraph="\n\n".join(paragraphs),
            reasoning=remove_last_subsentence(response_text.strip()),
            answer=response_text.strip(),
            token_usage=token_usage,
        ),
        used_prompt_func,
    )


@trace
async def final_answer_with_reasoning(
    paragraphs: list[str], intervention: str, ranked_paragraphs: list[str]
):
    """Sample ten completions, and choose a reasoning which has the most
    numbers in common with the other reasonings.

    Use that reasoning as support to complete the final answer.
    """
    answers_short = [
        (
            await sample_generation_answer_with_reasoning(
                paragraphs, intervention, cache_id, ranked_paragraphs
            )
        )
        for cache_id in range(10)
    ]
    answers = [answer[0] for answer in answers_short]
    used_prompt_func = answers_short[0][1]
    total_token_usage = sum([a.token_usage for a in answers])
    print(f"Total token usage: {total_token_usage}")
    numbers_in_answers = [extract_numbers(a.answer) for a in answers]
    for nums, answer in zip(numbers_in_answers, answers):
        if "unclear" in answer.answer.lower():
            nums.append("Unclear")

    def rank(numbers, number):
        r = 0
        for n in numbers:
            if number in n:
                r += 1
        return r

    scores: list[float] = []

    for numbers in numbers_in_answers:
        score = 0.0
        for number in numbers:
            score += rank(numbers_in_answers, number)
        if numbers:
            score /= len(numbers)
            score += 0.01 * len(numbers)
            scores.append(score)
        else:
            scores.append(0)

    answers_with_scores = [(answer, score) for answer, score in zip(answers, scores)]
    best_answer = max(answers_with_scores, key=lambda aws: aws[1])[0]

    final_prompt = used_prompt_func(
        paragraphs=paragraphs,
        intervention=intervention,
        final_reasoning=best_answer.reasoning,
    )

    final_answer = await complete_with_cache_buster(
        prompt=final_prompt,
        temperature=0.0,
        max_tokens=n_remaining_tokens(final_prompt, 83),
        top_p=1,
        stop=("\nFourth", "\nFifth", "\nSixth", "\nFinally"),
        cache_id=0,
    )
    final_answer_text = final_answer["choices"][0]["text"]
    return AnswerWithReasoning(
        paragraph="\n\n".join(paragraphs),
        reasoning=best_answer.reasoning,
        answer=remove_last_subsentence(final_answer_text),
        token_usage=final_answer["usage"]["total_tokens"],
    )


def intervention_classification_prompt(paragraph: str, intervention: str):
    return f"""
From the textbook, "Critically Evaluating Interventional Studies," Chapter 3:

When evaluating the quality of a randomized controlled trial, you should also consider whether any participants dropped out of the study or failed to follow its protocols correctly. This is sometimes called "adherence," "attrition," or "compliance". If too many participants failed to receive the intervention or failed to receive it correctly, for whatever reason, this may damage the internal validity of the study's results.

Unfortunately, papers are often not as clear as they should be when discussing adherence. Sometimes it can be tricky to tell whether the author is talking about adherence/compliance with the study's protocols versus simply discussing the results of the study. For simple interventions that are accomplished in one shot (e.g., having a group of college students complete a test in a lab that takes 30 minutes), the study doesn't discuss adherence unless something unusual happened, and we can safely assume that everyone in the sample completed the study.

Let's look at five examples to decide whether they contain information about adherence or compliance. For each paragraph, we'll conclude whether the paragraph does tell us about the study's adherence.

First, consider this paragraph from a paper studying non-cognitive skills certificate disclosure to job candidates and firms:

---
38 Information on whether each job interview in the matching intervention turned into a hire (and on the associated job characteristics) was collected in both the firm and worker follow-ups. We prefer to use information from the worker follow-ups for these match-level outcomes as measurement error is likely to be lower there for at least two reasons: (i) while the median firm was matched to three workers, the median worker was matched Figure 4 shows a summary of compliance and attrition. Starting from compliance, of the 1,230 scheduled job interviews, 515 (or 42%) actually took place. Lack of compliance is mainly due to workers having lost interest in being matched (32% of cases) or to the firm having lost interest (30% of cases) by the time they were called for the interviews. 39  Panel A of Appendix Table A6 explores the determinants of compliance, and shows very little evidence of selection on observables. 40 Importantly, Treatment does not predict the likelihood of the job interview taking place. This is not surprising, as the certificates were shown to firms and workers only conditional on the job interview taking place. Consistently with this, the Online Appendix confirms that the sample of job interviews that took place remains balanced on the main observable worker and firm characteristics. All the Treatment workers who showed up to the job interviews were given the certificates (corresponding to 49% of Treatment workers). The remaining Treatment certificates were disbursed to the workers shortly after the first worker follow-up survey. So by the second follow-up survey about 81% of Treatment workers had received the certificate. 41  oving on to attrition, the follow-up surveys targeted all firms and workers in the experimental sample, irrespective of whether the scheduled job interviews took place or not. We have very moderate attrition rates: these are about 12% in the firm follow-up, and about 14% in both worker follow-ups. 42  Panel B of Appendix Table A6 shows that attrition is not related to Treatment in either sample, and there is also very little evidence of observable characteristics determining attrition. Panel B of Appendix Table A5 .1 and Panels B and C of Table A5 .2 confirm that the samples of both workers and firms remain balanced on baseline characteristics at follow-up, so that attrition is not likely to affect the validity of the initial random assignment. 43 Therefore, we do not correct for attrition in our main regression specifications. 44   only one firm, so possible recall errors related to the respondent getting confused about the different job interviews are lower on the worker side; (ii) in 13% of the cases, the person that answered the firm follow-up survey is different from the owner that conducted the job interviews. Results using corresponding match-level information from the firm follow-up survey (not reported) are qualitatively similar.
---

Let's think through what this paragraph tells us about the study's adherence, attrition, or compliance. First, we find out that of the 1,230 scheduled job interviews, only 515, or 42% took place. Then, we find out that all the treatment workers who showed up to job interviews were given certificates, which corresponds to 49% of treatment workers. Finally, by the second follow-up survey, 81% of the workers had received the certificate. This tells us about attrition, i.e., adherence.

These figures describe both how much and how well participants in the study complied with the study's protocol.

Conclusion: Yes, this paragraph does tell us about adherence, attrition, or compliance for the intervention.

Second, consider this paragraph from a paper studying relaxation and park walking during lunch breaks.

```
 Lunch breaks constitute the longest within-workday rest period, but it is unclear how they affect recovery from job stress. We conducted two randomized controlled trials with 153 Finnish knowledge workers who engaged for 15 minutes daily in prescribed lunch break activities for ten consecutive working days. Participants were randomly assigned to a: 1) park walking group (N = 51), 2) relaxation exercises group (N = 46) and 3) control group (N = 56). The study was divided into two parts scheduled in spring (N = 83) and fall (N = 70). Recovery experiences (detachment, relaxation, enjoyment) and recovery outcomes (restoration, fatigue, job satisfaction) were assessed with SMS and paper-and-pencil questionnaires several times per day before, during and after the intervention period. A manipulation check revealed that both intervention groups reported less tension after lunch breaks during the intervention than before. In spring, the interventions did hardly affect recovery experiences and outcomes. In fall, restoration increased and fatigue decreased markedly immediately after lunch breaks and in the afternoon in both intervention groups (d = 0.22-0.58) and most consistent positive effects across the day were reported by the park walking group. Park walks and relaxation exercises during lunch breaks can enhance knowledge workers' recovery from work, but effects seem weak, short-lived and dependent on the season.
```

Let's think through what this paragraph tells us about the study's adherence, attrition, or compliance. First, we find out that 51 participants were assigned to the park walking group, 46 to the relaxation exercises group, and 3 to the control group, and that the study was divided into two parts, a spring (n=83) and fall (n=70) group. This is simply information about the size of the sample and its allocation to different treatment arms; it tells us nothing about whether participants in these groups actually completed the intervention. For that, we would need to know, for example, how often those in the park walking group actually took walks in the park during their lunch breaks. Second, we find out that there was increased restoration and decreased fatigue (d=0.22-0.58) in both intervention groups in the fall. This is about the results of the study (what happened to the participants), not simply about how well they adhered to the intervention protocol.

These figures describe the size of the sample and the results of the study, but not how well participants adhered to the study's plan.

Conclusion: No, this paragraph does not tell us about adherence, attrition, or compliance for the intervention.

Third, consider this paragraph from a paper studying albendazole:

---
A somewhat lower proportion of pupils in school took the medicine in 1999. Among girls younger than thirteen and boys who were enrolled in school for at least part of the 1999 school year, the overall treatment rate was approximately 72 percent (73 percent in Group 1 and 71 percent in Group 2 schools), suggesting that the process of selection into treatment was fairly similar in the two years despite the change in consent rules. Of course, measured relative to the baseline population of students enrolled in early 1998, a smaller percentage of students were still in school in 1999 and hence, treatment rates in this baseline sample were considerably lower in 1999 than in 1998: among girls under thirteen years of age and all boys in treatment schools from the baseline sample, approximately 57 percent received medical treatment at some point in 1999, while only nine percent of the girls thirteen years of age and older received treatment. 17  nly five percent of comparison school pupils received medical treatment for worms independently of the program during the previous year, according to the 1999 pupil questionnaire. 18  An anthropological study examining worm treatment practices in a neighboring district in Kenya (Geissler et al. (2000)), finds that children self-treat the symptoms of helminth infections with local herbs, but found no case in which a child or parent purchased deworming 17 The difference between the 72 percent and 57 percent figures is due to Group 2 pupils who dropped out of school (or who could not be matched in the data cross years, despite the efforts of the NGO field staff) between years 1 and 2 of the project. Below, we compare infection outcomes for pupils who participated in the 1999 parasitological survey, all of whom were enrolled in school in 1999. Thus the parasitological survey sample consists of pupils enrolled in school in both 1998 and 1999 for both the treatment and comparison schools. To the extent that the deworming program itself affected enrolment outcomes-1999 school enrolment is approximately four percentage points higher in the treatment schools than the comparison schools-the pupils enrolled in the treatment versus comparison schools in 1999 will have different characteristics. However, since drop-out rates were lower in the treatment schools, this is likely to lead to a bias toward zero in the within-school health externality estimates, in which case our estimates serve as lower bounds on true within-school effects.
---

Let's think through what this paragraph tells us about the study's adherence, attrition, or compliance. The treatment rate among was approximately 72 percent in 1999. Is this a percentage of the participants in the study? It's not clear from this paragraph alone; we need more context. Similarly, we find that only five percent of comparison school pupils received medical treatment for worms independently of the program during the previous school year. This could be about adherence, but it could also be describing the results of the intervention. We would need a longer description of the study to find out.

Conclusion: Unclear; we don't know whether this paragraph tells us about adherence, attrition, or compliance for the intervention.

Fourth, consider this paragraph from a paper studying {intervention.strip()}:

---
{paragraph.strip()}
---

Let's think through what this paragraph tells us about the study's adherence, attrition, or compliance.""".strip()


def this_or_other_study_prompt(paragraph: str, intervention: str):
    return f"""
From the textbook, "Critically Evaluating Interventional Studies," Chapter 3:

When evaluating the quality of a randomized controlled trial, you should also consider whether any participants dropped out of the study or failed to follow its protocols correctly. This is sometimes called "adherence" or "compliance". If too many participants failed to receive the intervention or failed to receive it correctly, for whatever reason, this may damage the internal validity of the study's results.

Unfortunately, papers are often not as clear as they should be when discussing adherence. Sometimes it can be tricky to tell whether the author is talking about the adherence/compliance with the study's own protocols versus simply discussing the adherence or compliance of a related work.

Let's look at five examples of paragraphs from papers that discuss adherence or compliance to decide whether they are describing adherence or compliance for the author's own study versus adherence/compliance of a different study or a related work. Usually, when the adherence or compliance being discussed belongs to a different study, that study is cited explicitly. If another study is not cited explicitly, you can assume that the adherence/compliance rate being discussed belongs to the author's own study.

For each paragraph, we'll conclude either that Yes, the adherence/compliance being discussed probably belongs to the author's own study, or No, that it probably belongs to a different study.

First, consider this paragraph from a paper studying the Preschool Situational Self-Regulation Toolkit (PRSIST) Program:

---
All children in their final prior-to-school year in these centers, who attended at least one of the 1-2 assessment days, were invited to participate in this study. There were no further exclusion criteria. Parental consent to participate was provided for 547 3-5-year old children, all of whom were identified as likely to be attending school in the subsequent year. The flow of participants throughout the study is depicted in Figure 1 . At baseline, 473 of these children were assessed (86.5%), with non-participation largely due to absence on the day of assessment. The mean age of this sample was 4.44 years (SD = 0.38, range = 3.20-5.33), with a relative balance of boys and girls (48.2% girls). Children who were identified as of Aboriginal or Torres Strait Islander descent comprised 7.2% of the sample, which is in line with population estimates for this age group (Australian Institute of Health and Welfare (AIHW), 2012). Family income was diverse: 11.9% of families qualified for full childcare benefit subsidies (low income); 65.5% of families qualified for some childcare benefit (low-middle to middle-high income); and 22.7% of families did not qualify for any childcare benefit subsidy (high income). Maternal education levels were also diverse: 9.5% did not complete high school; 9.3% completed only high school; 30.6% had completed a diploma, trade, certificate; 34.6% completed a tertiary degree; and 16.0% a post-graduate qualification. At follow-up, 426 children were assessed, which corresponded to a 90.1% retention rate. Nonparticipation at follow-up was due to the child having left the center or absence on the day of assessment.
---

Let's think through whether this paragraph describes adherence for the study in question or another study: When describing nonparticipation rates, the text does not contain any citations to related works. Further, these details are also shown in Figure 1, strongly suggesting that the adherence/compliance rate being discussed belongs to the author's own study.

Conclusion: Yes, the adherence/compliance being discussed probably belongs to the author's own study.

Second, consider this paragraph from a paper studying DDUGKY skills training programs:

---
In the Indian context, we were unable to find studies that have estimated the impact of youth skills training programs sponsored by the government. Although not offered by the government, an experimental study designed by Maitra and Mani (2017) and implemented in co-operation with non-governmental organizations offers estimates of the impact of a 6-month stitching and tailoring training program targeted at young women (aged 18-39 years) in New Delhi. The paper examined the 5 The youth training employment programs (Joven) in Latin America were initiated in Chile in 1991, and thereafter, similar programs have been implemented in Argentina, Colombia, Peru, and Uruguay. The various programs target youth from low-income families, with low educational attainment, and with limited or no job experience. The programs consist of basic literacy, training in a trade which is in demand, work experience, and help finding a job. Typically, the intervention lasts for 6 months and includes 200-400 h of training and 2-3 months of work experience. 6  Other experimental evaluations of vocational training program in developing countries include Acevedo et al. (2017) for the Dominican Republic, Attanasio et al. (2017) for Columbia, Maitra and Mani (2017) for India, Diaz and Rosas (2016) for Peru, Honorati (2015) for Kenya. 7  Although their paper does not focus on disadvantaged youth but on the general unemployed population, Hirshleifer et al. (2016) use a randomised experiment to assess the effect of a large-scale vocational training program in Turkey and conclude that the effect of being assigned to training had a 2 percentage point, but statistically not significant effect on the probability of being employed. impact of the program 6 months and 18 months after program completion on a sample of 594 women (409 treatment and 185 control). According to the study's findings, in the short term, women who received training were 4 percentage points more likely to be self-employed, 6 percentage points more likely to be employed and earn 150% more per month as compared to the control group. The effects persisted in the medium term. While the effects are impressive, the authors report that only 56% of those assigned to treatment completed the course and that there were a number of barriers to entry, chiefly, lack of access to credit, lack of child-care support and the distance from residence to the training center.
---

Let's think through whether this paragraph describes adherence for the study in question or another study: When describing how only 56% of those assigned to treatment completed the course, the authors are reporting the findings from an experiment in Hirshleifer et al. (2016). This means that the adherence/compliance being discussed belongs to that study, not the author's own study.

Conclusion: No, the adherence/compliance being discussed probably belongs to a different study.

Third, consider this paragraph from a paper studying {intervention.strip()}:

---
{paragraph.strip()}
---

Let's think through whether this paragraph describes adherence for the study in question or another study:

""".strip()


class AnswerWithReasoning(BaseModel):
    paragraph: str
    reasoning: str
    answer: str
    token_usage: int


@trace
async def intervention_classification_answer_with_reasoning(
    paragraph: str,
    intervention: str,
    temperature: float,
    cache_id: int = 0,
):
    """Sample reasoning and a final answer for the classification prompt, asking
    "Does this paragraph contain information about adherence, compliance, or attrition?"
    """
    cache_id  # unused
    response = await openai_complete(
        prompt=intervention_classification_prompt(paragraph, intervention),
        temperature=temperature,
        max_tokens=657,
        stop=("\nFifth,", "\nFinally,"),
        top_p=1,
        cache_id=cache_id,
    )
    response_text = response["choices"][0]["text"]
    token_usage = response["usage"]["total_tokens"]
    if "Conclusion: " in response_text:
        reasoning, answer_text = response_text.split("Conclusion:")
        return AnswerWithReasoning(
            paragraph=paragraph,
            reasoning=reasoning.strip(),
            answer=answer_text.strip(),
            token_usage=token_usage,
        )
    log.warning(
        "Unexpected response in intervention classification",
        response=response,
        paragraph=paragraph,
    )
    print("Unexpected response:", response)
    return AnswerWithReasoning(
        paragraph=paragraph,
        reasoning=response_text.strip(),
        answer="",
        token_usage=token_usage,
    )


@trace
async def this_or_other_classification_answer_with_reasoning(
    paragraph: str,
    intervention: str,
    temperature: float,
    cache_id: int = 0,
):
    """Sample reasoning and a final answer for the classification prompt,
    asking, "Is this paragraph about adherence about a related work or
    the study this paper is reporting on?"
    """
    response = await openai_complete(
        prompt=this_or_other_study_prompt(paragraph, intervention),
        temperature=temperature,
        max_tokens=768,
        stop=("\nFourth,", "\nFinally,", "\n\nNow,"),
        top_p=1,
        cache_id=cache_id,
    )
    response_text = response["choices"][0]["text"]
    token_usage = response["usage"]["total_tokens"]
    if "Conclusion: " in response_text:
        reasoning, answer_text = response_text.split("Conclusion:")
        return AnswerWithReasoning(
            paragraph=paragraph,
            reasoning=reasoning.strip(),
            answer=answer_text.strip(),
            token_usage=token_usage,
        )
    log.warning(
        "Unexpected response in this or other classification",
        response=response,
        paragraph=paragraph,
    )
    print("Unexpected response:", response)
    return AnswerWithReasoning(
        paragraph=paragraph,
        reasoning=response_text.strip(),
        answer="",
        token_usage=token_usage,
    )


def answer_has_prefix(answer: AnswerWithReasoning, prefix: str):
    return answer.answer.lower().startswith(prefix.lower())


async def majority_vote(
    answers: list[AnswerWithReasoning],
    candidate_prefixes: tuple[str, ...] = ("Yes", "No", "Unclear"),
):
    votes: Counter[str] = Counter()
    for answer in answers:
        for prefix in candidate_prefixes:
            if answer_has_prefix(answer, prefix):
                votes[prefix] += 1
                break
    return votes.most_common(1)[0][0]


def prompt_from_reasoning(
    prompt_function: Callable[[str, str], str],
    *,
    paragraph: str,
    intervention: str,
    reasoning: str,
):
    prefix = prompt_function(paragraph, intervention)
    return f"""{ prefix } { reasoning }

Conclusion: """.strip()


@trace
async def zero_temp_final_classification(prompt: str):
    """Perform a final classification step using a reasoning
    selected from the sampled classifications."""
    return await openai_complete(
        prompt=prompt,
        stop=("\n"),
    )


@trace
async def adherence_paragraph_classification(
    selection_function: Callable[
        [str, str, float, int], Awaitable[AnswerWithReasoning]
    ],
    prompt_function: Callable[[str, str], str],
    *,
    paragraph: str,
    intervention: str,
):
    """Using the selection and prompt functions provided,
    complete the classification task by chain-of-thought reasoning,
    high-temperature sampling, plurality voting, and zero-temperature
    generation of the final classification.
    """
    answers = [
        (
            await selection_function(
                paragraph,
                intervention,
                0.4,
                cache_id,
            )
        )
        for cache_id in range(10, 20)
    ]
    total_token_usage = sum(answer.token_usage for answer in answers)
    print(f"Total token usage: {total_token_usage}")
    most_common_prefix = await majority_vote(
        answers, candidate_prefixes=("Yes", "No", "Unclear")
    )

    answers_with_most_common_prefix = [
        a for a in answers if answer_has_prefix(a, most_common_prefix)
    ]

    if not answers_with_most_common_prefix:
        # just use the longest reasoning
        best_reasoning = max(answers, key=lambda a: len(a.reasoning))

    else:
        best_reasoning = max(
            answers_with_most_common_prefix, key=lambda a: len(a.reasoning)
        )

    zero_temp_answer = await zero_temp_final_classification(
        prompt_from_reasoning(
            prompt_function,
            paragraph=paragraph,
            intervention=intervention,
            reasoning=best_reasoning.reasoning,
        )
    )

    token_usage = zero_temp_answer["usage"]["total_tokens"]

    return AnswerWithReasoning(
        paragraph=paragraph,
        reasoning=best_reasoning.reasoning,
        answer=zero_temp_answer["choices"][0]["text"].strip(),
        token_usage=total_token_usage + token_usage,
    )


TFEW_ADHERENCE_ANSWER_CHOICES = ("no", "yes")


def make_multiple_adherence_prompts(
    context: str, section: str, sentence: str
) -> list[tuple[str, tuple[str, str]]]:
    prompts = [
        f"Context: { context }\n\nSection: { section }\n\nAnswer yes if the following sentence is about how many participants in the study complied with the study's protocol, had to drop out, or withdrew; answer no if it is about something else, such as the study's design, sampling strategy, or results.\n\nSentence: { sentence }",
        f'Context: { context }\n\nQuestion: Does "{ sentence }" describe how many people eligible for the intervention actually completed it or failed to complete it?\nOptions:\nA. Yes, "{ sentence }" describes how many people actually completed or failed to complete the intervention.\nB. No, "{ sentence }" does not describe how many people completed or failed to complete the intervention.',
        f'Context: { context }\n\nQuestion: Is "{ sentence }" about the actual adherence or dropout rate of the study? True, False, or Neither?',
        f"Does the following sentence from a research paper describe how many participants dropped out of or withdrew from the study?\n\nSection: { section }\nSentence: { sentence }",
        f"Does the following sentence from a research paper describe how many participants dropped out of or withdrew from the study?\n\nSection: { section }\nSentence: { sentence }",
    ]
    prompts = [prompt.strip() for prompt in prompts]
    choices: list[tuple[str, str]] = [
        ("no", "yes"),
        ("B", "A"),
        ("False", "True"),
        ("no", "yes"),
        ("no", "yes"),
    ]
    return [(prompt, choice) for prompt, choice in zip(prompts, choices)]


@trace
async def adherence_regex(sentence: str, level: int = 0) -> bool:
    """Simple regex for adherence-related English language patterns."""
    if level == 0:
        pattern = r"\b(adherence|Adherence|had to be excluded|were excluded|had to drop out|dropped out)\b"
    elif level == 1:
        pattern = r"\b(withdrew|did not complete the)\b"
    elif level == 2:
        pattern = r"\b(was omitted from|complied with)\b"
    else:
        raise ValueError(f"Invalid level: { level }")
    answer = re.search(pattern, sentence) is not None
    return answer


def remove_worst_paragraph(paragraphs: list[str], ranked_paragraphs: list[str]):
    overlap = [paragraph for paragraph in ranked_paragraphs if paragraph in paragraphs]
    return [
        paragraph
        for paragraph in paragraphs
        if paragraph in overlap[: len(paragraphs) - 1]
    ]


class AdherenceTfewSettings(BaseSettings):
    qa_model = "adherence-tfew-multi"
    backup_search_model = "mono-t5"


class AdherenceParagraphTfew(Recipe):
    defaults = lambda self: AdherenceTfewSettings()  # noqa: E731

    async def is_possibly_adherence_sentence(
        self, *, sentence: str, context: str, section: str
    ) -> bool:
        """Detect whether a sentence is possibly related to adherence, using up to 5 prompts."""
        for prompt, choice_inputs in make_multiple_adherence_prompts(
            context=context, section=section, sentence=sentence
        ):
            choice_probs, _ = await self.agent(self.s.qa_model).classify(
                prompt=prompt, choices=choice_inputs
            )
            choice, _ = max_by_value(choice_probs)
            if choice == choice_inputs[1]:
                return True
        return False

    async def is_possibly_adherence_paragraph(self, paragraph: Paragraph) -> bool:
        """Detect whether a paragraph is possibly related to adherence,
        by checking whether any of its sentences are possibly adherence-related,
        supplemented by regex."""
        for sentence in paragraph.sentences:
            is_adherence_sentence = await self.is_possibly_adherence_sentence(
                sentence=sentence,
                context=str(paragraph),
                section=paragraph.sections[0].title if paragraph.sections else "",
            )
            if is_adherence_sentence:
                return True
        return await adherence_regex(str(paragraph), 0)

    async def rank_paragraphs_by_adherence(
        self, paragraphs: list[Paragraph]
    ) -> list[tuple[Paragraph, float]]:
        """Score all paragraphs by their probability of being about adherence.
        These ranks will be used when we have to shorten prompts or where
        nothing in particular seems to be much about adherence."""

        async def score_paragraph(paragraph: Paragraph) -> float:
            return await self.agent(self.s.backup_search_model).relevance(
                question="How many participants actually received the intervention?",
                context=str(paragraph),
            )

        scores = await map_async(paragraphs, score_paragraph)
        ranked_paragraphs = {
            paragraph: score
            for score, paragraph in sorted(
                zip(scores, paragraphs), reverse=True, key=lambda sp: sp[0]
            )
        }
        return list(ranked_paragraphs.items())

    async def top_n_paragraphs_of_possible_adherence_paragraphs(
        self,
        possible_adherence_paragraphs: list[Paragraph],
        ranked_paragraphs: list[tuple[Paragraph, float]],
        n: int,
    ) -> list[Paragraph]:
        """Shorten the list of paragraphs by keeping the paragraphs
        most likely to be about adherence.
        """
        ranked_paragraphs_dict = dict(ranked_paragraphs)
        top_n_adherence_paragraphs = set(
            [
                paragraph
                for paragraph in ranked_paragraphs_dict
                if paragraph in possible_adherence_paragraphs
            ][:n]
        )
        # maintain input order
        return [
            paragraph
            for paragraph in possible_adherence_paragraphs
            if paragraph in top_n_adherence_paragraphs
        ]

    async def adherence_paragraphs_recall(
        self,
        paragraphs: list[Paragraph],
        record=recorder,
    ) -> list[Paragraph]:
        """Collect paragraphs that may be about adherence.
        Err on the side of high recall.
        """

        possible_adherence_paragraphs = await filter_async(
            paragraphs, self.is_possibly_adherence_paragraph
        )

        if not possible_adherence_paragraphs:
            for level in range(0, 3):
                possible_adherence_paragraphs = [
                    paragraph
                    for paragraph in paragraphs
                    if (await adherence_regex(str(paragraph), level))
                ]
                if possible_adherence_paragraphs:
                    break

        ranked_paragraphs = await self.rank_paragraphs_by_adherence(paragraphs)

        top_2_ranked_paragraphs = (
            await self.top_n_paragraphs_of_possible_adherence_paragraphs(
                paragraphs, ranked_paragraphs, 2
            )
        )

        combined_adherence_paragraphs = [
            paragraph
            for paragraph in paragraphs
            if paragraph in possible_adherence_paragraphs
            or paragraph in top_2_ranked_paragraphs
        ]

        NO_MORE_THAN_N_PARAGRAPHS = 6

        if len(combined_adherence_paragraphs) > NO_MORE_THAN_N_PARAGRAPHS:
            top_n_combined_adherence_paragraphs = (
                await self.top_n_paragraphs_of_possible_adherence_paragraphs(
                    combined_adherence_paragraphs,
                    ranked_paragraphs,
                    NO_MORE_THAN_N_PARAGRAPHS,
                )
            )
            record(
                info=f"Found more than {NO_MORE_THAN_N_PARAGRAPHS} paragraphs, shortening by ranks",
                classified_paragraphs=possible_adherence_paragraphs,
                top_n_ranked=top_n_combined_adherence_paragraphs,
            )
            combined_adherence_paragraphs = top_n_combined_adherence_paragraphs

        return combined_adherence_paragraphs

    async def adherence_paragraphs(
        self, paragraphs: list[Paragraph], intervention: str
    ) -> list[Paragraph]:
        """Collect paragraphs that may be about adherence,
        combining a high-recall search with a high-precision refinement
        step.
        """
        possible_adherence_paragraphs = await self.adherence_paragraphs_recall(
            paragraphs
        )

        async def is_really_adherence(paragraph: Paragraph) -> AnswerWithReasoning:
            return await adherence_paragraph_classification(
                intervention_classification_answer_with_reasoning,
                intervention_classification_prompt,
                paragraph=str(paragraph),
                intervention=intervention,
            )

        classification_answers = await map_async(
            possible_adherence_paragraphs, is_really_adherence
        )

        return [
            paragraph
            for paragraph, answer in zip(
                possible_adherence_paragraphs, classification_answers
            )
            if answer_has_prefix(answer, "Yes") or "adherence" in str(paragraph).lower()
        ]

    async def adherence_paragraphs_this_study(
        self, paragraphs: list[Paragraph], intervention: str
    ) -> list[Paragraph]:
        """For paragraphs that we know are about adherence, which
        are about adherence of a *related work* and not this paper?"""
        really_adherence_paragraphs = await self.adherence_paragraphs(
            paragraphs, intervention
        )

        async def is_adherence_this_study(paragraph: Paragraph) -> AnswerWithReasoning:
            return await adherence_paragraph_classification(
                this_or_other_classification_answer_with_reasoning,
                this_or_other_study_prompt,
                paragraph=str(paragraph),
                intervention=intervention,
            )

        classification_answers = await map_async(
            really_adherence_paragraphs, is_adherence_this_study
        )

        return [
            paragraph
            for paragraph, answer in zip(
                really_adherence_paragraphs, classification_answers
            )
            if answer_has_prefix(answer, "Yes")
        ]

    async def adherence_description(
        self, paragraphs: list[Paragraph], intervention: str
    ) -> tuple[str, list[Paragraph]]:
        """Describe the adherence, compliance, or attrition that occurred in this study,
        for this intervention."""
        ranked_paragraphs = await self.rank_paragraphs_by_adherence(paragraphs)
        ranked_paragraphs_dict = dict(ranked_paragraphs)
        adherence_paragraphs_this_study = await self.adherence_paragraphs_this_study(
            paragraphs, intervention
        )

        if not adherence_paragraphs_this_study:
            return "Unclear", adherence_paragraphs_this_study

        return (
            await final_answer_with_reasoning(
                [str(p) for p in adherence_paragraphs_this_study],
                intervention,
                [str(p) for p in list(ranked_paragraphs_dict.keys())],
            )
        ).answer, adherence_paragraphs_this_study

    async def list_experiments(
        self, document_id: str, question_short_name: str = "adherence"
    ):
        return list_experiments(
            document_id=document_id, question_short_name=question_short_name
        )

    async def run(self, paper: Paper):
        results = []

        for intervention in await self.list_experiments(paper.document_id):
            answer, excerpts = await self.adherence_description(
                paper.paragraphs, intervention
            )

            recipe_result = RecipeResult(
                document_id=paper.document_id,
                question_short_name="adherence",
                result=(answer, excerpts),
                answer=answer,
                excerpts=[str(excerpt) for excerpt in excerpts],
                experiment=intervention,
                classifcation_eq=(classification_eq_adherence,),
                classification=(
                    "Unclear"
                    if not excerpts or "unclear" in answer.lower()
                    else "found"
                ),
            )

            results.append(recipe_result)

        self.maybe_add_to_results(results)
        return results


AdherenceClassification = Literal["explicit", "implicit", "missing"]


def classification_eq_adherence(
    prediction: Optional[str],
    gold: Optional[AdherenceClassification],
) -> Optional[bool]:
    if gold is None or gold == "implicit":
        return None
    if gold not in ["explicit", "missing"]:
        return None
    if prediction is None:
        return None
    if prediction.strip().lower().startswith("unclear"):
        return gold == "missing"
    else:
        return gold == "explicit"
