from typing import Tuple
from ice.apis.openai import openai_complete
from ice.evaluation.evaluate_recipe_result import RecipeResult
from ice.paper import Paper
from ice.recipe import Recipe
from ice.settings import settings
from pydantic import BaseSettings
from structlog import get_logger
from transformers.models.auto.tokenization_auto import AutoTokenizer
from transformers.models.gpt2.tokenization_gpt2_fast import GPT2TokenizerFast
from ice.utils import filter_async
import re
from ..trace import recorder, trace

log = get_logger()


TFEW_SAMPLE_SIZE_ANSWER_CHOICES = ("false", "true")

MAX_POPULATIONS = 2

VAL_GS = ['agley-2021.pdf', 'bloom-2016.pdf', 'caturla-2011.pdf', 'choopanya-2013.pdf', 'fleming-1986.pdf', 'haugen-2014.pdf', 'howard-2020.pdf', 'sagara-2009.pdf', 'shen-2016.pdf', 'tergesen-2020.pdf', 'winskell-2018.pdf']

TEST_GS = ['arifeen-2012.pdf', 'bigira-2014.pdf', 'black-1990.pdf', 'boer-2004.pdf', 'bryant-2021.pdf', 'bures-2016.pdf', 'ebner-2016.pdf', 'fisker-2014.pdf', 'gosling-2009.pdf', 'grover-2020.pdf', 'himmelmann-1996.pdf', 'lauque-2000.pdf', 'liu-2013.pdf', 'matsumoto-2020.pdf', 'mullany-2006.pdf', 'ross-1993.pdf', 'sudhakar-2021.pdf', 'sullivan-2009.pdf', 'tricker-1996.pdf', 'wirz-2011.pdf']

gpt2_tokenizer: GPT2TokenizerFast = AutoTokenizer.from_pretrained("gpt2")

def n_tokens(prompt: str) -> int:
    tokenized = gpt2_tokenizer(prompt)
    return len(tokenized.input_ids)

def make_prompt_monot5(paragraph: str) -> str:
    # Prompt for FTed mono-T5; do not change without retraining the model.
    prompt = f"""Query: What is the sample size of this study? Document: {paragraph} Relevant:"""
    return prompt

def make_populations_prompt(abstract: str) -> str:
    return f"""Below is an abstract from a randomized control trial(RCT)

Abstract: Glucomannan is a water-soluble dietary fiber derived from the root of Amorphophallus konjac that can improve blood sugar, blood fat concentration, and weight management, and has other health benefits. The aim of this study is to investigate the effect of glucomannan noodles on components of the metabolic syndrome. A randomized, double-blind, placebo-controlled, crossover study, 32 individuals with metabolic syndrome were received a daily servings of 400 gram glucomannan noodles for a period of four weeks. After two weeks of wash out period, they received a placebo noodles for four weeks. There were no statistical difference in calories, carbohydrate, protein, fat and dietary fiber intake from 24 h food recalls between glucomannan noodles and placebo noodles groups. However, the body weight, body mass index, and waist circumference had significantly decreased after 4-week intervention in both groups, but high sensitivity C-reactive protein was lowered only in glucomannan noodles group. Moreover, the 24 individuals with type 2 diabetes had significantly decreased body weight, BMI, waist circumference, hs-CRP, and glycated hemoglobin after glucomannan noodles intervention. The rest of lipid profile, fasting blood glucose, insulin, and HOMA-IR of the subjects did not show any significant difference. This study showed that glucomannan noodles as a staple food can contribute to metabolic syndrome in adults predisposed to type 2 diabetes.

List briefly the primary population(s) that were included in this study. ALL population(s) should be mutually exclusive and be the primary population(s) that were included in this study.

-Individuals with metabolic syndrome

Below is an abstract from a randomized control trial(RCT)

Abstract: Objective To assess the impact of increasing incentive size and reminder calls on the measles vaccine uptake rate. Design Randomized controlled trial, randomized at individual level, stratified by clinic. Setting Nigeria Participants 1088 caregivers with children aged nine months or older; had received at least one previous conditional cash transfer (CCT) at a program clinic, had received their Penta-3 immunization but had not yet received their measles immunization, and the caregiver had provided a phone number. Intervention Nine clinics were randomized to two models; caregivers in Model 1 received a default of 2000 Nigerian Naira (NGN) for completing the measles vaccine, and those in Model 2 received by 3000 NGN. Caregivers from the respective clinics were then randomized to one of the four arms: 1) control (baseline amount of 2000 NGN or 3000 NGN), 2) baseline amount plus a reminder call, 3) baseline amount plus 1000 NGN and a reminder call, and 4) baseline amount plus 3000 NGN and a reminder call. Main outcome measure Receipt of measles vaccine as reported on a child health card. Results Overall, there was no clear trend that increasing the incentive amount resulted in an increase in vaccine uptake rates. In Model 1 households, an additional 1000 NGN and 3000 NGN resulted in a 6.4 percentage point (95% CI: -2.3–15, p-value = 0.15) and 11.8 percentage point (95% CI: 3.9–19.6, p-value = 0.003) increase in the probability of completing the measles vaccines, respectively. This increase, however, was only significant for the 3000 NGN increase. On the other hand, in Model 2 households, increasing the incentive by 1000 NGN and 3000 NGN increased the probability by 3.3 (95% CI: -3.8–10.4, p-value = 0.36) and 3.3 (95% CI: -3.7–10.4, p-value = 0.35) percentage points. These increases were not statistically significant. Adding reminder calls to CCTs increased the probability of completing the measles vaccine; caregivers who received reminder calls plus CCTs were 5.1 percentage points more likely to get their children vaccinated (95% CI: 0.50–9.8, p-value = 0.03) compared to those who received CCTs and did not receive a reminder call. These results were largely driven by caregivers who went to clinics in Model 1. Conclusion A combination of increasing incentive amounts and reminder calls modestly improves measles immunization rates. However, this program also shows that there is substantial regional heterogeneity in response to both incentives and calls. While one possible conclusion is that a larger incentive and phone reminders are more likely to work in higher income and higher baseline coverage settings, the study is not designed to evaluate this claim. Rather, policymakers could consider experimenting with a similar low-cost calling study as part of the design of other cash transfer programs to identify whether adding reminder phone calls could increase the impact of the program.

List briefly the primary population(s) that were included in this study. ALL population(s) should be mutually exclusive and be the primary population(s) that were included in this study.

-Caregivers 

Below is an abstract from a randomized control trial(RCT)

Abstract: Results of a randomised controlled trial testing the EFFect Of Running Therapy on Depression.BackgroundThis randomised controlled trial explored the anti-depressive and health effects of add-on exercise (running therapy or Nordic walking) in patients with Major Depressive Disorder (MDD). MethodsPatients were recruited at three specialised mental health care institutions. In the intervention group exercise was planned two times a week during 6 months, the control group received care as usual. Observer-blinded measurements included Hamilton-17 depression scores and several health and fitness parameters. Submaximal bicycle-tests were performed at inclusion, 3, 6 and 12 months. The effects of exercise were assessed by effect size, intention-to-treat and analysis per protocol using General Linear Models (GLM) with time x group interactions.ResultsIn total, 183 patients were assessed for eligibility and 135 were excluded (40% of the potential participants declined to participate mainly due to a lack of time and motivation). Together with a drop-out of 55% at 6 months, this reduced the power of the study severely. As a result, statistical analysis was performed only on the first 3 months of the study. Data were ultimately analysed from 46 patients, of which 24 were in the intervention group. Significantly more women were in the intervention group, and depression and fitness were higher in the control group. Participants showed 2–3 points less depression on average after 3 months. However, the GLM showed no effect on depression (Cohen’s d < 0.2, F = .13, p = .73) in both the intention-to-treat and per protocol analyses. However, large effect sizes (Cohen’s d > 0.8) were found for aerobic capacity (VO2max∙.kg− 1, F = 7.1, p = .02*), maximal external output (Wmax∙.kg− 1, F = 6.1, p = .03*), and Body Mass Index (F = 5, p = .04*), in favour of the intervention group.ConclusionsIn this selective and relative small clinical population with MDD, an anti-depressive effect of the exercise intervention could not be measured and is also unlikely due to the very low effect size. An integrated lifestyle intervention will probably be more effective than a single add-on exercise intervention. However, significantly increased fitness levels may contribute to the alleviation of current cardio-metabolic risk factors or prevention of these in the future.Trial registration: Netherlands Trial Register (NTR): NTR1894 on July 2nd 2009.

List briefly the primary population(s) that were included in this study. ALL population(s) should be mutually exclusive and be the primary population(s) that were included in this study.

-Patients with Major Depressive Disorder

Below is an abstract from a randomized control trial(RCT)

Abstract: Calorie restriction (CR) has been promoted to increase longevity. Previous studies have indicated that CR can negatively affect mood and therefore the effect of CR on mood and quality of life (QOL) becomes crucial when considering the feasibility of CR in humans. We conducted a three month clinical trial on CR (reduction of 300 to 500 kcal/day) combined with two days/week of Muslim sunnah fasting (FCR) to determine the effectiveness of FCR on QOL among aging men in Klang Valley, Malaysia. A total of 25 healthy Malay men (age 58.8±5.1 years), with no chronic diseases and a BMI of 23.0 to 29.9 kg/m2 were randomized to FCR (n=12) and control (n=13) groups. Body composition measurements and QOL questionnaires were ascertained at baseline, week 6 and week 12. QOL was measured using the Short-Form 36, sleep quality was determined using the Pittsburgh Sleep Quality Index, the Beck Depression Inventory II was used to measure mood and the Perceived Stress Scale was used to measure depression. The FCR group had a significant reduction in body weight, BMI, body fat percentage and depression (P<0.05). The energy component of QOL was significantly increased in FCR group (p<0.05). There were no significant changes in sleep quality and stress level between the groups as a result of the intervention. In conclusion, FCR resulted in body weight and fat loss and alleviated depression with some improvement in the QOL in our study and has the potential to be implemented on a wider scale.

List briefly the primary population(s) that were included in this study. ALL population(s) should be mutually exclusive and be the primary population(s) that were included in this study.

-Malay men

Below is an abstract from a randomized control trial(RCT)

Abstract: Caloric restriction has consistently been shown to extend life span and ameliorate aging-related diseases. These effects may be due to diet-induced reactive oxygen species acting to up-regulate sirtuins and related protective pathways, which research suggests may be partially inhibited by dietary anti-oxidant supplementation. Because caloric restriction is not sustainable long term for most humans, we investigated an alternative dietary approach, intermittent fasting (IF), which is proposed to act on similar biological pathways. We hypothesized that a modified IF diet, where participants maintain overall energy balance by alternating between days of fasting (25% of normal caloric intake) and feasting (175% of normal), would increase expression of genes associated with aging and reduce oxidative stress and that these effects would be suppressed by anti-oxidant supplementation. To assess the tolerability of the diet and to explore effects on biological mechanisms related to aging and metabolism, we recruited a cohort of 24 healthy individuals in a double-crossover, double-blinded, randomized clinical trial. Study participants underwent two 3-week treatment periods-IF and IF with anti-oxidant (vitamins C and E) supplementation. We found strict adherence to study-provided diets and that participants found the diet tolerable, with no adverse clinical findings or weight change. We detected a marginal increase (2.7%) in SIRT3 expression due to the IF diet, but no change in expression of other genes or oxidative stress markers analyzed. We also found that IF decreased plasma insulin levels (1.01 μU/mL). Although our study suggests that the IF dieting paradigm is acceptable in healthy individuals, additional research is needed to further assess the potential benefits and risks.

List briefly the primary population(s) that were included in this study. ALL population(s) should be mutually exclusive and be the primary population(s) that were included in this study.

-Healthy individuals 

Below is an abstract from a randomized control trial(RCT)

Abstract: {abstract}

List briefly the primary population(s) that were included in this study. ALL population(s) should be mutually exclusive and be the primary population(s) that were included in this study.

-"""


def extract_numbers(text: str) -> list[str]:
    # Only extracts numbers written in digits so that the int function can convert them to ints.
    words = text.split()

    number_strings = []
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

def answer_populations_question_with_reasoning(abstract: str, text: str, population: str) -> str:
    population = population.lower()
    population = population+" who participated in the study"
    return f"""A user on Statistics Stack Exchange needs help with this problem:

Use the excerpts from an academic paper to identify how many patients undergoing hemodialysis in an intervention completed the intervention and are included in the final analysis. Ignore irrelevant excerpts. 

Excerpts from paper: This randomized, placebo-controlled and double-blind trial was conducted on 151 patients on hemodialysis who were divided randomly by lottery method to three identical groups. In the intervention group, 250 mg of vitamin C was injected intravenously immediately at the end of each hemodialysis session three times a week for 8 weeks in a row. In the control group 1, same term of placebo saline was injected, and in the control group 2, no intervention was performed. Results: A total of 86 (61%) male and 55 female patients with mean hemodialysis duration of 39.74 ± 45.5 months, and a mean age of 61.36 ± 11.46 years-old, participated in this study. Hypertension and diabetes were the most common underlying diseases (79.4%). Median baseline CRP in the intervention, control 1 and control 2 groups were 16.8, 17.8, and 19.4 mg/L respectively. After 2 months, median CRP reduced significantly in the vitamin C group to 10.7 (P = 0.04) vs. 22.6, and 30.6 mg/L in control groups. Conclusions: Our findings demonstrated that vitamin C supplementation modifies the levels of CRP in patients on hemodialysis.
Of 152 randomized patients, 10 were excluded from the study due to transmission to other dialysis centers, being infected by active infections, getting cancers, death, or their own refusal, and only 141 patients completed the study.

Before giving your answer describe your reasoning(in the form "Reasoning:") in detail. Think about how many patients undergoing hemodialysis participated in the study. Explain in your reasoning(in the form "Reasoning:") how to deduce an answer the question "What is the final number of patients undergoing hemodialysis included in the analysis" from the relevant excerpts step by step. At the end of your reasoning, you MUST state your final answer in the form "Final answer:".

Answer format:
Reasoning: ...
Final answer: ...

The best response from Statistics Stack Exchange was the following:

Reasoning: 

Let’s think step by step.
The number of patients undergoing hemodialysis in final analysis is the number of participants who were enrolled in the study after removing the patients who were excluded, dropped out, failed to adhere to the study or otherwise failed to complete the study.
From "Of 152 randomized patients, 10 were excluded from the study due to transmission to other dialysis centers, being infected by active infections, getting cancers, death, or their own refusal, and only 141 patients completed the study." We know that there are 152 patients undergoing hemodialysis enrolled in the study. From the same excerpts, we know that 10 of them were excluded from the study. 
So 152 - 10 = 142 patients undergoing hemodialysis remained in the study. From "Of 152 randomized patients, 10 were excluded from the study due to transmission to other dialysis centers, being infected by active infections, getting cancers, death, or their own refusal, and only 141 patients completed the study." We know that 141 patients undergoing hemodialysis the study. So the number included in the final analysis is 141. 
Sanity check: 141 is smaller than 152 and 142.

Final answer: 141

A user on Statistics Stack Exchange needs help with this problem:

Use the excerpts from an academic paper to identify how many {population} in an intervention completed the intervention and are included in the final analysis. Ignore irrelevant excerpts. 

For additional context, the abstract from the paper is: {abstract}
Excerpts from paper: {text}

Before giving your answer describe your reasoning(in the form "Reasoning:") in detail. Think about how many {population} participated in the study. Explain in your reasoning(in the form "Reasoning:") how to deduce an answer the question "What is the final number of {population} included in the analysis" from the relevant excerpts step by step. At the end of your reasoning, you MUST state your final answer in the form "Final answer:".

Answer format:
Reasoning: ...
Final answer: ...

The best response from Statistics Stack Exchange was the following:

Reasoning:

Let’s think step by step."""

@trace
async def answer_with_reasoning(prompt: str, cache_id: int, temp=0.4) -> Tuple[str, int]:
    response = await openai_complete(
        prompt=prompt,
        temperature=temp,
        max_tokens=800,
        top_p=1,
        model="text-davinci-002",
        stop=None,
        cache_id=cache_id,
    )
    response_text = response["choices"][0]["text"]
    token_usage = response["usage"]["total_tokens"]
    answer = response_text.split("Final answer:")[1].strip().strip("\n") if "Final answer:" in response_text else ""
    log.info(f"GPT3 used {token_usage} tokens", final_answer=answer, full_response=response_text.strip())
    return answer, token_usage

@trace
async def get_best_answer(abstract: str, text: str, population: str):
    prompt = answer_populations_question_with_reasoning(abstract, text, population)
    answers = [(await answer_with_reasoning(prompt, cache_id=i)) for i in range(5)]
    total_token_usage = sum([t for _, t in answers])
    log.warn(f"Total token usage: {total_token_usage}")
    answers = [a for a, _ in answers]

    numbers_in_answers = [extract_numbers(a) for a in answers]

    def rank(numbers, number):
        r = 0
        for n in numbers:
            if number in n:
                r += 1
        return r

    scores = []

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

    answers = [(answer, score) for answer, score in zip(answers, scores)]
    answers.sort(key=lambda x: x[1], reverse=True)

    answers = [a for a, _ in answers]
    return answers[0]

def remove_citations(s: str) -> str:
    return re.sub(r"\s\([A-Z][a-z]+,\s[A-Z][a-z]?\.[^\)]*,\s\d{4}\)", "", s)

def remove_worst_paragraph(relevant_paragraphs: list) -> list:
    scores = [p[1] for p in relevant_paragraphs]
    relevant_paragraphs = [p for p in relevant_paragraphs if p[1] != min(scores)]
    return relevant_paragraphs

class FinalNSettings(BaseSettings):
    qa_model = "Final-N-monoT5"
    gpt_engine = "text-davinci-002"

class FinalN(Recipe):

    defaults = lambda self: FinalNSettings()

    @trace
    async def get_populations(self, abstract: str) -> list[str]:
        response = await openai_complete(
            stop=None,
            prompt=make_populations_prompt(abstract),
            temperature=0.0,
            max_tokens=200,
            top_p=1,
            model=self.s.gpt_engine,
        )
        response_text = response["choices"][0]["text"]
        token_usage = response["usage"]["total_tokens"]
        populations = response_text.strip("\n").split("\n-")
        populations = [p.strip() for p in populations if p.strip()]
        log.info(f"GPT3 used {token_usage} tokens", populations=populations)
        return populations

    @trace
    async def score_paragraph(self, paragraph: str) -> bool:
        output_dict, _ = await self.agent(self.s.qa_model).classify(
            prompt=make_prompt_monot5(paragraph),
            choices=TFEW_SAMPLE_SIZE_ANSWER_CHOICES,
        )
        choice, score = list(output_dict.keys())[0], list(output_dict.values())[0]
        score = (
            1 - score if choice == "false" else score
        )  # You could use the score with a threshold to determine if the paragraph is relevant.
        return choice == "true"

    @trace
    async def get_populations_numbers(
        self, relevant_paragraphs: list[str], populations: list[str], abstract: str
    ) -> list[str]:
        log.info("Number of relevant paragraphs", n=len(relevant_paragraphs))
        text = "\n".join([p[0] for p in relevant_paragraphs])
        while n_tokens(answer_populations_question_with_reasoning(abstract, text, "population")) > 3300:
            relevant_paragraphs = remove_worst_paragraph(relevant_paragraphs)
            log.info("Number of relevant paragraphs", n=len(relevant_paragraphs), tokens=n_tokens(answer_populations_question_with_reasoning(abstract, text, "population")))
            text = "\n".join([p[0] for p in relevant_paragraphs])
        log.info("GPT3 text")
        results = []
        for population in populations[:MAX_POPULATIONS]:
            answer = await get_best_answer(abstract, text, population)
            final_answer = population + ": " + answer
            results.append(final_answer)
        log.info(
            "GPT3 results",
            population_numbers="|".join(results),
        )
        return results

    
    @trace
    def retrieve_abstract(self, paper: Paper):
        abstract = ""
        for paragraph in paper.paragraphs:
            if paragraph.sections:
                if "abstract" in paragraph.sections[0].title.lower():
                    abstract += str(paragraph) + "\n\n"

        return abstract.strip()

    @trace
    async def get_answer(self, paper:Paper, results: list[str], relevant_paragraphs: list[str]) -> RecipeResult:
        total_population_size: int = 0
        for result in results:
            number_strings: list[str] = extract_numbers(result.split(": ")[1])
            number: str = (
                number_strings[0].replace(",", "").replace(" ", "")
                if number_strings
                else "0"
            )
            total_population_size += int(number)
        return RecipeResult(
            experiment="Final Number included in the analysis",
            question_short_name="Final N",
            document_id=paper.document_id,
            result=("|".join(results)),
            answer=total_population_size if total_population_size != 0 else "Answer not found.",
            excerpts=relevant_paragraphs, 
        )
        
    async def run(self, paper: Paper):
        abstract = self.retrieve_abstract(paper)
        paragraphs = [str(p) for p in paper.paragraphs if str(p)]
        populations = await self.get_populations(abstract)
        relevant_paragraphs = await filter_async(paragraphs, self.score_paragraph)
        results = await self.get_populations_numbers(relevant_paragraphs, populations, abstract)
        recipe_results = await self.get_answer(paper, results, relevant_paragraphs)
        self.maybe_add_to_results(results)
        return recipe_results


            